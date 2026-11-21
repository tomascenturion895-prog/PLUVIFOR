"""GET /api/events: días de lluvia intensa y rachas secas, descriptivo. Un hueco no es 0 mm."""

from datetime import date, timedelta

import pytest

from app.domain.enums import DataCategory, RainState, Validation
from app.domain.events import analyze
from app.domain.quality import DayValue
from app.models import RainfallRecord, Source, Station

INICIO = date(2020, 1, 1)


def serie(valores: list[float | None]) -> list[DayValue]:
    return [
        DayValue(
            INICIO + timedelta(days=i),
            RainState.DATO if v is not None else RainState.SIN_FILA,
            v,
        )
        for i, v in enumerate(valores)
    ]


# --- dominio --------------------------------------------------------------------------------


def test_cuenta_50_y_100_y_un_dia_de_100_figura_en_las_dos_listas():
    a = analyze(serie([10, 49.9, 50, 99.9, 100, 0]), [], 7)
    assert [e.mm for e in a.ge50] == [50, 99.9, 100]
    assert [e.mm for e in a.ge100] == [100]


def test_un_hueco_corta_la_racha_seca_y_no_cuenta_como_dia_seco():
    a = analyze(serie([0, 0, 0, None, 0, 0, 0]), [], 1)
    assert [s.days for s in a.dry_streaks] == [3, 3]  # nunca una racha de 7
    assert a.longest is not None and a.longest.days == 3


def test_min_dry_days_filtra_la_lista_pero_la_mas_larga_se_informa_siempre():
    a = analyze(serie([0, 0, 5, 0, 0, 0]), [], 10)
    assert a.dry_streaks == []
    assert a.longest is not None and a.longest.days == 3


def test_una_racha_que_toca_ceros_prolongados_viene_marcada():
    a = analyze(serie([0, 0, 0]), [(INICIO + timedelta(days=2), INICIO + timedelta(days=9))], 1)
    assert a.dry_streaks[0].zero_run_warning is True


def test_sin_dato_en_toda_la_serie_no_inventa_rachas():
    a = analyze(serie([None, None, None]), [], 1)
    assert a.ge50 == [] and a.dry_streaks == [] and a.longest is None


# --- API ------------------------------------------------------------------------------------


@pytest.fixture
def estacion(db):
    fuente = Source(code="demo", name="Demo", network="INTA", category=DataCategory.OBSERVADO)
    db.add(fuente)
    db.flush()
    st = Station(code="E1", name="Estación de prueba", source_id=fuente.id, zone="Centro")
    db.add(st)
    db.flush()
    valores = {0: 0.0, 1: 0.0, 2: 60.0, 3: 0.0, 4: 0.0, 5: 0.0, 7: 120.0}  # el día 6 no tiene fila
    for i, mm in valores.items():
        db.add(
            RainfallRecord(
                station_id=st.id,
                obs_date=INICIO + timedelta(days=i),
                state=RainState.DATO,
                mm=mm,
                category=DataCategory.OBSERVADO,
                validation=Validation.SIN_VALIDAR,
            )
        )
    db.commit()
    return st.id


def pedir(client, **params):
    base = {"from": INICIO.isoformat(), "to": (INICIO + timedelta(days=7)).isoformat()}
    return client.get("/api/events", params={**base, **params})


def test_la_api_devuelve_eventos_y_rachas_de_una_estacion(client, estacion):
    r = pedir(client, station_id=estacion, min_dry_days=2)
    body = r.json()
    assert r.status_code == 200
    est = body["stations"][0]
    assert [e["mm"] for e in est["days_50mm_or_more"]] == [60.0, 120.0]
    assert [e["mm"] for e in est["days_100mm_or_more"]] == [120.0]
    assert [s["days"] for s in est["dry_streaks"]] == [2, 3]
    assert est["longest_dry_streak"]["days"] == 3
    assert "no una alerta" in body["description"]


def test_un_dia_sin_fila_corta_la_racha_y_no_es_cero(client, estacion):
    est = pedir(client, station_id=estacion).json()["stations"][0]
    assert est["summary"]["days_sin_fila"] == 1
    assert est["summary"]["accumulated_mm"] == 180.0  # el hueco no suma ni resta


def test_se_puede_pedir_por_zona(client, estacion):
    r = pedir(client, zone="Centro")
    assert r.status_code == 200 and len(r.json()["stations"]) == 1


def test_sin_estacion_ni_zona_o_con_las_dos_es_un_error_422(client, estacion):
    assert pedir(client).status_code == 422
    assert pedir(client, station_id=estacion, zone="Centro").status_code == 422


def test_estacion_o_zona_inexistente_es_404(client, estacion):
    assert pedir(client, station_id=999).status_code == 404
    assert pedir(client, zone="Nada").status_code == 404


def test_entradas_invalidas_se_rechazan(client, estacion):
    assert pedir(client, station_id=estacion, min_dry_days=0).status_code == 422
    assert pedir(client, station_id="abc").status_code == 422
    assert pedir(client, station_id=estacion, **{"from": "2020-02-01"}).status_code == 422


def test_el_periodo_no_pasa_el_corte_de_datos(client, estacion):
    body = pedir(client, station_id=estacion, to="2030-01-01").json()
    assert body["clipped_to_cutoff"] is True and body["date_to"] == "2026-10-31"
