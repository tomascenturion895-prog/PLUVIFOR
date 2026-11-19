from dataclasses import dataclass
from datetime import date
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.domain.enums import DataCategory, RainState
from app.models import RainfallRecord, Station


@dataclass(frozen=True)
class LastReading:
    station: Station
    obs_date: date | None
    mm: float | None


class NetworkHealthRepository(Protocol):
    def last_readings(self, cutoff: date) -> list[LastReading]: ...


class SqlNetworkHealthRepository:
    def __init__(self, session: Session):
        self._session = session

    def last_readings(self, cutoff: date) -> list[LastReading]:
        """Última lectura observada con valor (≤ corte) de cada estación; None si no tiene."""
        last = (
            select(RainfallRecord.station_id, func.max(RainfallRecord.obs_date).label("d"))
            .where(
                RainfallRecord.category == DataCategory.OBSERVADO,
                RainfallRecord.state == RainState.DATO,
                RainfallRecord.obs_date <= cutoff,
            )
            .group_by(RainfallRecord.station_id)
            .subquery()
        )
        rows = self._session.execute(
            select(Station, last.c.d, RainfallRecord.mm)
            .outerjoin(last, last.c.station_id == Station.id)
            .outerjoin(
                RainfallRecord,
                (RainfallRecord.station_id == Station.id)
                & (RainfallRecord.obs_date == last.c.d)
                & (RainfallRecord.category == DataCategory.OBSERVADO),
            )
            .options(selectinload(Station.source))
            .order_by(Station.name, Station.id)
        )
        return [LastReading(station, d, mm) for station, d, mm in rows]
