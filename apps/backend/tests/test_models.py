"""Las reglas de calidad viven en la base: se prueban contra la base, no contra el código."""

from datetime import UTC, date, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import create_db_engine, create_session_factory
from app.domain.enums import (
    CoordsStatus,
    DataCategory,
    ImportMode,
    ImportStatus,
    RainState,
    Severity,
)
from app.models import (
    ClimateReference,
    ImportLog,
    QualityFlag,
    RainfallRecord,
    Source,
    Station,
)


@pytest.fixture
def session() -> Session:
    engine = create_db_engine("sqlite://")
    Base.metadata.create_all(engine)
    with create_session_factory(engine)() as db:
        yield db
    engine.dispose()


@pytest.fixture
def station(session: Session) -> Station:
    source = Source(
        code="siga_inta", name="SIGA INTA", network="INTA", category=DataCategory.OBSERVADO
    )
    session.add(source)
    session.flush()
    st = Station(source_id=source.id, code="424", name="El Colorado")
    session.add(st)
    session.flush()
    return st


def _record(station: Station, **overrides) -> RainfallRecord:
    values = {
        "station_id": station.id,
        "obs_date": date(2016, 1, 1),
        "state": RainState.DATO,
        "mm": 0.0,
        "category": DataCategory.OBSERVADO,
    }
    values.update(overrides)
    return RainfallRecord(**values)


def test_zero_mm_is_a_valid_data_day(session: Session, station: Station) -> None:
    session.add(_record(station, mm=0.0))
    session.flush()


@pytest.mark.parametrize("state", [RainState.FILA_SIN_VALOR, RainState.SIN_FILA])
def test_gap_is_stored_without_mm(session: Session, station: Station, state: RainState) -> None:
    session.add(_record(station, state=state, mm=None))
    session.flush()


@pytest.mark.parametrize("state", [RainState.FILA_SIN_VALOR, RainState.SIN_FILA])
def test_gap_cannot_carry_zero_mm(session: Session, station: Station, state: RainState) -> None:
    session.add(_record(station, state=state, mm=0.0))
    with pytest.raises(IntegrityError):
        session.flush()


def test_data_day_requires_mm(session: Session, station: Station) -> None:
    session.add(_record(station, state=RainState.DATO, mm=None))
    with pytest.raises(IntegrityError):
        session.flush()


def test_negative_rain_is_rejected(session: Session, station: Station) -> None:
    session.add(_record(station, mm=-1.0))
    with pytest.raises(IntegrityError):
        session.flush()


def test_chrono_value_cannot_fill_a_gap(session: Session, station: Station) -> None:
    session.add(_record(station, state=RainState.FILA_SIN_VALOR, mm=None, mm_chrono=3.2))
    session.flush()
    stored = session.query(RainfallRecord).one()
    assert stored.mm is None
    assert stored.mm_chrono == 3.2


def test_same_day_and_category_cannot_repeat(session: Session, station: Station) -> None:
    session.add_all([_record(station), _record(station)])
    with pytest.raises(IntegrityError):
        session.flush()


def test_observed_and_estimated_can_share_a_day(session: Session, station: Station) -> None:
    session.add_all([_record(station), _record(station, category=DataCategory.ESTIMADO, mm=1.0)])
    session.flush()


def test_unit_must_be_mm(session: Session, station: Station) -> None:
    session.add(_record(station, unit="in"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_foreign_keys_are_enforced(session: Session) -> None:
    session.add(
        RainfallRecord(
            station_id=999,
            obs_date=date(2016, 1, 1),
            state=RainState.SIN_FILA,
            category=DataCategory.OBSERVADO,
        )
    )
    with pytest.raises(IntegrityError):
        session.flush()


def test_station_defaults_to_pending_coordinates(session: Session, station: Station) -> None:
    assert station.coords_status == CoordsStatus.PENDIENTE
    assert station.lat is None and station.lon is None


def test_verified_station_requires_coordinates(session: Session, station: Station) -> None:
    station.coords_status = CoordsStatus.VERIFICADA
    with pytest.raises(IntegrityError):
        session.flush()


def test_station_code_is_unique_per_source(session: Session, station: Station) -> None:
    session.add(Station(source_id=station.source_id, code="424", name="Duplicada"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_quality_flag_range_must_be_ordered(session: Session, station: Station) -> None:
    session.add(
        QualityFlag(
            station_id=station.id,
            code="ceros_prolongados",
            start_date=date(2016, 6, 26),
            end_date=date(2015, 9, 20),
            severity=Severity.ALERTA,
            rule_version="1",
        )
    )
    with pytest.raises(IntegrityError):
        session.flush()


def test_climate_reference_must_be_reference_category(session: Session, station: Station) -> None:
    base = {
        "station_id": station.id,
        "month": 1,
        "normal_mm": 120.0,
        "period": "1991-2020",
        "source_note": "fuente verificada",
    }
    session.add(ClimateReference(**base))
    session.flush()
    session.add(ClimateReference(**{**base, "month": 2, "category": DataCategory.OBSERVADO}))
    with pytest.raises(IntegrityError):
        session.flush()


def test_climate_reference_month_out_of_range(session: Session, station: Station) -> None:
    session.add(
        ClimateReference(
            station_id=station.id,
            month=13,
            normal_mm=1.0,
            period="1991-2020",
            source_note="x",
        )
    )
    with pytest.raises(IntegrityError):
        session.flush()


def test_import_log_counts_must_be_consistent(session: Session, station: Station) -> None:
    session.add(
        ImportLog(
            source_id=station.source_id,
            mode=ImportMode.AUDIT,
            status=ImportStatus.COMPLETED,
            filename="x.csv",
            sha256="0" * 64,
            rows_read=10,
            rows_accepted=8,
            rows_rejected=5,
            cutoff_applied=date(2026, 10, 31),
            started_at=datetime(2026, 11, 1, tzinfo=UTC),
        )
    )
    with pytest.raises(IntegrityError):
        session.flush()
