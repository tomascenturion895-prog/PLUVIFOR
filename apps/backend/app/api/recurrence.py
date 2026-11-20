from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_series_service
from app.config import Settings, get_settings
from app.schemas.ids import StationIdQuery
from app.schemas.recurrence import RecurrenceOut
from app.services.recurrence import RecurrenceService
from app.services.series import SeriesService

router = APIRouter(prefix="/api/recurrence", tags=["recurrencia (descriptiva)"])


@router.get(
    "",
    response_model=RecurrenceOut,
    summary="Cada cuánto llovió 50 y 100 mm o más en una estación (histórico, no es predicción)",
)
def recurrence(
    station_id: StationIdQuery,
    date_from: Annotated[date, Query(alias="from")],
    date_to: Annotated[date, Query(alias="to")],
    series: Annotated[SeriesService, Depends(get_series_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RecurrenceOut:
    return RecurrenceService(series, settings.data_cutoff_date).get(station_id, date_from, date_to)
