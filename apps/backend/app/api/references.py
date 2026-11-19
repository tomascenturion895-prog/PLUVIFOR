from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_reference_service
from app.domain.enums import DataCategory
from app.schemas.ids import StationIdQuery
from app.services.references import ReferenceService

router = APIRouter(prefix="/api/climate-reference", tags=["referencia climática"])


class NormalMonthOut(BaseModel):
    month: int
    normal_mm: float


class NormalSetOut(BaseModel):
    period: str
    source_note: str
    months: list[NormalMonthOut]


class ClimateReferenceOut(BaseModel):
    """Referencia climática: va separada de lo observado y nunca se suma ni se promedia con él."""

    station_id: int
    station_name: str
    category: DataCategory
    normals: list[NormalSetOut]  # vacío = no hay normal cargada para esta estación (no es 0)
    notice: str = (
        "Referencia climática: no es lluvia observada y no se suma ni se promedia con ella."
    )


@router.get(
    "",
    response_model=ClimateReferenceOut,
    summary="Normal mensual de una estación (referencia, separada de lo observado)",
)
def get_reference(
    station_id: StationIdQuery,
    service: Annotated[ReferenceService, Depends(get_reference_service)],
) -> ClimateReferenceOut:
    result = service.for_station(station_id)
    by_period: dict[str, list] = {}
    for normal in result.normals:
        by_period.setdefault(normal.period, []).append(normal)
    return ClimateReferenceOut(
        station_id=result.station.id,
        station_name=result.station.name,
        category=DataCategory.REFERENCIA,
        normals=[
            NormalSetOut(
                period=period,
                source_note=items[0].source_note,
                months=[NormalMonthOut(month=n.month, normal_mm=n.normal_mm) for n in items],
            )
            for period, items in by_period.items()
        ],
    )
