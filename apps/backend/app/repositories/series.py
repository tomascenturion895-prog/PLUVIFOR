from dataclasses import dataclass
from datetime import date
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.enums import DataCategory, Validation
from app.domain.quality import DayValue
from app.models import QualityFlag, RainfallRecord, Station


@dataclass(frozen=True)
class SeriesData:
    days: list[DayValue]
    unvalidated_days: int


class SeriesRepository(Protocol):
    def get_station(self, station_id: int) -> Station | None: ...

    def read(
        self, station_id: int, category: DataCategory, date_from: date, date_to: date
    ) -> SeriesData: ...

    def flags(self, station_id: int, date_from: date, date_to: date) -> list[QualityFlag]: ...


class SqlSeriesRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_station(self, station_id: int) -> Station | None:
        return self._session.scalar(
            select(Station).where(Station.id == station_id).options(selectinload(Station.source))
        )

    def read(
        self, station_id: int, category: DataCategory, date_from: date, date_to: date
    ) -> SeriesData:
        rows = self._session.execute(
            select(
                RainfallRecord.obs_date,
                RainfallRecord.state,
                RainfallRecord.mm,
                RainfallRecord.validation,
            )
            .where(
                RainfallRecord.station_id == station_id,
                RainfallRecord.category == category,
                RainfallRecord.obs_date.between(date_from, date_to),
            )
            .order_by(RainfallRecord.obs_date)
        ).all()
        days = [DayValue(obs_date, state, mm) for obs_date, state, mm, _ in rows]
        unvalidated = sum(
            1
            for *_, mm, validation in rows
            if mm is not None and validation is Validation.SIN_VALIDAR
        )
        return SeriesData(days, unvalidated)

    def flags(self, station_id: int, date_from: date, date_to: date) -> list[QualityFlag]:
        return list(
            self._session.scalars(
                select(QualityFlag)
                .where(
                    QualityFlag.station_id == station_id,
                    QualityFlag.start_date <= date_to,
                    QualityFlag.end_date >= date_from,
                )
                .order_by(QualityFlag.start_date)
            )
        )
