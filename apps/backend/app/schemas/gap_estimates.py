import json
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.enums import DataCategory, RainState

AVISO_ESTIMADO = (
    "Valores estimados, no medidos: cubren días SIN DATO y nunca se suman ni se promedian con lo "
    "observado. Método propuesto y sin validar como reemplazo de una medición."
)


class GapEstimateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    station_id: int
    obs_date: date
    mm: float
    category: DataCategory
    gap_state: RainState  # cómo era el día original: sin_fila o fila_sin_valor
    method: str
    detail: dict[str, Any]
    created_at: datetime

    @field_validator("detail", mode="before")
    @classmethod
    def _desde_json(cls, value: object) -> object:
        return json.loads(value) if isinstance(value, str) else value


class GapEstimateList(BaseModel):
    category: DataCategory = DataCategory.ESTIMADO
    notice: str = AVISO_ESTIMADO
    items: list[GapEstimateOut]
    total: int
    limit: int
    offset: int
