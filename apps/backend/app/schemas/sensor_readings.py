import re
from datetime import UTC, datetime
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.enums import SensorCategory

# Tope descriptivo para frenar un error de tipeo (un cero de más), no una regla meteorológica.
MAX_MM = 1000.0
_DISPOSITIVO = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")

AVISO_SIMULADAS = (
    "Lecturas simuladas: no son datos de sensores reales ni se suman a las series de lluvia."
)


class SensorReadingIn(BaseModel):
    """Lo que envía un dispositivo. No trae categoría: la API siempre la fija como simulado."""

    model_config = ConfigDict(extra="forbid")

    device_id: str
    read_at: AwareDatetime
    mm: Annotated[float, Field(ge=0, le=MAX_MM, allow_inf_nan=False)]
    lat: Annotated[float | None, Field(ge=-90, le=90, allow_inf_nan=False)] = None
    lon: Annotated[float | None, Field(ge=-180, le=180, allow_inf_nan=False)] = None

    @field_validator("device_id")
    @classmethod
    def _dispositivo_valido(cls, value: str) -> str:
        if not _DISPOSITIVO.match(value):
            raise ValueError(
                "El dispositivo usa letras, números, punto, guion y guion bajo (hasta 64)."
            )
        return value

    @model_validator(mode="after")
    def _ubicacion_completa(self) -> "SensorReadingIn":
        if (self.lat is None) != (self.lon is None):
            raise ValueError("La ubicación necesita latitud y longitud juntas.")
        return self


class SensorReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: str
    read_at: datetime
    mm: float
    lat: float | None
    lon: float | None
    category: SensorCategory
    source: str
    created_at: datetime

    @field_validator("read_at", "created_at")
    @classmethod
    def _en_utc(cls, value: datetime) -> datetime:
        """SQLite devuelve fechas sin zona: se guardan siempre en UTC, así que se la devolvemos."""
        return value.replace(tzinfo=UTC) if value.tzinfo is None else value


class SensorReadingList(BaseModel):
    items: list[SensorReadingOut]
    total: int
    notice: str = AVISO_SIMULADAS
