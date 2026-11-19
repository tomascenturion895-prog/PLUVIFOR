from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.enums import DataCategory
from app.schemas.series import SummaryOut, WarningOut
from app.schemas.stations import SourceOut
from app.services.report import MAX_STATIONS


class ReportRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    station_ids: list[int] = Field(min_length=1, max_length=MAX_STATIONS)
    date_from: date = Field(alias="from")
    date_to: date = Field(alias="to")
    category: DataCategory = DataCategory.OBSERVADO

    @field_validator("station_ids")
    @classmethod
    def _positive(cls, ids: list[int]) -> list[int]:
        if any(i < 1 for i in ids):
            raise ValueError("Los identificadores de estación deben ser positivos.")
        return ids


class IntenseEventOut(BaseModel):
    obs_date: date
    mm: float
    level_mm: float


class StationReportOut(BaseModel):
    station_id: int
    station_name: str
    source: SourceOut
    category: DataCategory
    summary: SummaryOut
    intense_events: list[IntenseEventOut]
    warnings: list[WarningOut]


class NotEvaluatedOut(BaseModel):
    code: str
    reason: str


class ReportOut(BaseModel):
    category: DataCategory
    date_from: date
    date_to: date
    data_cutoff_date: date
    clipped_to_cutoff: bool
    stations: list[StationReportOut]
    comparability_warnings: list[WarningOut]
    not_evaluated: list[NotEvaluatedOut]
    text: str
    notice: str = "PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial"
