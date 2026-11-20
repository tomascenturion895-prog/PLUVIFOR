"""Recurrencia histórica de lluvia intensa: descriptiva, nunca una predicción."""

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.enums import DataCategory, RainState, Severity, Validation
from app.domain.quality import DayValue
from app.domain.recurrence import MIN_OBSERVED_YEARS, compute
from app.models import QualityFlag, RainfallRecord, Source, Station

INICIO = date(2014, 1, 1)
FIN = date(2020, 12, 31)  # 7 años completos


def dia(n: int, mm: float | None, estado: RainState = RainState.DATO) -> DayValue:
    return DayValue(INICIO + timedelta(days=n), estado, mm)


def serie(valores: list[float | None]) -> list[DayValue]:
    return [
        dia(i, v, RainState.DATO if v is not None else RainState.SIN_FILA)
        for i, v in enumerate(valores)
    ]


# --- dominio --------------------------------------------------------------------------------


def test_cuenta_50_y_100_y_un_dia_de_100_figura_en_las_dos():
    r = compute(serie([10, 49.9, 50, 99.9, 100, 180]), [])
    assert (r.ge50, r.ge100) == (4, 2)


def test_un_hueco_no_es_un_dia_seco_ni_de_lluvia_y_no_suma_al_periodo():
    r = compute(serie([60, None, None, 0, 70]), [])
    assert r.gap_days == 2 and r.valid_days == 3  # los 2 huecos no cuentan como 0 mm
    assert (r.ge50, r.ge100) == (2, 0)


def test_los_dias_dentro_de_una_racha_de_ceros_prolongados_se_excluyen():
    r = compute(serie([0, 0, 0, 60, 0]), [(INICIO, INICIO + timedelta(days=2))])
    assert r.excluded_zero_run_days == 3 and r.valid_days == 2
    assert r.ge50 == 1


def test_con_menos_de_5_anios_de_dato_no_se_informa_ninguna_frecuencia():
    r = compute(serie([80] + [0] * 364 * 3), [])
    assert not r.sufficient and r.observed_years < MIN_OBSERVED_YEARS
    assert r.ge50 == 1  # el conteo se informa igual
    assert (r.ge50_per_year, r.ge50_every_years) == (None, None)


def test_con_5_anios_o_mas_calcula_la_frecuencia_pasada():
    dias = [0.0] * (365 * 10)
    for i in (10, 800, 1900, 3000):
        dias[i] = 75.0
    dias[3000] = 120.0
    r = compute(serie(dias), [])
    assert r.sufficient and r.ge50 == 4 and r.ge100 == 1
    assert r.ge50_per_year == pytest.approx(4 / r.observed_years, rel=1e-2)
    assert r.ge50_every_years == pytest.approx(r.observed_years / 4, rel=1e-2)
    assert r.ge100_every_years == pytest.approx(r.observed_years, rel=1e-2)


def test_sin_eventos_no_hay_intervalo_ni_se_inventa_uno():
    r = compute(serie([5.0] * (365 * 6)), [])
    assert r.sufficient and r.ge50 == 0
    assert (r.ge50_per_year, r.ge50_every_years) == (None, None)


def test_el_detalle_por_anio_suma_lo_mismo_que_el_total():
    r = compute(serie([60.0, 0, 0] * 800), [])
    assert sum(y.ge50 for y in r.by_year) == r.ge50
    assert sum(y.valid_days for y in r.by_year) == r.valid_days


# --- API ------------------------------------------------------------------------------------


@pytest.fixture
def estacion(db: Session) -> int:
    fuente = Source(
        code="siga_inta",
        name="SIGA",
        network="INTA",
        category=DataCategory.OBSERVADO,
        day_cutoff_local="09:00",
    )
    db.add(fuente)
    db.flush()
    st = Station(source_id=fuente.id, code="424", name="El Colorado")
    db.add(st)
    db.flush()
    total = (FIN - INICIO).days + 1
    for i in range(total):
        d = INICIO + timedelta(days=i)
        if d == date(2015, 3, 3):
            continue  # sin_fila: un hueco
        if d == date(2015, 3, 4):
            estado, mm = RainState.FILA_SIN_VALOR, None
        else:
            estado = RainState.DATO
            mm = {date(2016, 2, 1): 62.0, date(2018, 2, 1): 140.0, date(2019, 2, 1): 55.0}.get(
                d, 1.0
            )
        db.add(
            RainfallRecord(
                station_id=st.id,
                obs_date=d,
                state=estado,
                mm=mm,
                category=DataCategory.OBSERVADO,
                validation=Validation.SIN_VALIDAR,
            )
        )
    db.commit()
    return st.id


def pedir(client: TestClient, station_id: int, **extra):
    params = {"station_id": station_id, "from": INICIO.isoformat(), "to": FIN.isoformat(), **extra}
    return client.get("/api/recurrence", params=params)


def test_la_api_cuenta_los_eventos_y_aclara_que_no_es_prediccion(client, estacion):
    r = pedir(client, estacion)
    body = r.json()
    assert r.status_code == 200
    assert (body["ge50"], body["ge100"]) == (3, 1)
    assert body["category"] == "observado" and body["sufficient_history"] is True
    assert body["gap_days"] == 2  # los dos huecos no son 0 mm ni suman al período
    assert body["valid_days"] == (FIN - INICIO).days + 1 - 2
    assert "No es una predicción" in body["notice"]
    assert body["ge50_every_years"] == pytest.approx(body["observed_years"] / 3, abs=0.06)
    assert {y["year"] for y in body["by_year"]} == set(range(2014, 2021))


def test_la_api_excluye_los_dias_de_una_racha_de_ceros_prolongados(client, db, estacion):
    db.add(
        QualityFlag(
            station_id=estacion,
            code="ceros_prolongados",
            start_date=date(2016, 1, 25),
            end_date=date(2016, 2, 10),  # incluye el día de 62 mm: no se cuenta
            severity=Severity.AVISO,
            rule_version="ceros_prolongados/1",
        )
    )
    db.commit()
    body = pedir(client, estacion).json()
    assert body["ge50"] == 2 and body["excluded_zero_run_days"] == 17


def test_un_periodo_de_mas_de_10_anios_se_pide_por_tramos(client, estacion):
    r = client.get(
        "/api/recurrence",
        params={"station_id": estacion, "from": "2000-01-01", "to": "2020-12-31"},
    )
    assert r.status_code == 200 and r.json()["ge50"] == 3


def test_el_periodo_no_pasa_el_corte_de_datos(client, estacion):
    body = client.get(
        "/api/recurrence",
        params={"station_id": estacion, "from": "2020-01-01", "to": "2030-01-01"},
    ).json()
    assert body["clipped_to_cutoff"] is True and body["date_to"] == "2026-10-31"


def test_entradas_invalidas(client, estacion):
    assert pedir(client, 9999).status_code == 404
    assert pedir(client, estacion, **{"from": "2021-01-01", "to": "2020-01-01"}).status_code == 422
    r = pedir(client, estacion, **{"from": "2027-01-01", "to": "2027-02-01"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "after_cutoff"
    assert pedir(client, estacion, **{"from": "1900-01-01"}).status_code == 422
    assert client.get("/api/recurrence", params={"station_id": "abc"}).status_code == 422
    assert pedir(client, 0).status_code == 422
