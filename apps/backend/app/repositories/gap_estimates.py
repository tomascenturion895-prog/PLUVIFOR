import json
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Protocol

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.domain.enums import CoordsStatus, DataCategory, RainState
from app.domain.estimation import Estimacion
from app.models import GapEstimate, QualityFlag, RainfallRecord, Source, Station


@dataclass(frozen=True)
class Punto:
    """Una estación y, si están verificadas, sus coordenadas."""

    id: int
    name: str
    lat: float | None
    lon: float | None
    kind: str | None = None  # tipo de estación (convencional, automática…)
    day_cutoff: str | None = None  # hora de corte del «día» de su fuente


@dataclass(frozen=True)
class DiaObservado:
    state: RainState
    mm: float | None


@dataclass(frozen=True)
class Guardar:
    station_id: int
    obs_date: date
    gap_state: RainState
    estimacion: Estimacion


class GapEstimateRepository(Protocol):
    def stations(self, station_id: int | None) -> list[Punto]: ...

    def neighbors_candidates(self) -> list[Punto]: ...

    def data_span(self, station_id: int) -> tuple[date, date] | None: ...

    def observed_days(
        self, station_ids: list[int], start: date, end: date
    ) -> dict[tuple[int, date], DiaObservado]: ...

    def flagged_days(
        self, station_ids: list[int], start: date, end: date
    ) -> set[tuple[int, date]]: ...

    def chirps_values(self, station_id: int, start: date, end: date) -> dict[date, float]: ...

    def replace(
        self, station_ids: list[int], start: date, end: date, items: list[Guardar]
    ) -> None: ...

    def search(
        self, station_id: int | None, start: date | None, end: date | None, limit: int, offset: int
    ) -> tuple[list[GapEstimate], int]: ...


class SqlGapEstimateRepository:
    def __init__(self, session: Session):
        self._session = session

    def _puntos(self, only_verified: bool, station_id: int | None) -> list[Punto]:
        query = select(Station, Source.day_cutoff_local).join(
            Source, Station.source_id == Source.id
        )
        if only_verified:
            query = query.where(Station.coords_status == CoordsStatus.VERIFICADA)
        if station_id is not None:
            query = query.where(Station.id == station_id)
        puntos = []
        for station, corte in self._session.execute(query.order_by(Station.id)):
            # Coordenadas pendientes no cuentan: nunca se asume una ubicación.
            verified = station.coords_status == CoordsStatus.VERIFICADA
            puntos.append(
                Punto(
                    station.id,
                    station.name,
                    station.lat if verified else None,
                    station.lon if verified else None,
                    station.kind,
                    corte,
                )
            )
        return puntos

    def stations(self, station_id: int | None) -> list[Punto]:
        return self._puntos(False, station_id)

    def neighbors_candidates(self) -> list[Punto]:
        return self._puntos(True, None)

    def data_span(self, station_id: int) -> tuple[date, date] | None:
        low, high = self._session.execute(
            select(func.min(RainfallRecord.obs_date), func.max(RainfallRecord.obs_date)).where(
                RainfallRecord.station_id == station_id,
                RainfallRecord.category == DataCategory.OBSERVADO,
                RainfallRecord.state == RainState.DATO,
            )
        ).one()
        return (low, high) if low is not None else None

    def observed_days(
        self, station_ids: list[int], start: date, end: date
    ) -> dict[tuple[int, date], DiaObservado]:
        if not station_ids:
            return {}
        rows = self._session.execute(
            select(
                RainfallRecord.station_id,
                RainfallRecord.obs_date,
                RainfallRecord.state,
                RainfallRecord.mm,
            ).where(
                RainfallRecord.station_id.in_(station_ids),
                RainfallRecord.category == DataCategory.OBSERVADO,
                RainfallRecord.obs_date.between(start, end),
            )
        )
        return {(r.station_id, r.obs_date): DiaObservado(r.state, r.mm) for r in rows}

    def flagged_days(self, station_ids: list[int], start: date, end: date) -> set[tuple[int, date]]:
        if not station_ids:
            return set()
        flags = self._session.scalars(
            select(QualityFlag).where(
                QualityFlag.station_id.in_(station_ids),
                QualityFlag.start_date <= end,
                QualityFlag.end_date >= start,
            )
        )
        days: set[tuple[int, date]] = set()
        for flag in flags:
            day, last = max(flag.start_date, start), min(flag.end_date, end)
            while day <= last:
                days.add((flag.station_id, day))
                day += timedelta(days=1)
        return days

    def chirps_values(self, station_id: int, start: date, end: date) -> dict[date, float]:
        rows = self._session.execute(
            select(RainfallRecord.obs_date, RainfallRecord.mm).where(
                RainfallRecord.station_id == station_id,
                RainfallRecord.category == DataCategory.ESTIMADO,
                RainfallRecord.state == RainState.DATO,
                RainfallRecord.obs_date.between(start, end),
            )
        )
        return {r.obs_date: r.mm for r in rows if r.mm is not None}

    def replace(self, station_ids: list[int], start: date, end: date, items: list[Guardar]) -> None:
        """Las estimaciones son datos derivados: se regeneran, no se editan."""
        self._session.execute(
            delete(GapEstimate).where(
                GapEstimate.station_id.in_(station_ids),
                GapEstimate.obs_date.between(start, end),
            )
        )
        self._session.add_all(
            GapEstimate(
                station_id=i.station_id,
                obs_date=i.obs_date,
                mm=i.estimacion.mm,
                category=DataCategory.ESTIMADO,
                gap_state=i.gap_state,
                method=i.estimacion.method,
                detail=json.dumps(i.estimacion.detail, ensure_ascii=False),
            )
            for i in items
        )
        self._session.commit()

    def search(
        self, station_id: int | None, start: date | None, end: date | None, limit: int, offset: int
    ) -> tuple[list[GapEstimate], int]:
        base = select(GapEstimate)
        if station_id is not None:
            base = base.where(GapEstimate.station_id == station_id)
        if start is not None:
            base = base.where(GapEstimate.obs_date >= start)
        if end is not None:
            base = base.where(GapEstimate.obs_date <= end)
        total = self._session.scalar(select(func.count()).select_from(base.subquery())) or 0
        rows = self._session.scalars(
            base.order_by(GapEstimate.obs_date, GapEstimate.station_id).limit(limit).offset(offset)
        ).all()
        return list(rows), total
