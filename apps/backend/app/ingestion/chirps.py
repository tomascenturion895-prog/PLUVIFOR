"""Conector de lluvia diaria estimada CHIRPS v3 (SCRUM-43).

CHIRPS (Climate Hazards Center Infrared Precipitation with Stations) v3 provee
lluvia estimada por satélite y estaciones terrestres (resolución 0,05°).
Licencia: Creative Commons Attribution 4.0 International (CC BY 4.0).
DOI de los datos: 10.15780/G2JQ0P (2025).

Reglas que no se rompen:
1. Categoría obligatoria: ESTIMADO (nunca OBSERVADO).
2. Un hueco no es 0 mm (estado 'dato' solo con valor mm; huecos como 'sin_fila' o 'fila_sin_valor').
3. No se inventan datos ni coordenadas.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterator

from app.domain.enums import DataCategory
from app.ingestion.sources import SourceDefinition
from app.ingestion.types import InvalidFileError, RawRainRow, Rejection, StationRow

REQUIRED_COLUMNS = {
    "estacion_id",
    "fecha",
    "mm",
    "unidad",
    "estado",
    "categoria",
    "fuente",
}

CHIRPS_V3 = SourceDefinition(
    code="chirps_v3",
    name="CHIRPS v3 · Climate Hazards Center (UC Santa Barbara)",
    network="CHIRPS",
    category=DataCategory.ESTIMADO,
    url="https://www.chc.ucsb.edu/data/chirps3",
)


class ChirpsCsvConnector:
    """Conector que lee CSVs de extracción CHIRPS v3."""

    definition: SourceDefinition = CHIRPS_V3

    def read_stations(self, text: str) -> tuple[list[StationRow], list[Rejection]]:
        """CHIRPS no define estaciones nuevas: se extrae sobre las estaciones existentes."""
        return [], []

    def read_rainfall(self, text: str) -> Iterator[RawRainRow]:
        reader = csv.DictReader(io.StringIO(text))
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise InvalidFileError(f"Faltan columnas: {', '.join(sorted(missing))}")
        for index, row in enumerate(reader, start=2):
            yield RawRainRow(
                line=index,
                station_code=(row["estacion_id"] or "").strip(),
                obs_date=(row["fecha"] or "").strip(),
                mm=(row["mm"] or "").strip(),
                mm_chrono="",
                unit=(row["unidad"] or "").strip(),
                state=(row["estado"] or "").strip(),
                category=(row["categoria"] or "").strip(),
            )
