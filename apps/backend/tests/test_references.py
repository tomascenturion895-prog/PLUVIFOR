"""Normal mensual (SCRUM-60): referencia con fuente, separada de lo observado."""

from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import cli
from app.ingestion.types import InvalidFileError
from app.models import ClimateReference, RainfallRecord, Station
from app.repositories.references import SqlReferenceRepository
from app.services.references import ReferenceService

REAL = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "datos"
    / "normales_smn_formosa_aero_1991_2020.csv"
)
HEADER = "station_code,station_name,lat,lon,elevation_m,month,normal_mm,period,source_note\n"
NOTA = "SMN prueba"


def fila(month=1, mm="10", code="1", period="1991-2020", note=NOTA, lat="-26.2", lon="-58.2"):
    return f"{code},Est,{lat},{lon},59,{month},{mm},{period},{note}\n"


@pytest.fixture
def service(db: Session) -> ReferenceService:
    return ReferenceService(SqlReferenceRepository(db))


def cargar(service, texto: str, name="n.csv"):
    return service.import_normals(name, texto.encode())


class TestDatosReales:
    def test_el_archivo_versionado_carga_12_meses_de_referencia(self, service, db):
        done = service.import_normals(REAL.name, REAL.read_bytes())
        assert (done.station_code, done.months, done.period) == ("87162", 12, "1991-2020")
        normals = list(db.scalars(select(ClimateReference).order_by(ClimateReference.month)))
        assert [n.normal_mm for n in normals][:3] == [163.5, 135.6, 138.2]
        assert all(n.category.value == "referencia" for n in normals)
        assert all("pág. 400" in n.source_note for n in normals)

    def test_la_suma_de_los_meses_coincide_con_el_anual_publicado(self, service, db):
        service.import_normals(REAL.name, REAL.read_bytes())
        total = db.scalar(select(func.sum(ClimateReference.normal_mm)))
        assert total == pytest.approx(1406.4, abs=0.2)

    def test_la_estacion_queda_con_sus_coordenadas_publicadas(self, service, db):
        service.import_normals(REAL.name, REAL.read_bytes())
        st = db.scalar(select(Station).where(Station.code == "87162"))
        assert (st.lat, st.lon, st.elevation_m) == (-26.21242, -58.22929, 59)
        assert st.coords_status.value == "verificada"

    def test_cargarlo_dos_veces_no_duplica(self, service, db):
        service.import_normals(REAL.name, REAL.read_bytes())
        service.import_normals(REAL.name, REAL.read_bytes())
        assert db.scalar(select(func.count()).select_from(ClimateReference)) == 12
        assert db.scalar(select(func.count()).select_from(Station)) == 1


class TestValidacion:
    @pytest.mark.parametrize(
        ("texto", "mensaje"),
        [
            (HEADER, "no tiene filas"),
            (HEADER + fila(month=13), "entre 1 y 12"),
            (HEADER + fila(month=0), "entre 1 y 12"),
            (HEADER + fila(month="1.5"), "entre 1 y 12"),
            (HEADER + fila(mm="-3"), "negativa"),
            (HEADER + fila(mm="abc"), "no es un número"),
            (HEADER + fila(mm="nan"), "no es un número válido"),
            (HEADER + fila(note=""), "su período y la nota de su fuente"),
            (HEADER + fila(period=""), "su período y la nota de su fuente"),
            (HEADER + fila() + fila(), "repetido"),
            (HEADER + fila() + fila(month=2, code="2"), "mezcla estaciones"),
            (HEADER + fila() + fila(month=2, period="1981-2010"), "mezcla estaciones"),
            ("station_code,month\n1,1\n", "Faltan columnas"),
        ],
    )
    def test_entradas_invalidas_se_rechazan_sin_guardar_nada(self, service, db, texto, mensaje):
        with pytest.raises(InvalidFileError, match=mensaje):
            cargar(service, texto)
        assert db.scalar(select(func.count()).select_from(ClimateReference)) == 0

    def test_un_archivo_que_no_es_csv_se_rechaza(self, service):
        with pytest.raises(InvalidFileError):
            cargar(service, HEADER + fila(), name="normal.xlsx")

    def test_un_cero_es_una_normal_valida(self, service, db):
        cargar(service, HEADER + fila(mm="0"))
        assert db.scalar(select(ClimateReference.normal_mm)) == 0.0


class TestApi:
    def test_devuelve_la_normal_como_referencia_con_su_fuente(self, client, service, db):
        service.import_normals(REAL.name, REAL.read_bytes())
        sid = db.scalar(select(Station.id).where(Station.code == "87162"))
        body = client.get("/api/climate-reference", params={"station_id": sid}).json()
        assert body["category"] == "referencia"
        assert "no se suma ni se promedia" in body["notice"]
        conjunto = body["normals"][0]
        assert conjunto["period"] == "1991-2020"
        assert "SMN" in conjunto["source_note"]
        assert [m["month"] for m in conjunto["months"]] == list(range(1, 13))
        assert conjunto["months"][0]["normal_mm"] == 163.5

    def test_sin_normal_cargada_devuelve_vacio_y_no_ceros(self, client, db):
        from app.domain.enums import DataCategory
        from app.models import Source

        src = Source(code="s", name="S", network="R", category=DataCategory.OBSERVADO)
        db.add(src)
        db.flush()
        st = Station(source_id=src.id, code="1", name="Sin normal")
        db.add(st)
        db.commit()
        body = client.get("/api/climate-reference", params={"station_id": st.id}).json()
        assert body["normals"] == []

    def test_estacion_inexistente_da_404(self, client):
        assert client.get("/api/climate-reference", params={"station_id": 999}).status_code == 404

    @pytest.mark.parametrize("valor", ["0", "-1", "abc"])
    def test_id_invalido_da_422(self, client, valor):
        assert client.get("/api/climate-reference", params={"station_id": valor}).status_code == 422

    def test_la_normal_no_aparece_mezclada_en_la_lluvia_observada(self, client, service, db):
        service.import_normals(REAL.name, REAL.read_bytes())
        sid = db.scalar(select(Station.id).where(Station.code == "87162"))
        serie = client.get(
            "/api/rainfall", params={"station_id": sid, "from": "2016-01-01", "to": "2016-01-31"}
        ).json()
        assert serie["summary"]["accumulated_mm"] is None  # nada observado: sin dato, no 163,5
        assert serie["summary"]["days_with_data"] == 0
        assert db.scalar(select(func.count()).select_from(RainfallRecord)) == 0


def test_el_comando_carga_la_normal(monkeypatch, tmp_path, capsys):
    url = f"sqlite:///{tmp_path / 'n.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    from app.config import get_settings
    from app.db.base import Base
    from app.db.session import create_db_engine

    get_settings.cache_clear()
    try:
        engine = create_db_engine(url)
        Base.metadata.create_all(engine)
        engine.dispose()
        assert cli.main(["import-normals"]) == 0
        assert "12 meses" in capsys.readouterr().out
    finally:
        get_settings.cache_clear()
