from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_alert_service, require_admin
from app.schemas.alerts import (
    AlertPreviewOut,
    AlertSendOut,
    ConfirmIn,
    InboxIn,
    InboxOut,
    OutboxList,
    OutboxMessageOut,
    SubscribeIn,
    SubscriptionStatusOut,
    UnsubscribeIn,
)
from app.schemas.ids import MAX_ID
from app.services.alerts import AlertService

router = APIRouter(prefix="/api/alerts", tags=["avisos (canal simulado)"])

Service = Annotated[AlertService, Depends(get_alert_service)]
StationId = Annotated[int, Query(ge=1, le=MAX_ID)]
Day = Annotated[date, Query(alias="date")]


@router.post(
    "/subscriptions",
    response_model=SubscriptionStatusOut,
    status_code=202,
    summary="Pedir avisos: se manda un código de confirmación (canal simulado)",
)
def subscribe(data: SubscribeIn, service: Service) -> SubscriptionStatusOut:
    return service.subscribe(data.phone, data.station_id, data.email)


@router.post(
    "/subscriptions/confirm",
    response_model=SubscriptionStatusOut,
    summary="Confirmar la suscripción con el código recibido",
)
def confirm(data: ConfirmIn, service: Service) -> SubscriptionStatusOut:
    return service.confirm(data.phone, data.code)


@router.post(
    "/subscriptions/unsubscribe",
    response_model=SubscriptionStatusOut,
    summary="Darse de baja de los avisos",
)
def unsubscribe(data: UnsubscribeIn, service: Service) -> SubscriptionStatusOut:
    return service.unsubscribe(data.phone)


@router.post(
    "/inbox",
    response_model=InboxOut,
    summary="Demostración: lo que vería la persona en su celular y su correo (ALERTS_DEMO)",
)
def inbox(data: InboxIn, service: Service) -> InboxOut:
    return service.inbox(data.phone)


@router.get(
    "/preview",
    response_model=AlertPreviewOut,
    dependencies=[Depends(require_admin)],
    summary="Vista previa del aviso de una estación y un día (solo personal)",
)
def preview(station_id: StationId, day: Day, service: Service) -> AlertPreviewOut:
    return service.preview(station_id, day)


@router.post(
    "/send",
    response_model=AlertSendOut,
    dependencies=[Depends(require_admin)],
    summary="Poner el aviso en la bandeja simulada de las suscripciones confirmadas",
)
def send(station_id: StationId, day: Day, service: Service) -> AlertSendOut:
    return service.send(station_id, day)


@router.get(
    "/outbox",
    response_model=OutboxList,
    dependencies=[Depends(require_admin)],
    summary="Mensajes que se enviarían (solo personal)",
)
def outbox(
    service: Service,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> OutboxList:
    items, total = service.outbox(limit, offset)
    return OutboxList(items=[OutboxMessageOut.model_validate(i) for i in items], total=total)
