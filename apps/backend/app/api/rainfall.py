from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_series_service
from app.config import Settings, get_settings
from app.domain.enums import DataCategory
from app.schemas.series import AccumulatedOut, AccumulatedStationOut, SeriesOut, WarningOut
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


@router.get(
    "/accumulated",
    response_model=AccumulatedOut,
    summary="Acumulado por estación de una estación o de una zona (sin sumar entre estaciones)",
)
def get_accumulated(
    date_from: Annotated[date, Query(alias="from")],
    date_to: Annotated[date, Query(alias="to")],
    service: Annotated[SeriesService, Depends(get_series_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    station_id: Annotated[int | None, Query(ge=1)] = None,
    zone: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    category: DataCategory = DataCategory.OBSERVADO,
) -> AccumulatedOut:
    result = service.accumulated(date_from, date_to, category, station_id=station_id, zone=zone)
    return AccumulatedOut(
        category=result.category,
        date_from=result.date_from,
        date_to=result.date_to,
        data_cutoff_date=settings.data_cutoff_date,
        clipped_to_cutoff=result.clipped_to_cutoff,
        days_in_period=result.days_in_period,
        stations=[
            AccumulatedStationOut(
                station_id=e.station_id,
                station_name=e.station_name,
                accumulated_mm=e.accumulated_mm,
                days_with_data=e.days_with_data,
                days_without_data=e.days_without_data,
                coverage=e.coverage,
                warnings=[WarningOut.model_validate(w) for w in e.warnings],
            )
            for e in result.stations
        ],
        # Esta consulta no lee día por día: no puede saber cuántos datos están sin validar.
        not_evaluated=["dato_sin_validar"],
    )
