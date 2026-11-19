from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.enums import DataCategory, RainState, Severity, Validation
from app.models import QualityFlag, RainfallRecord, Source, Station

START = date(2016, 1, 1)


@pytest.fixture
def station_id(db: Session) -> int:
    source = Source(
        code="siga_inta",
        name="SIGA",
        network="INTA",
        category=DataCategory.OBSERVADO,
        day_cutoff_local="09:00",
    )
    db.add(source)
    db.flush()
    station = Station(source_id=source.id, code="424", name="El Colorado")
    db.add(station)
    db.flush()
    # 10 días: lluvia, cero, hueco sin fila, hueco sin valor, y el resto ceros. Falta el día 11.
    plan = [
        (RainState.DATO, 12.5),
        (RainState.DATO, 0.0),
        (RainState.SIN_FILA, None),
        (RainState.FILA_SIN_VALOR, None),
    ] + [(RainState.DATO, 0.0)] * 6
    for i, (state, mm) in enumerate(plan):
        db.add(
            RainfallRecord(
                station_id=station.id,
                obs_date=START + timedelta(days=i),
                state=state,
                mm=mm,
                category=DataCategory.OBSERVADO,
                validation=Validation.VALIDADO,
            )
        )
    db.commit()
    return station.id


def get(client: TestClient, station_id: int, **params):
    params.setdefault("from", "2016-01-01")
    params.setdefault("to", "2016-01-10")
    return client.get("/api/rainfall", params={"station_id": station_id, **params})


def test_series_keeps_gaps_as_null_never_zero(client: TestClient, station_id: int):
    body = get(client, station_id).json()
    by_date = {d["obs_date"]: d for d in body["days"]}
    assert by_date["2016-01-02"] == {
        "obs_date": "2016-01-02",
        "state": "dato",
        "mm": 0.0,
        "category": "observado",
        "source": "siga_inta",
        "flags": [],
    }
    assert by_date["2016-01-03"]["mm"] is None and by_date["2016-01-03"]["state"] == "sin_fila"
    assert by_date["2016-01-04"]["mm"] is None
    assert by_date["2016-01-04"]["state"] == "fila_sin_valor"


def test_summary_reports_coverage_and_accumulated_from_data_days_only(
    client: TestClient, station_id: int
):
    body = get(client, station_id).json()
    assert body["summary"] == {
        "days_in_period": 10,
        "days_with_data": 8,
        "days_sin_fila": 1,
        "days_fila_sin_valor": 1,
        "coverage": 0.8,
        "accumulated_mm": 12.5,
    }
    assert body["category"] == "observado" and body["source"]["code"] == "siga_inta"
    assert "PROTOTIPO" in body["notice"]


def test_days_missing_in_the_database_show_as_sin_fila(client: TestClient, station_id: int):
    body = get(client, station_id, to="2016-01-12").json()
    assert body["summary"]["days_in_period"] == 12
    assert body["days"][-1]["state"] == "sin_fila" and body["days"][-1]["mm"] is None


def test_period_without_any_data_has_null_accumulated_not_zero(client: TestClient, station_id: int):
    body = get(client, station_id, **{"from": "2016-03-01", "to": "2016-03-05"}).json()
    assert body["summary"]["days_with_data"] == 0
    assert body["summary"]["accumulated_mm"] is None
    assert "cobertura_baja" in [w["code"] for w in body["warnings"]]


def test_low_coverage_warning(client: TestClient, station_id: int):
    codes = [w["code"] for w in get(client, station_id, to="2016-01-20").json()["warnings"]]
    assert "cobertura_baja" in codes


