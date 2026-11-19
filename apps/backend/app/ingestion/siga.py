"""Lector del CSV de lluvia diaria del SIGA (`docs/datos/lluvia_diaria_siga_formosa.csv`)."""

__all__ = ["REQUIRED_COLUMNS", "InvalidFileError", "SigaCsvConnector", "read_rainfall_rows"]

import csv
import io
from collections.abc import Iterator

from app.ingestion.sources import SIGA_INTA, SourceDefinition
from app.ingestion.stations import read_stations
from app.ingestion.types import InvalidFileError, RawRainRow, Rejection, StationRow

REQUIRED_COLUMNS = {
    "estacion_id",
    "fecha",
    "mm_pluviometrica",
    "mm_cronologica",
    "unidad",
    "estado",
    "categoria",
}


def read_rainfall_rows(text: str) -> Iterator[RawRainRow]:
    reader = csv.DictReader(io.StringIO(text))
    missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
    if missing:
        raise InvalidFileError(f"Faltan columnas: {', '.join(sorted(missing))}")
    for index, row in enumerate(reader, start=2):  # la línea 1 es el encabezado
        yield RawRainRow(
            line=index,
            station_code=(row["estacion_id"] or "").strip(),
            obs_date=(row["fecha"] or "").strip(),
            mm=(row["mm_pluviometrica"] or "").strip(),
            mm_chrono=(row["mm_cronologica"] or "").strip(),
            unit=(row["unidad"] or "").strip(),
            state=(row["estado"] or "").strip(),
            category=(row["categoria"] or "").strip(),
        )


class SigaCsvConnector:
    """Conector del SIGA/INTA que lee los CSV versionados en `docs/datos/`."""

    definition: SourceDefinition = SIGA_INTA

    def read_stations(self, text: str) -> tuple[list[StationRow], list[Rejection]]:
        return read_stations(text)

    def read_rainfall(self, text: str) -> Iterator[RawRainRow]:
        return read_rainfall_rows(text)
