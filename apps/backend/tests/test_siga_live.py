"""SIGA en vivo con respaldo en CSV (SCRUM-64). La red va simulada, sin internet."""

import json
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import ImportMode, ImportStatus, RainState
from app.ingestion.siga_live import SigaLiveClient, SigaUnavailableError, rows_to_csv
from app.ingestion.types import InvalidFileError
from app.models import ImportLog, RainfallRecord
from app.repositories.ingestion import SqlIngestionRepository
from app.services.importer import ImportService
from app.services.siga_live import SigaLiveImporter

CUTOFF = date(2026, 10, 31)
DATOS = Path(__file__).resolve().parents[3] / "docs" / "datos"
PHP = "AbCdEfGhIjKlMn.php"


def fila(dia: str, plub: float | None, crono: float | None = None) -> dict:
    return {
        "fechaHora": f"{dia}T00:00:00Z[UTC]",
        "idEstacion": 424,
        "precDiaPlub": plub,
        "precDiaCrono": crono,
    }


class SigaFalso:
    """Imita al SIGA: un .php escondido en el JavaScript, el catálogo y las series diarias."""

    def __init__(self, filas: list[dict]):
        self.filas = filas
        self.urls: list[str] = []

    def __call__(self, url: str) -> str:
        self.urls.append(url)
        if url.endswith("/js/urlserver.js"):
            return f"var url = '{PHP}';"
        if "param_type=estacion" in url:
            return json.dumps([{"id": 424}])
        if "param_type=diario" in url:
            return json.dumps(self.filas)
        raise SigaUnavailableError("no existe")


def sin_red(url: str) -> str:
    raise SigaUnavailableError("Sin conexión")


@pytest.fixture
def repo(db: Session) -> SqlIngestionRepository:
    repo = SqlIngestionRepository(db)
    ImportService(repo, CUTOFF).import_stations(
        "siga_inta", "estaciones.csv", (DATOS / "estaciones_siga_formosa.csv").read_bytes()
    )
    return repo


def armar(repo: SqlIngestionRepository, fetch) -> SigaLiveImporter:
    return SigaLiveImporter(
        ImportService(repo, CUTOFF),
        repo,
        SigaLiveClient(fetch, host="https://siga.example"),
        DATOS / "lluvia_diaria_siga_formosa.csv",
        CUTOFF,
    )


def test_descubre_el_endpoint_en_el_javascript_del_sitio() -> None:
    falso = SigaFalso([])
    assert SigaLiveClient(falso, "https://siga.example").discover_endpoint().endswith(PHP)


def test_si_el_sitio_cambio_no_inventa_un_endpoint() -> None:
    with pytest.raises(SigaUnavailableError):
        SigaLiveClient(lambda url: "sin php", "https://siga.example").discover_endpoint()


def test_un_hueco_no_es_cero_al_convertir_a_csv() -> None:
    texto = rows_to_csv(
        424, [fila("2016-01-01", 0.0), fila("2016-01-02", None)], date(2016, 1, 1), date(2016, 1, 3)
    )
    estados = [linea.split(",")[6] for linea in texto.strip().split("\n")[1:]]
    assert estados == ["dato", "fila_sin_valor", "sin_fila"]
    # el cero real es un dato; los dos huecos quedan sin milímetros
    mm = [linea.split(",")[3] for linea in texto.strip().split("\n")[1:]]
    assert mm == ["0", "", ""]


def test_pide_de_a_730_dias_y_nunca_despues_del_corte(repo: SqlIngestionRepository) -> None:
    falso = SigaFalso([])
    armar(repo, falso).run([424], date(2024, 1, 1), date(2027, 1, 1), ImportMode.AUDIT)
    pedidos = [u for u in falso.urls if "param_type=diario" in u]
    assert len(pedidos) == 2  # 2024-01-01 a 2026-10-31 son 1.035 días
    assert all("/01-11-2026" not in u and not u.endswith("2027") for u in pedidos)
    assert pedidos[-1].endswith("/31-10-2026")


def test_respuesta_truncada_se_trata_como_fallo() -> None:
    llena = SigaFalso([fila("2016-01-01", 1.0)] * 1000)
    with pytest.raises(SigaUnavailableError):
        SigaLiveClient(llena, "https://siga.example").daily(
            424, date(2016, 1, 1), date(2016, 1, 31)
        )


def test_en_vivo_guarda_los_datos_y_conserva_los_huecos(
    db: Session, repo: SqlIngestionRepository
) -> None:
    falso = SigaFalso([fila("2016-01-01", 12.5), fila("2016-01-02", 0.0), fila("2016-01-03", None)])
    resultado = armar(repo, falso).run([424], date(2016, 1, 1), date(2016, 1, 4), ImportMode.COMMIT)
    assert resultado.origin == "en_vivo" and resultado.reason is None
    guardado = {r.obs_date: (r.state, r.mm) for r in db.scalars(select(RainfallRecord))}
    assert guardado[date(2016, 1, 1)] == (RainState.DATO, 12.5)
    assert guardado[date(2016, 1, 2)] == (RainState.DATO, 0.0)
    assert guardado[date(2016, 1, 3)][1] is None  # fila sin valor: no es 0
    assert guardado[date(2016, 1, 4)][1] is None  # sin fila: no es 0


def test_sin_red_usa_el_csv_lo_avisa_y_registra_el_intento(
    db: Session, repo: SqlIngestionRepository
) -> None:
    resultado = armar(repo, sin_red).run(
        [424], date(2016, 1, 1), date(2016, 1, 31), ImportMode.COMMIT
    )
    assert resultado.origin == "respaldo_csv"
    assert "Sin conexión" in (resultado.reason or "")
    assert resultado.report.inserted > 7000  # el CSV versionado completo
    logs = list(db.scalars(select(ImportLog).order_by(ImportLog.id)))
    fallido = [log for log in logs if log.status == ImportStatus.FAILED]
    assert len(fallido) == 1 and fallido[0].filename == "siga_en_vivo.csv"
    assert any(log.filename == "lluvia_diaria_siga_formosa.csv" for log in logs)


@pytest.mark.parametrize("estaciones", [[], [0], [-3]])
def test_estaciones_invalidas_se_rechazan(
    repo: SqlIngestionRepository, estaciones: list[int]
) -> None:
    with pytest.raises(InvalidFileError):
        armar(repo, sin_red).run(estaciones, date(2016, 1, 1), date(2016, 1, 31), ImportMode.AUDIT)


def test_un_periodo_posterior_al_corte_se_rechaza(repo: SqlIngestionRepository) -> None:
    with pytest.raises(InvalidFileError):
        armar(repo, sin_red).run([424], date(2026, 11, 5), date(2026, 11, 30), ImportMode.AUDIT)


def test_solo_se_consulta_por_https() -> None:
    from app.ingestion.siga_live import http_fetch

    with pytest.raises(SigaUnavailableError):
        http_fetch("http://siga.inta.gob.ar/algo")