def test_zero_streak_flag_is_returned_as_warning(client: TestClient, db: Session, station_id: int):
    db.add(
        QualityFlag(
            station_id=station_id,
            code="ceros_prolongados",
            start_date=date(2015, 9, 20),
            end_date=date(2016, 1, 5),
            severity=Severity.AVISO,
            rule_version="ceros_prolongados/1",
        )
    )
    db.commit()
    warnings = get(client, station_id).json()["warnings"]
    assert [w["code"] for w in warnings if w["code"] == "ceros_prolongados"]
    # El tramo termina antes del período pedido: no debe aparecer.
    later = get(client, station_id, **{"from": "2016-01-06", "to": "2016-01-10"}).json()
    assert later["warnings"] == [] or all(
        w["code"] != "ceros_prolongados" for w in later["warnings"]
    )


def test_unvalidated_data_is_warned(client: TestClient, db: Session, station_id: int):
    record = db.query(RainfallRecord).filter_by(obs_date=START).one()
    record.validation = Validation.SIN_VALIDAR
    db.commit()
    codes = [w["code"] for w in get(client, station_id).json()["warnings"]]
    assert "dato_sin_validar" in codes


def test_dates_after_cutoff_are_clipped_and_flagged(client: TestClient, station_id: int):
    body = get(client, station_id, **{"from": "2026-10-30", "to": "2027-03-01"}).json()
    assert body["date_to"] == "2026-10-31" and body["clipped_to_cutoff"] is True
    assert body["summary"]["days_in_period"] == 2


def test_period_fully_after_cutoff_is_rejected(client: TestClient, station_id: int):
    response = get(client, station_id, **{"from": "2026-11-05", "to": "2026-11-10"})
    assert response.status_code == 422 and response.json()["error"]["code"] == "after_cutoff"


@pytest.mark.parametrize(
    ("params", "code"),
    [
        ({"from": "2016-02-01", "to": "2016-01-01"}, "invalid_range"),
        ({"from": "1990-01-01", "to": "2016-01-01"}, "range_too_large"),
    ],
)
def test_invalid_ranges(client: TestClient, station_id: int, params: dict, code: str):
    response = get(client, station_id, **params)
    assert response.status_code == 422 and response.json()["error"]["code"] == code


def test_bad_input_and_unknown_station(client: TestClient, station_id: int):
    assert get(client, station_id, **{"from": "no-es-fecha"}).status_code == 422
    assert get(client, station_id, category="inventada").status_code == 422
    assert client.get("/api/rainfall", params={"station_id": station_id}).status_code == 422
    assert (
        client.get("/api/rainfall", params={"from": "2016-01-01", "to": "2016-01-02"}).status_code
        == 422
    )
    missing = get(client, 9999)
    assert missing.status_code == 404 and missing.json()["error"]["code"] == "station_not_found"


def test_categories_are_never_mixed(client: TestClient, db: Session, station_id: int):
    db.add(
        RainfallRecord(
            station_id=station_id,
            obs_date=START,
            state=RainState.DATO,
            mm=99.0,
            category=DataCategory.ESTIMADO,
        )
    )
    db.commit()
    observed = get(client, station_id).json()
    estimated = get(client, station_id, category="estimado").json()
    assert observed["summary"]["accumulated_mm"] == 12.5
    assert estimated["summary"]["accumulated_mm"] == 99.0
    assert estimated["category"] == "estimado"


def test_each_day_lists_the_flags_that_cover_it(client: TestClient, db: Session, station_id: int):
    db.add(
        QualityFlag(
            station_id=station_id,
            code="ceros_prolongados",
            start_date=date(2016, 1, 5),
            end_date=date(2016, 1, 7),
            severity=Severity.AVISO,
            rule_version="ceros_prolongados/1",
        )
    )
    db.commit()
    by_date = {d["obs_date"]: d for d in get(client, station_id).json()["days"]}
    assert by_date["2016-01-04"]["flags"] == []
    assert by_date["2016-01-06"]["flags"] == ["ceros_prolongados"]
    assert by_date["2016-01-08"]["flags"] == []


def test_series_route_under_stations_no_longer_exists(client: TestClient, station_id: int):
    assert client.get(f"/stations/{station_id}/series").status_code == 404
