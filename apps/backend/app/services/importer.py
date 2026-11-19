import hashlib
import json
from collections.abc import Callable, Mapping
from datetime import UTC, date, datetime
from pathlib import PurePath

from app.domain.enums import ImportMode
from app.ingestion.registry import DEFAULT_CONNECTORS
from app.ingestion.sources import SourceConnector
from app.ingestion.types import (
    ImportLogEntry,
    ImportReport,
    InvalidFileError,
    RainRow,
    Rejection,
)
from app.ingestion.upload import DEFAULT_MAX_UPLOAD_BYTES, check_upload
from app.ingestion.validation import RowValidator
from app.repositories.ingestion import IngestionRepository


def _decode(content: bytes) -> str:
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InvalidFileError("El archivo no está en UTF-8.") from exc


def _safe_name(filename: str) -> str:
    """Solo el nombre del archivo, sin carpetas ni caracteres de control."""
    name = PurePath(filename.replace("\\", "/")).name
    return "".join(ch for ch in name if ch.isprintable())[:255] or "archivo"


class ImportService:
    """Orquesta la importación. No conoce SQL ni el formato de ningún archivo en particular."""

    def __init__(
        self,
        repository: IngestionRepository,
        cutoff: date,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        connectors: Mapping[str, SourceConnector] | None = None,
        max_upload_bytes: int = DEFAULT_MAX_UPLOAD_BYTES,
    ):
        self._repository = repository
        self._cutoff = cutoff
        self._clock = clock
        self._connectors = DEFAULT_CONNECTORS if connectors is None else connectors
        self._max_upload_bytes = max_upload_bytes

    def _connector(self, source_code: str) -> SourceConnector:
        connector = self._connectors.get(source_code)
        if connector is None:
            raise InvalidFileError("Fuente desconocida.")
        return connector

    def import_stations(
        self,
        source_code: str,
        filename: str,
        content: bytes,
        mode: ImportMode = ImportMode.COMMIT,
    ) -> ImportReport:
        connector = self._connector(source_code)
        check_upload(filename, content, self._max_upload_bytes)
        definition = connector.definition
        rows, rejections = connector.read_stations(_decode(content))
        report = ImportReport(
            filename=_safe_name(filename),
            sha256=hashlib.sha256(content).hexdigest(),
            mode=mode.value,
            rows_read=len(rows) + len(rejections),
            accepted=list(rows),
            rejections=rejections,
        )
        if mode is ImportMode.AUDIT:
            return report  # simulación: no se toca la base
        try:
            source_id = self._repository.ensure_source(definition)
            report.inserted, report.updated = self._repository.upsert_stations(source_id, rows)
            self._repository.commit()
        except Exception:
            self._repository.rollback()
            raise
        return report

    def import_rainfall(
        self,
        source_code: str,
        filename: str,
        content: bytes,
        mode: ImportMode,
        record_audit: bool = True,
    ) -> ImportReport:
        """`record_audit=False` deja una auditoría sin ninguna escritura (la usa la API)."""
        started_at = self._clock()
        connector = self._connector(source_code)
        check_upload(filename, content, self._max_upload_bytes)
        source_id = self._repository.find_source_id(source_code)
        if source_id is None:
            raise InvalidFileError("La fuente no existe: importar primero el catálogo.")
        station_ids = self._repository.station_ids(source_id)

        report = ImportReport(
            filename=_safe_name(filename),
            sha256=hashlib.sha256(content).hexdigest(),
            mode=mode.value,
        )
        validator = RowValidator(self._cutoff, set(station_ids))
        for raw in connector.read_rainfall(_decode(content)):
            report.rows_read += 1
            result = validator.validate(raw)
            if isinstance(result, RainRow):
                report.accepted.append(result)
            else:
                report.rejections.append(Rejection(raw.line, result))

        if mode is ImportMode.AUDIT and not record_audit:
            return report
        try:
            import_id = self._repository.record_import(source_id, report, self._cutoff, started_at)
            if mode is ImportMode.COMMIT:
                report.inserted, report.updated = self._repository.upsert_rainfall(
                    [row for row in report.accepted if isinstance(row, RainRow)],
                    station_ids,
                    import_id,
                )
            self._repository.commit()
        except Exception:
            self._repository.rollback()
            raise
        return report

    def recent_imports(self, limit: int = 20) -> list[ImportLogEntry]:
        """Historial de cargas (import_logs), de la más nueva a la más vieja."""
        return [
            ImportLogEntry(
                id=log.id,
                source=source_code,
                mode=log.mode.value,
                status=log.status.value,
                filename=log.filename,
                sha256=log.sha256,
                rows_read=log.rows_read,
                rows_accepted=log.rows_accepted,
                rows_rejected=log.rows_rejected,
                rejections_by_reason=json.loads(log.rejections) if log.rejections else {},
                cutoff_applied=log.cutoff_applied,
                started_at=log.started_at,
            )
            for log, source_code in self._repository.recent_imports(limit)
        ]
