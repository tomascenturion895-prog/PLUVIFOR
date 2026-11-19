from dataclasses import dataclass
from datetime import date
from typing import Literal, Protocol

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session, selectinload

from app.domain.enums import DataCategory, RainState, Validation
from app.domain.quality import DayValue
from app.models import QualityFlag, RainfallRecord, Station


@dataclass(frozen=True)
class SeriesData:
    days: list[DayValue]
    unvalidated_days: int


@dataclass(frozen=True)
class StationAccumulated:
    """Acumulado de una estación en un período.

    `accumulated_mm` es None si no hubo ningún día con dato: los huecos no suman 0.
    """

    station_id: int
    station_name: str
    data_days: int
    gap_days: int  # filas guardadas sin valor (fila_sin_valor y sin_fila)
    accumulated_mm: float | None


class SeriesRepository(Protocol):
    def get_station(self, station_id: int) -> Station | None: ...

    def read(
        self, station_id: int, category: DataCategory, date_from: date, date_to: date
    ) -> SeriesData: ...

    def flags(self, station_id: int, date_from: date, date_to: date) -> list[QualityFlag]: ...

    def accumulated_by_station(
        self, station_id: int, category: DataCategory, date_from: date, date_to: date
    ) -> StationAccumulated | None: ...

    def accumulated_by_group(
        self,
        group: Literal["zone", "department"],
        value: str,
        category: DataCategory,
        date_from: date,
        date_to: date,
    ) -> list[StationAccumulated]: ...


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

    def accumulated_by_station(
        self, station_id: int, category: DataCategory, date_from: date, date_to: date
    ) -> StationAccumulated | None:
        rows = self._accumulated(Station.id == station_id, category, date_from, date_to)
        return rows[0] if rows else None

    def accumulated_by_group(
        self,
        group: Literal["zone", "department"],
        value: str,
        category: DataCategory,
        date_from: date,
        date_to: date,
    ) -> list[StationAccumulated]:
        column = Station.zone if group == "zone" else Station.department
        return self._accumulated(column == value, category, date_from, date_to)

    def _accumulated(
        self, station_filter, category: DataCategory, date_from: date, date_to: date
    ) -> list[StationAccumulated]:
        """Una fila por estación, incluso las que no tienen ningún registro en el período.

        Las categorías nunca se mezclan (se filtra por una) y las estaciones no se suman entre sí.
        """
        is_data = RainfallRecord.state == RainState.DATO
        stmt = (
            select(
                Station.id,
                Station.name,
                func.coalesce(func.sum(case((is_data, 1), else_=0)), 0),
                func.coalesce(
                    func.sum(case((RainfallRecord.id.is_not(None) & ~is_data, 1), else_=0)), 0
                ),
                func.sum(RainfallRecord.mm),  # NULL si no hay ningún día con dato
            )
            .select_from(Station)
            .outerjoin(
                RainfallRecord,
                and_(
                    RainfallRecord.station_id == Station.id,
                    RainfallRecord.category == category,
                    RainfallRecord.obs_date.between(date_from, date_to),
                ),
            )
            .where(station_filter)
            .group_by(Station.id, Station.name)
            .order_by(Station.id)
        )
        return [
            StationAccumulated(
                station_id=station_id,
                station_name=name,
                data_days=int(data_days),
                gap_days=int(gap_days),
                accumulated_mm=None if total is None else round(float(total), 2),
            )
            for station_id, name, data_days, gap_days, total in self._session.execute(stmt)
        ]
