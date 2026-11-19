from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_gap_estimation_service
from app.errors import ApiError
from app.schemas.gap_estimates import GapEstimateList, GapEstimateOut
from app.schemas.ids import StationIdQuery
from app.services.gap_estimation import GapEstimationService

router = APIRouter(prefix="/api/estimates", tags=["estimaciones (no medidas)"])

Service = Annotated[GapEstimationService, Depends(get_gap_estimation_service)]


@router.get(
    "",
    response_model=GapEstimateList,
    summary="Estimaciones de días sin dato (siempre estimado, nunca medido)",
)
def list_estimates(
    service: Service,
    station_id: StationIdQuery | None = None,
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> GapEstimateList:
    if date_from and date_to and date_from > date_to:
        raise ApiError(422, "invalid_range", "«Desde» no puede ser posterior a «Hasta».")
    items, total = service.search(station_id, date_from, date_to, limit, offset)
    return GapEstimateList(
        items=[GapEstimateOut.model_validate(i) for i in items],
        total=total,
        limit=limit,
        offset=offset,
    )
