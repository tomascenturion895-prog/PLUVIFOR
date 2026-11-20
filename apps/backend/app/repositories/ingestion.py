import hashlib
import json
from datetime import date, datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import CoordsStatus, ImportMode, ImportStatus
from app.ingestion.sources import SourceDefinition
from app.ingestion.types import ImportReport, RainRow, StationRow
from app.models import ImportLog, RainfallRecord, Source, Station


class IngestionRepository(Protocol):
    """Lo que la importación necesita de la persistencia."""

    def ensure_source(self, definition: SourceDefinition) -> int: ...

    def find_source_id(self, code: str) -> int | None: ...

    def station_ids(self, source_id: int | None = None) -> dict[str, int]: ...

    def upsert_stations(self, source_id: int, rows: list[StationRow]) -> tuple[int, int]: ...

    def record_import(
        self,
        source_id: int,
        report: ImportReport,
        cutoff: date,
        started_at: datetime,
        created_by_user_id: int | None = None,
    ) -> int: ...

    def record_failed_attempt(
        self,
        source_id: int,
        mode: ImportMode,
        filename: str,
        reason_code: str,
        cutoff: date,
        started_at: datetime,
    ) -> int: ...

    def recent_imports(self, limit: int) -> list[tuple[ImportLog, str]]: ...

    def upsert_rainfall(
        self, rows: list[RainRow], station_ids: dict[str, int], import_id: int
    ) -> tuple[int, int]: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class SqlIngestionRepository:
    def __init__(self, session: Session):
        self._session = session

    def ensure_source(self, definition: SourceDefinition) -> int:
        source = self._session.scalar(select(Source).where(Source.code == definition.code))
        if source is None:
            source = Source(
                code=definition.code,
                name=definition.name,
                network=definition.network,
                category=definition.category,
                url=definition.url,
                day_cutoff_local=definition.day_cutoff_local,
            )
            self._session.add(source)
            self._session.flush()
        return source.id

    def find_source_id(self, code: str) -> int | None:
        return self._session.scalar(select(Source.id).where(Source.code == code))

    def station_ids(self, source_id: int | None = None) -> dict[str, int]:
        stmt = select(Station.code, Station.id)
        if source_id is not None:
            stmt = stmt.where(Station.source_id == source_id)
        rows = self._session.execute(stmt)
        return {code: station_id for code, station_id in rows}

    def upsert_stations(self, source_id: int, rows: list[StationRow]) -> tuple[int, int]:
        existing = {
            s.code: s
            for s in self._session.scalars(select(Station).where(Station.source_id == source_id))
        }
        inserted = updated = 0
        for row in rows:
            station = existing.get(row.code)
            if station is None:
                station = Station(source_id=source_id, code=row.code, name=row.name)
                self._session.add(station)
                inserted += 1
            else:
                updated += 1
            station.internal_code = row.internal_code
            station.name = row.name
            station.kind = row.kind
            station.locality = row.locality
            station.lat = row.lat
            station.lon = row.lon
            station.elevation_m = row.elevation_m
            station.active_from = row.active_from
            station.active_to = row.active_to
            has_coords = row.lat is not None and row.lon is not None
            station.coords_status = (
                CoordsStatus.VERIFICADA if has_coords else CoordsStatus.PENDIENTE
            )
        self._session.flush()
        return inserted, updated

    def record_import(
        self,
        source_id: int,
        report: ImportReport,
        cutoff: date,
        started_at: datetime,
        created_by_user_id: int | None = None,
    ) -> int:
        log = ImportLog(
            source_id=source_id,
            mode=ImportMode(report.mode),
            status=ImportStatus.COMPLETED,
            filename=report.filename,
            sha256=report.sha256,
            rows_read=report.rows_read,
            rows_accepted=report.rows_accepted,
            rows_rejected=report.rows_rejected,
            rejections=json.dumps(report.rejections_by_reason(), ensure_ascii=False),
            cutoff_applied=cutoff,
            started_at=started_at,
            created_by_user_id=created_by_user_id,
        )
        self._session.add(log)
        self._session.flush()
        return log.id

    def record_failed_attempt(
        self,
        source_id: int,
        mode: ImportMode,
        filename: str,
        reason_code: str,
        cutoff: date,
        started_at: datetime,
    ) -> int:
        """Deja constancia de un intento que no llegó a leer ninguna fila (por ejemplo, sin red)."""
        log = ImportLog(
            source_id=source_id,
            mode=mode,
            status=ImportStatus.FAILED,
            filename=filename,
            sha256=hashlib.sha256(reason_code.encode()).hexdigest(),
            rows_read=0,
            rows_accepted=0,
            rows_rejected=0,
            rejections=json.dumps({reason_code: 1}, ensure_ascii=False),
            cutoff_applied=cutoff,
            started_at=started_at,
        )
        self._session.add(log)
        self._session.flush()
        self._session.commit()
        return log.id

    def recent_imports(self, limit: int) -> list[tuple[ImportLog, str]]:
        """Las últimas cargas, la más nueva primero, con el código de su fuente."""
        rows = self._session.execute(
            select(ImportLog, Source.code)
            .join(Source, Source.id == ImportLog.source_id)
            .order_by(ImportLog.started_at.desc(), ImportLog.id.desc())
            .limit(limit)
        )
        return [(log, code) for log, code in rows]

    def upsert_rainfall(
        self, rows: list[RainRow], station_ids: dict[str, int], import_id: int
    ) -> tuple[int, int]:
        ids = set(station_ids.values())
        existing = {
            (r.station_id, r.obs_date, r.category): r
            for r in self._session.scalars(
                select(RainfallRecord).where(RainfallRecord.station_id.in_(ids))
            )
        }
        inserted = updated = 0
        for row in rows:
            station_id = station_ids[row.station_code]
            record = existing.get((station_id, row.obs_date, row.category))
            if record is None:
                record = RainfallRecord(
                    station_id=station_id, obs_date=row.obs_date, category=row.category
                )
                self._session.add(record)
                inserted += 1
            else:
                updated += 1
            record.import_id = import_id
            record.state = row.state
            record.mm = row.mm
            record.mm_chrono = row.mm_chrono
            record.unit = "mm"
            record.validation = row.validation
        self._session.flush()
        return inserted, updated

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
