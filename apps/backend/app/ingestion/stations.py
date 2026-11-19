"""Lector y validación del catálogo de estaciones del SIGA."""

import csv
import io
from datetime import date

from app.ingestion.types import InvalidFileError, Rejection, RejectionReason, StationRow

REQUIRED_COLUMNS = {"estacion_id", "nombre", "lat", "lon"}


def _optional_float(text: str) -> float | None:
    text = (text or "").strip()
    return float(text) if text else None


def _optional_date(text: str) -> date | None:
    text = (text or "").strip()
    return date.fromisoformat(text) if text else None


def read_stations(text: str) -> tuple[list[StationRow], list[Rejection]]:
    reader = csv.DictReader(io.StringIO(text))
    missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
    if missing:
        raise InvalidFileError(f"Faltan columnas: {', '.join(sorted(missing))}")

    rows: list[StationRow] = []
    rejections: list[Rejection] = []
    for line, row in enumerate(reader, start=2):
        code = (row["estacion_id"] or "").strip()
        if not code or not (row["nombre"] or "").strip():
            rejections.append(Rejection(line, RejectionReason.CODIGO_VACIO))
            continue
        try:
            lat = _optional_float(row["lat"])
            lon = _optional_float(row["lon"])
            elevation = _optional_float(row.get("altura_m", ""))
            active_from = _optional_date(row.get("desde_siga", ""))
            active_to = _optional_date(row.get("hasta_siga", ""))
        except ValueError:
            rejections.append(Rejection(line, RejectionReason.COORDENADAS_INVALIDAS))
            continue
        # Coordenadas incompletas o fuera de rango: no se adivinan, se rechaza la fila.
        if (lat is None) != (lon is None) or (
            lat is not None and lon is not None and not (-90 <= lat <= 90 and -180 <= lon <= 180)
        ):
            rejections.append(Rejection(line, RejectionReason.COORDENADAS_INVALIDAS))
            continue
        rows.append(
            StationRow(
                code=code,
                internal_code=(row.get("id_interno") or "").strip() or None,
                name=row["nombre"].strip(),
                kind=(row.get("tipo") or "").strip() or None,
                locality=(row.get("localidad") or "").strip() or None,
                lat=lat,
                lon=lon,
                elevation_m=elevation,
                active_from=active_from,
                active_to=active_to,
            )
        )
    return rows, rejections
