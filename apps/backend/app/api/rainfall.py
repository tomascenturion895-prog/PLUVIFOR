from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_series_service
from app.config import Settings, get_settings
from app.domain.enums import DataCategory
from app.schemas.series import SeriesOut
from app.services.series import SeriesService

router = APIRouter(prefix="/api/rainfall", tags=["lluvia"])


@router.get(
    "",
    response_model=SeriesOut,
    summary="Serie diaria de una estación con cobertura y advertencias",
)
def get_rainfall(
    station_id: Annotated[int, Query(ge=1)],
    date_from: Annotated[date, Query(alias="from")],
    date_to: Annotated[date, Query(alias="to")],
    service: Annotated[SeriesService, Depends(get_series_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    category: DataCategory = DataCategory.OBSERVADO,
) -> SeriesOut:
    result = service.get_series(station_id, date_from, date_to, category)
    return SeriesOut(
        station_id=result.station.id,
        station_name=result.station.name,
        source=result.station.source,
        category=result.category,
        date_from=result.date_from,
        date_to=result.date_to,
        data_cutoff_date=settings.data_cutoff_date,
        clipped_to_cutoff=result.clipped_to_cutoff,
        summary=result.summary,
        warnings=result.warnings,
        days=[
            {
                "obs_date": d.obs_date,
                "state": d.state,
                "mm": d.mm,
                "category": result.category,
                "source": result.station.source.code,
                "flags": [
                    w.code
                    for w in result.warnings
                    if w.start_date and w.end_date and w.start_date <= d.obs_date <= w.end_date
                ],
            }
            for d in result.days
        ],
    )
