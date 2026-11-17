from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_station_service
from app.domain.enums import CoordsStatus
from app.repositories.stations import Page, StationFilters
from app.schemas.stations import StationList, StationOut
from app.services.stations import StationService

router = APIRouter(prefix="/stations", tags=["estaciones"])

Service = Annotated[StationService, Depends(get_station_service)]


@router.get("", response_model=StationList, summary="Catálogo de estaciones")
def list_stations(
    service: Service,
    source: Annotated[str | None, Query(max_length=64, description="Código de la fuente")] = None,
    department: Annotated[str | None, Query(max_length=100)] = None,
    zone: Annotated[str | None, Query(max_length=100)] = None,
    coords_status: CoordsStatus | None = None,
    q: Annotated[
        str | None, Query(max_length=100, description="Texto en nombre o localidad")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> StationList:
    filters = StationFilters(
        source_code=source, department=department, zone=zone, coords_status=coords_status, text=q
    )
    items, total = service.search(filters, Page(limit=limit, offset=offset))
    return StationList(items=items, total=total, limit=limit, offset=offset)


@router.get("/{station_id}", response_model=StationOut, summary="Ficha de una estación")
def get_station(station_id: int, service: Service) -> StationOut:
    return service.get(station_id)
