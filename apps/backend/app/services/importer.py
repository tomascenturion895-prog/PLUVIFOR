import hashlib
from collections.abc import Callable
from datetime import UTC, date, datetime
from pathlib import PurePath

from app.domain.enums import ImportMode
from app.ingestion.siga import InvalidFileError, read_rainfall_rows
from app.ingestion.sources import KNOWN_SOURCES
from app.ingestion.stations import read_stations
from app.ingestion.types import ImportReport, RainRow, Rejection
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
    ):
        self._repository = repository
        self._cutoff = cutoff
        self._clock = clock

    def import_stations(self, source_code: str, filename: str, content: bytes) -> ImportReport:
        definition = KNOWN_SOURCES.get(source_code)
        if definition is None:
            raise InvalidFileError(f"Fuente desconocida: {source_code}")
        text = _decode(content)
        rows, rejections = read_stations(text)
        report = ImportReport(
            filename=_safe_name(filename),
            sha256=hashlib.sha256(content).hexdigest(),
            mode=ImportMode.COMMIT.value,
            rows_read=len(rows) + len(rejections),
            accepted=list(rows),
            rejections=rejections,
        )
        try:
            source_id = self._repository.ensure_source(definition)
            report.inserted, report.updated = self._repository.upsert_stations(source_id, rows)
            self._repository.commit()
        except Exception:
            self._repository.rollback()
            raise
        return report

    def import_rainfall(
        self, source_code: str, filename: str, content: bytes, mode: ImportMode
    ) -> ImportReport:
        started_at = self._clock()
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
        for raw in read_rainfall_rows(_decode(content)):
            report.rows_read += 1
            result = validator.validate(raw)
            if isinstance(result, RainRow):
                report.accepted.append(result)
            else:
                report.rejections.append(Rejection(raw.line, result))

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
