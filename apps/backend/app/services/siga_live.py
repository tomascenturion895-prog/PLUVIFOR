"""Importación del SIGA en vivo con respaldo en el CSV versionado (SCRUM-64).

Si el SIGA no responde, se registra el intento fallido en `import_logs`, se usa el CSV de
`docs/datos/` y se **avisa** en el resultado: nunca se hace pasar el respaldo por datos en vivo.
Se respeta la fecha de corte: no se pide nada posterior.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Literal

from app.domain.enums import ImportMode
from app.ingestion.siga_live import SigaLiveClient, SigaUnavailableError, rows_to_csv
from app.ingestion.sources import SIGA_INTA
from app.ingestion.types import ImportReport, InvalidFileError
from app.repositories.ingestion import IngestionRepository
from app.services.importer import ImportService

LIVE_FILENAME = "siga_en_vivo.csv"
FALLBACK_REASON = "siga_en_vivo_no_disponible"


@dataclass(frozen=True)
class LiveImportResult:
    report: ImportReport
    origin: Literal["en_vivo", "respaldo_csv"]
    reason: str | None = None  # por qué se usó el respaldo


class SigaLiveImporter:
    def __init__(
        self,
        importer: ImportService,
        repository: IngestionRepository,
        client: SigaLiveClient,
        fallback_csv: Path,
        cutoff: date,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ):
        self._importer = importer
        self._repository = repository
        self._client = client
        self._fallback_csv = fallback_csv
        self._cutoff = cutoff
        self._clock = clock

    def run(
        self, stations: list[int], start: date, end: date, mode: ImportMode
    ) -> LiveImportResult:
        if not stations or any(s < 1 for s in stations):
            raise InvalidFileError("Indicá al menos una estación con un número positivo.")
        end = min(end, self._cutoff)  # no se pide nada posterior al corte
        if start > end:
            raise InvalidFileError("El período es posterior a la fecha de corte o está invertido.")
        started_at = self._clock()
        try:
            parts: list[str] = []
            for station in stations:
                rows = self._client.daily(station, start, end)
                text = rows_to_csv(station, rows, start, end)
                parts.append(text if not parts else text.split("\n", 1)[1])
        except SigaUnavailableError as exc:
            return self._fallback(mode, str(exc), started_at)
        report = self._importer.import_rainfall(
            SIGA_INTA.code, LIVE_FILENAME, "".join(parts).encode(), mode
        )
        return LiveImportResult(report, "en_vivo")

    def _fallback(self, mode: ImportMode, reason: str, started_at: datetime) -> LiveImportResult:
        source_id = self._repository.find_source_id(SIGA_INTA.code)
        if source_id is None:
            raise InvalidFileError("La fuente no existe: importar primero el catálogo.")
        self._repository.record_failed_attempt(
            source_id, mode, LIVE_FILENAME, FALLBACK_REASON, self._cutoff, started_at
        )
        report = self._importer.import_rainfall(
            SIGA_INTA.code, self._fallback_csv.name, self._fallback_csv.read_bytes(), mode
        )
        return LiveImportResult(report, "respaldo_csv", reason)
