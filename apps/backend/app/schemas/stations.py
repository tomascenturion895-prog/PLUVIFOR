from datetime import date

from pydantic import BaseModel, ConfigDict

from app.domain.enums import CoordsStatus, DataCategory


class SourceOut(BaseModel):
    """Toda estación informa su fuente y la categoría de sus datos."""

    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    network: str
    category: DataCategory
    day_cutoff_local: str | None


class StationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    internal_code: str | None
    name: str
    kind: str | None
    locality: str | None
    department: str | None
    zone: str | None
    # Vacíos cuando están pendientes: nunca se inventan.
    lat: float | None
    lon: float | None
    elevation_m: float | None
    coords_status: CoordsStatus
    active_from: date | None
    active_to: date | None
    source: SourceOut


class StationList(BaseModel):
    items: list[StationOut]
    total: int
    limit: int
    offset: int
