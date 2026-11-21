from datetime import date

from pydantic import BaseModel, ConfigDict

from app.domain.enums import DataCategory
from app.schemas.series import SummaryOut, WarningOut
from app.schemas.stations import SourceOut

AVISO_PROTOTIPO = "PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial"
DESCRIPCION_EVENTOS = (
    "Cuenta descriptiva de lo que pasó, no una alerta ni una predicción. "
    "Un día sin dato no es un día seco: corta la racha seca y no la extiende."
)


class IntenseDayOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    obs_date: date
    mm: float


class DryStreakOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    start_date: date
    end_date: date
    days: int
    zero_run_warning: bool


class EventsStationOut(BaseModel):
    station_id: int
    station_name: str
    source: SourceOut
    summary: SummaryOut
    days_50mm_or_more: list[IntenseDayOut]
    days_100mm_or_more: list[IntenseDayOut]
    dry_streaks: list[DryStreakOut]
    longest_dry_streak: DryStreakOut | None
    warnings: list[WarningOut]


class EventsOut(BaseModel):
    category: DataCategory
    date_from: date
    date_to: date
    data_cutoff_date: date
    clipped_to_cutoff: bool
    min_dry_days: int
    stations: list[EventsStationOut]
    notice: str = AVISO_PROTOTIPO
    description: str = DESCRIPCION_EVENTOS
