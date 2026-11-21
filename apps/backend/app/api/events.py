from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_series_service, get_station_service
from app.config import Settings, get_settings
from app.domain.enums import DataCategory
from app.domain.events import ZERO_RUN_CODE, analyze
from app.errors import ApiError
from app.repositories.stations import Page, StationFilters
from app.schemas.events import DryStreakOut, EventsOut, EventsStationOut, IntenseDayOut
from app.schemas.ids import StationIdQuery
from app.schemas.series import SummaryOut, WarningOut
from app.services.series import SeriesService
from app.services.stations import StationService

router = APIRouter(prefix="/api/events", tags=["eventos (descriptivos)"])

# Tope de estaciones analizadas en una consulta por zona (igual que la API en Go).
MAX_ZONE_STATIONS = 100
# Largo mínimo de una racha seca para listarla. Valor provisional, pendiente de confirmar:
# la racha más larga se informa siempre.
DEFAULT_MIN_DRY_DAYS = 7


@router.get(
    "",
    response_model=EventsOut,
    summary="Días de lluvia intensa (50 y 100 mm) y rachas secas, de forma descriptiva",
)
def events(
    date_from: Annotated[date, Query(alias="from")],
    date_to: Annotated[date, Query(alias="to")],
    series: Annotated[SeriesService, Depends(get_series_service)],
    stations: Annotated[StationService, Depends(get_station_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    station_id: StationIdQuery | None = None,
    zone: Annotated[str | None, Query(max_length=100)] = None,
    min_dry_days: Annotated[int, Query(ge=1, le=3660)] = DEFAULT_MIN_DRY_DAYS,
    category: DataCategory = DataCategory.OBSERVADO,
) -> EventsOut:
    if (station_id is None) == (zone is None):
        raise ApiError(422, "invalid_filter", "Hay que indicar station_id o zone, pero no los dos.")
    if station_id is not None:
        ids = [station_id]
    else:
        found, _ = stations.search(StationFilters(zone=zone), Page(limit=MAX_ZONE_STATIONS))
        ids = [s.id for s in found]
        if not ids:
            raise ApiError(404, "zone_not_found", "No hay estaciones en la zona pedida.")

    out: list[EventsStationOut] = []
    last = None
    for sid in ids:
        res = series.get_series(sid, date_from, date_to, category)
        last = res
        a = analyze(
            res.days,
            [
                (w.start_date, w.end_date)
                for w in res.warnings
                if w.code == ZERO_RUN_CODE and w.start_date and w.end_date
            ],
            min_dry_days,
        )
        out.append(
            EventsStationOut(
                station_id=res.station.id,
                station_name=res.station.name,
                source=res.station.source,
                summary=SummaryOut.model_validate(res.summary),
                days_50mm_or_more=[IntenseDayOut.model_validate(e) for e in a.ge50],
                days_100mm_or_more=[IntenseDayOut.model_validate(e) for e in a.ge100],
                dry_streaks=[DryStreakOut.model_validate(s) for s in a.dry_streaks],
                longest_dry_streak=DryStreakOut.model_validate(a.longest) if a.longest else None,
                warnings=[WarningOut.model_validate(w) for w in res.warnings],
            )
        )
    return EventsOut(
        category=category,
        date_from=date_from,
        date_to=last.date_to,
        data_cutoff_date=settings.data_cutoff_date,
        clipped_to_cutoff=date_to > settings.data_cutoff_date,
        min_dry_days=min_dry_days,
        stations=out,
    )
