from datetime import date, timedelta
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import DataCategory, ImportMode, RainState
from app.domain.quality import DayValue, find_zero_streaks
from app.models import QualityFlag, RainfallRecord, Source, Station
from app.repositories.ingestion import SqlIngestionRepository
from app.repositories.quality import SqlQualityRepository
from app.services.importer import ImportService
from app.services.quality import QualityService

START = date(2016, 1, 1)


def days(spec: list[tuple[RainState, float | None]]) -> list[DayValue]:
    return [DayValue(START + timedelta(days=i), state, mm) for i, (state, mm) in enumerate(spec)]


def zeros(n: int) -> list[tuple[RainState, float | None]]:
    return [(RainState.DATO, 0.0)] * n


def test_streak_of_exactly_60_is_flagged():
    streaks = find_zero_streaks(days(zeros(60)))
    assert len(streaks) == 1 and streaks[0].days == 60


def test_streak_of_59_is_not_flagged():
    assert find_zero_streaks(days(zeros(59))) == []


def test_rain_breaks_the_streak():
    spec = zeros(40) + [(RainState.DATO, 1.5)] + zeros(40)
    assert find_zero_streaks(days(spec)) == []


def test_a_gap_is_not_a_zero_and_breaks_the_streak():
    spec = zeros(40) + [(RainState.SIN_FILA, None)] + zeros(40)
    assert find_zero_streaks(days(spec)) == []
    spec = zeros(40) + [(RainState.FILA_SIN_VALOR, None)] + zeros(40)
    assert find_zero_streaks(days(spec)) == []


def test_missing_calendar_days_break_the_streak():
    first = days(zeros(40))
    second = [DayValue(START + timedelta(days=45 + i), RainState.DATO, 0.0) for i in range(40)]
    assert find_zero_streaks(first + second) == []


def test_two_separate_streaks_are_reported_with_their_range():
    spec = zeros(60) + [(RainState.DATO, 3.0)] + zeros(70)
    streaks = find_zero_streaks(days(spec))
    assert [s.days for s in streaks] == [60, 70]
    assert streaks[0].start == START and streaks[1].end == START + timedelta(days=130)


def test_input_order_does_not_matter_and_empty_is_fine():
    assert find_zero_streaks([]) == []
    assert len(find_zero_streaks(list(reversed(days(zeros(60)))))) == 1


@pytest.fixture
def station_id(db: Session) -> int:
    source = Source(code="s", name="S", network="N", category=DataCategory.OBSERVADO)
    db.add(source)
    db.flush()
    station = Station(source_id=source.id, code="1", name="E1")
    db.add(station)
    db.flush()
    for i, (state, mm) in enumerate(zeros(70) + [(RainState.DATO, 2.0)]):
        db.add(
            RainfallRecord(
                station_id=station.id,
                obs_date=START + timedelta(days=i),
                state=state,
                mm=mm,
                category=DataCategory.OBSERVADO,
            )
        )
    db.commit()
    return station.id


def test_recompute_stores_flags_and_replaces_them(db: Session, station_id: int):
    service = QualityService(SqlQualityRepository(db))
    assert service.recompute_zero_streaks() == {station_id: 1}
    assert service.recompute_zero_streaks() == {station_id: 1}  # no se acumulan
    flags = list(db.scalars(select(QualityFlag)))
    assert len(flags) == 1
    flag = flags[0]
    assert flag.code == "ceros_prolongados" and flag.start_date == START
    assert flag.end_date == START + timedelta(days=69)
    assert '"days": 70' in flag.detail and flag.rule_version == "ceros_prolongados/1"


DATA = Path(__file__).resolve().parents[3] / "docs" / "datos"


@pytest.mark.skipif(not DATA.exists(), reason="docs/datos no está disponible")
def test_siga_demo_case_station_424_has_281_zero_days(db: Session):
    importer = ImportService(SqlIngestionRepository(db), date(2026, 10, 31))
    importer.import_stations(
        "siga_inta", "e.csv", (DATA / "estaciones_siga_formosa.csv").read_bytes()
    )
    importer.import_rainfall(
        "siga_inta",
        "l.csv",
        (DATA / "lluvia_diaria_siga_formosa.csv").read_bytes(),
        ImportMode.COMMIT,
    )
    QualityService(SqlQualityRepository(db)).recompute_zero_streaks()
    flag = db.scalars(
        select(QualityFlag)
        .join(Station)
        .where(Station.code == "424", QualityFlag.end_date == date(2016, 6, 26))
    ).one()
    assert flag.start_date == date(2015, 9, 20)
    assert (flag.end_date - flag.start_date).days + 1 == 281
