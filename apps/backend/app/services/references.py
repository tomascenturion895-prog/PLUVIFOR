import csv
import io
from dataclasses import dataclass

from app.domain.enums import DataCategory
from app.errors import ApiError
from app.ingestion.sources import SourceDefinition
from app.ingestion.types import InvalidFileError, StationRow
from app.ingestion.upload import check_upload
from app.models import ClimateReference, Station
from app.repositories.references import ReferenceRepository

NORMALS_SOURCE = SourceDefinition(
    code="smn_normales",
    name="SMN · Estadísticas Climatológicas Normales",
    network="SMN",
    category=DataCategory.REFERENCIA,
    url="https://repositorio.smn.gob.ar/handle/20.500.12160/2506",
)
REQUIRED = {
    "station_code",
    "station_name",
    "lat",
    "lon",
    "month",
    "normal_mm",
    "period",
    "source_note",
}


@dataclass(frozen=True)
class NormalsImport:
    station_code: str
    months: int
    period: str


@dataclass(frozen=True)
class StationNormals:
    station: Station
    normals: list[ClimateReference]


def _number(value: str, field: str, line: int) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise InvalidFileError(f"Línea {line}: «{field}» no es un número.") from exc
    if number != number or number in (float("inf"), float("-inf")):
        raise InvalidFileError(f"Línea {line}: «{field}» no es un número válido.")
    return number


class ReferenceService:
    """Normales climáticas: siempre `referencia` y solo con una fuente indicada en el archivo."""

    def __init__(self, repository: ReferenceRepository):
        self._repository = repository

    def import_normals(self, filename: str, content: bytes) -> NormalsImport:
        check_upload(filename, content)
        reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
        if not REQUIRED <= set(reader.fieldnames or []):
            raise InvalidFileError(f"Faltan columnas: {', '.join(sorted(REQUIRED))}.")
        rows = list(reader)
        if not rows:
            raise InvalidFileError("El archivo no tiene filas.")

        first = rows[0]
        station = StationRow(
            code=first["station_code"].strip(),
            internal_code=None,
            name=first["station_name"].strip(),
            kind=None,
            locality=None,
            lat=_number(first["lat"], "lat", 2),
            lon=_number(first["lon"], "lon", 2),
            elevation_m=_number(first["elevation_m"], "elevation_m", 2)
            if (first.get("elevation_m") or "").strip()
            else None,
            active_from=None,
            active_to=None,
        )
        if not station.code or not station.name:
            raise InvalidFileError("Falta el código o el nombre de la estación.")
        period, note = first["period"].strip(), first["source_note"].strip()
        if not period or not note:
            raise InvalidFileError("Toda normal necesita su período y la nota de su fuente.")

        values: dict[int, float] = {}
        for line, row in enumerate(rows, start=2):
            if (row["station_code"].strip(), row["period"].strip()) != (station.code, period):
                raise InvalidFileError(f"Línea {line}: el archivo mezcla estaciones o períodos.")
            if not row["source_note"].strip():
                raise InvalidFileError(f"Línea {line}: falta la fuente de la normal.")
            month = _number(row["month"], "month", line)
            if month != int(month) or not 1 <= month <= 12:
                raise InvalidFileError(f"Línea {line}: el mes debe estar entre 1 y 12.")
            mm = _number(row["normal_mm"], "normal_mm", line)
            if mm < 0:
                raise InvalidFileError(f"Línea {line}: la normal no puede ser negativa.")
            if int(month) in values:
                raise InvalidFileError(f"Línea {line}: el mes {int(month)} está repetido.")
            values[int(month)] = mm

        try:
            source_id = self._repository.ensure_source(NORMALS_SOURCE)
            station_id = self._repository.upsert_station(source_id, station)
            self._repository.replace_normals(station_id, sorted(values.items()), period, note)
            self._repository.commit()
        except Exception:
            self._repository.rollback()
            raise
        return NormalsImport(station.code, len(values), period)

    def for_station(self, station_id: int) -> StationNormals:
        station = self._repository.get_station(station_id)
        if station is None:
            raise ApiError(404, "station_not_found", "No existe la estación pedida.")
        return StationNormals(station, self._repository.normals(station_id))
