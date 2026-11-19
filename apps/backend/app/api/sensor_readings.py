from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import get_sensor_reading_service, require_device
from app.schemas.sensor_readings import SensorReadingIn, SensorReadingList, SensorReadingOut
from app.services.sensor_readings import SensorReadingService

router = APIRouter(prefix="/api/sensor-readings", tags=["sensores (simulados)"])

Service = Annotated[SensorReadingService, Depends(get_sensor_reading_service)]


@router.post(
    "",
    response_model=SensorReadingOut,
    status_code=201,
    dependencies=[Depends(require_device)],
    summary="Un dispositivo envía una lectura (hoy entra siempre como simulada)",
    responses={200: {"description": "La lectura ya estaba cargada: no se duplica."}},
)
def ingest_reading(data: SensorReadingIn, service: Service, response: Response) -> SensorReadingOut:
    reading, created = service.ingest(data)
    if not created:
        response.status_code = 200
    return SensorReadingOut.model_validate(reading)


@router.get("", response_model=SensorReadingList, summary="Últimas lecturas de sensores")
def list_readings(
    service: Service,
    device_id: Annotated[str | None, Query(max_length=64)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SensorReadingList:
    items, total = service.latest(limit, offset, device_id)
    return SensorReadingList(items=[SensorReadingOut.model_validate(i) for i in items], total=total)
