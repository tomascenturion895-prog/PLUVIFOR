from datetime import date

from pydantic import BaseModel, ConfigDict

from app.domain.enums import DataCategory, RainState, Severity
from app.schemas.stations import SourceOut


class DayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    obs_date: date
    state: RainState
    mm: float | None  # None = sin dato; nunca 0


class SummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    days_in_period: int
    days_with_data: int
    days_sin_fila: int
    days_fila_sin_valor: int
    coverage: float
    accumulated_mm: float | None


class WarningOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    message: str
    severity: Severity
    start_date: date | None
    end_date: date | None


class SeriesOut(BaseModel):
    station_id: int
    station_name: str
    source: SourceOut
    category: DataCategory
    date_from: date
    date_to: date
    data_cutoff_date: date
    clipped_to_cutoff: bool
    summary: SummaryOut
    warnings: list[WarningOut]
    days: list[DayOut]
    notice: str = "PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial"
