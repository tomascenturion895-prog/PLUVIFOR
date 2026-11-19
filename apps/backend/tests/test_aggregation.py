"""Acumulados por estación y por zona (SCRUM-30). Los huecos no suman 0."""

from datetime import date

import pytest
from sqlalchemy.orm import Session

from app.domain.enums import DataCategory, RainState
from app.models import RainfallRecord, Source, Station
from app.repositories.series import SqlSeriesRepository

D = date


@pytest.fixture
def repo_and_ids(db: Session):
    source = Source(code="s", name="S", network="N", category=DataCategory.OBSERVADO)
    db.add(source)
    db.flush()
    stations = [
        Station(source_id=source.id, code="A", name="A", zone="Centro", department="Pirané"),
        Station(source_id=source.id, code="B", name="B", zone="Centro", department="Formosa"),
        Station(source_id=source.id, code="C", name="C", zone="Oeste", department="Bermejo"),
    ]
    db.add_all(stations)
    db.flush()
    a, b, c = (s.id for s in stations)

    def add(station, day, state, mm, category=DataCategory.OBSERVADO):
        db.add(
            RainfallRecord(station_id=station, obs_date=day, state=state, mm=mm, category=category)
        )

    add(a, D(2016, 1, 1), RainState.DATO, 10.0)
    add(a, D(2016, 1, 2), RainState.DATO, 0.0)  # un cero real sí es dato
    add(a, D(2016, 1, 3), RainState.FILA_SIN_VALOR, None)
    add(a, D(2016, 1, 4), RainState.SIN_FILA, None)
    add(a, D(2016, 1, 5), RainState.DATO, 2.5)
    add(a, D(2016, 1, 1), RainState.DATO, 99.0, DataCategory.ESTIMADO)  # otra categoría
    add(b, D(2016, 1, 1), RainState.FILA_SIN_VALOR, None)  # solo huecos
    add(b, D(2016, 1, 2), RainState.SIN_FILA, None)
    db.commit()
    return SqlSeriesRepository(db), a, b, c


def test_station_accumulated_counts_only_days_with_data(repo_and_ids):
    repo, a, *_ = repo_and_ids
    result = repo.accumulated_by_station(a, DataCategory.OBSERVADO, D(2016, 1, 1), D(2016, 1, 31))
    assert result.accumulated_mm == 12.5
    assert (result.data_days, result.gap_days) == (3, 2)


def test_categories_are_never_mixed(repo_and_ids):
    repo, a, *_ = repo_and_ids
    observed = repo.accumulated_by_station(a, DataCategory.OBSERVADO, D(2016, 1, 1), D(2016, 1, 1))
    estimated = repo.accumulated_by_station(a, DataCategory.ESTIMADO, D(2016, 1, 1), D(2016, 1, 1))
    assert observed.accumulated_mm == 10.0 and estimated.accumulated_mm == 99.0


def test_only_gaps_gives_null_not_zero(repo_and_ids):
    repo, _, b, _ = repo_and_ids
    result = repo.accumulated_by_station(b, DataCategory.OBSERVADO, D(2016, 1, 1), D(2016, 1, 31))
    assert result.accumulated_mm is None
    assert (result.data_days, result.gap_days) == (0, 2)


def test_station_without_any_record_is_listed_with_null(repo_and_ids):
    repo, _, _, c = repo_and_ids
    result = repo.accumulated_by_station(c, DataCategory.OBSERVADO, D(2016, 1, 1), D(2016, 1, 31))
    assert result is not None
    assert (result.accumulated_mm, result.data_days, result.gap_days) == (None, 0, 0)


def test_period_is_inclusive_and_empty_period_is_null(repo_and_ids):
    repo, a, *_ = repo_and_ids
    one_day = repo.accumulated_by_station(a, DataCategory.OBSERVADO, D(2016, 1, 5), D(2016, 1, 5))
    assert one_day.accumulated_mm == 2.5
    outside = repo.accumulated_by_station(a, DataCategory.OBSERVADO, D(2017, 1, 1), D(2017, 1, 31))
    assert outside.accumulated_mm is None


def test_unknown_station_returns_none(repo_and_ids):
    repo, *_ = repo_and_ids
    assert (
        repo.accumulated_by_station(9999, DataCategory.OBSERVADO, D(2016, 1, 1), D(2016, 1, 2))
        is None
    )


def test_zone_lists_every_station_and_does_not_add_them_together(repo_and_ids):
    repo, a, b, _ = repo_and_ids
    rows = repo.accumulated_by_group(
        "zone", "Centro", DataCategory.OBSERVADO, D(2016, 1, 1), D(2016, 1, 31)
    )
    assert [(r.station_id, r.accumulated_mm) for r in rows] == [(a, 12.5), (b, None)]


def test_department_and_unknown_group(repo_and_ids):
    repo, a, *_ = repo_and_ids
    rows = repo.accumulated_by_group(
        "department", "Pirané", DataCategory.OBSERVADO, D(2016, 1, 1), D(2016, 1, 31)
    )
    assert [r.station_id for r in rows] == [a]
    assert (
        repo.accumulated_by_group(
            "zone", "No existe", DataCategory.OBSERVADO, D(2016, 1, 1), D(2016, 1, 31)
        )
        == []
    )
