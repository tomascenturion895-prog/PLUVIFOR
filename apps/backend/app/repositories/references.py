from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import DataCategory
from app.ingestion.sources import SourceDefinition
from app.ingestion.types import StationRow
from app.models import ClimateReference, Station
from app.repositories.ingestion import SqlIngestionRepository


class ReferenceRepository(Protocol):
    def ensure_source(self, definition: SourceDefinition) -> int: ...

    def upsert_station(self, source_id: int, row: StationRow) -> int: ...

    def replace_normals(
        self, station_id: int, rows: list[tuple[int, float]], period: str, source_note: str
    ) -> None: ...

    def normals(self, station_id: int) -> list[ClimateReference]: ...

    def get_station(self, station_id: int) -> Station | None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class SqlReferenceRepository:
    def __init__(self, session: Session):
        self._session = session
        self._ingestion = SqlIngestionRepository(session)

    def ensure_source(self, definition: SourceDefinition) -> int:
        return self._ingestion.ensure_source(definition)

    def upsert_station(self, source_id: int, row: StationRow) -> int:
        self._ingestion.upsert_stations(source_id, [row])
        return self._ingestion.station_ids(source_id)[row.code]

    def replace_normals(
        self, station_id: int, rows: list[tuple[int, float]], period: str, source_note: str
    ) -> None:
        existing = {
            n.month: n
            for n in self._session.scalars(
                select(ClimateReference).where(
                    ClimateReference.station_id == station_id, ClimateReference.period == period
                )
            )
        }
        for month, mm in rows:
            current = existing.get(month)
            if current is None:
                self._session.add(
                    ClimateReference(
                        station_id=station_id,
                        month=month,
                        normal_mm=mm,
                        period=period,
                        source_note=source_note,
                        category=DataCategory.REFERENCIA,
                    )
                )
            else:
                current.normal_mm = mm
                current.source_note = source_note
        self._session.flush()

    def normals(self, station_id: int) -> list[ClimateReference]:
        return list(
            self._session.scalars(
                select(ClimateReference)
                .where(ClimateReference.station_id == station_id)
                .order_by(ClimateReference.period, ClimateReference.month)
            )
        )

    def get_station(self, station_id: int) -> Station | None:
        return self._session.get(Station, station_id)

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
