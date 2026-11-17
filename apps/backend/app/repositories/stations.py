from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.domain.enums import CoordsStatus
from app.models import Source, Station


@dataclass(frozen=True)
class StationFilters:
    source_code: str | None = None
    department: str | None = None
    zone: str | None = None
    coords_status: CoordsStatus | None = None
    text: str | None = None


@dataclass(frozen=True)
class Page:
    limit: int = 100
    offset: int = 0


class StationRepository(Protocol):
    """Contrato que usan los servicios: no saben si detrás hay SQL u otra cosa."""

    def search(self, filters: StationFilters, page: Page) -> tuple[list[Station], int]: ...

    def get(self, station_id: int) -> Station | None: ...


class SqlStationRepository:
    def __init__(self, session: Session):
        self._session = session

    def search(self, filters: StationFilters, page: Page) -> tuple[list[Station], int]:
        base = select(Station).join(Source, Station.source_id == Source.id)
        base = self._apply(base, filters)
        total = self._session.scalar(select(func.count()).select_from(base.subquery())) or 0
        rows = self._session.scalars(
            base.options(selectinload(Station.source))
            .order_by(Station.name, Station.id)
            .limit(page.limit)
            .offset(page.offset)
        ).all()
        return list(rows), total

    def get(self, station_id: int) -> Station | None:
        return self._session.scalar(
            select(Station).where(Station.id == station_id).options(selectinload(Station.source))
        )

    @staticmethod
    def _apply(query: Select, filters: StationFilters) -> Select:
        if filters.source_code:
            query = query.where(Source.code == filters.source_code)
        if filters.department:
            query = query.where(Station.department == filters.department)
        if filters.zone:
            query = query.where(Station.zone == filters.zone)
        if filters.coords_status:
            query = query.where(Station.coords_status == filters.coords_status)
        if filters.text:
            pattern = f"%{filters.text.lower()}%"
            query = query.where(
                func.lower(Station.name).like(pattern) | func.lower(Station.locality).like(pattern)
            )
        return query
