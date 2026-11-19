import re
from datetime import date, datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.enums import DataCategory, LocationSource, ReportLocation, Validation

# Tope descriptivo para frenar un error de tipeo (un cero de más), no una regla meteorológica.
MAX_MM = 1000.0
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


def _limpio(valor: str) -> str:
    valor = valor.strip()
    if _CONTROL.search(valor):
        raise ValueError("No puede tener caracteres de control.")
    if not valor:
        raise ValueError("No puede estar vacío.")
    return valor


Texto = Annotated[str, Field(max_length=200)]


class FieldReportIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    obs_date: date
    mm: Annotated[float, Field(ge=0, le=MAX_MM, allow_inf_nan=False)]
    place: Texto
    reporter: Annotated[str, Field(max_length=120)]
    lat: Annotated[float | None, Field(ge=-90, le=90, allow_inf_nan=False)] = None
    lon: Annotated[float | None, Field(ge=-180, le=180, allow_inf_nan=False)] = None
    location_source: LocationSource | None = None

    _texto = field_validator("place", "reporter")(_limpio)

    @model_validator(mode="after")
    def _ubicacion_completa(self) -> Self:
        if (self.lat is None) != (self.lon is None):
            raise ValueError("La ubicación necesita latitud y longitud juntas.")
        if self.lat is None and self.location_source is not None:
            raise ValueError("No se puede indicar el origen de una ubicación que no se informó.")
        return self


class FieldReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    obs_date: date
    mm: float
    place: str
    reporter: str
    lat: float | None
    lon: float | None
    location_status: ReportLocation
    location_source: LocationSource | None
    category: DataCategory
    validation: Validation
    source: str
    created_at: datetime


class FieldReportList(BaseModel):
    items: list[FieldReportOut]
    total: int
