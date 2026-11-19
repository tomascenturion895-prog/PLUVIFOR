from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_network_health_service
from app.domain.network_health import MAX_SILENT_AFTER_DAYS, SILENT_AFTER_DAYS
from app.schemas.network_health import NetworkHealthOut
from app.services.network_health import NetworkHealthService

router = APIRouter(prefix="/api/network", tags=["red"])


@router.get(
    "/health",
    response_model=NetworkHealthOut,
    summary="Salud de la red: estaciones activas, en silencio y sin datos",
)
def network_health(
    service: Annotated[NetworkHealthService, Depends(get_network_health_service)],
    silent_after_days: Annotated[
        int,
        Query(
            ge=1,
            le=MAX_SILENT_AFTER_DAYS,
            description="Días sin lectura (antes del corte) para marcar una estación en silencio",
        ),
    ] = SILENT_AFTER_DAYS,
) -> NetworkHealthOut:
    return service.report(silent_after_days)
