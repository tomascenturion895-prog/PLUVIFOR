from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.deps import Actor, current_user, get_alert_service, require_admin, require_user
from app.models import User
from app.schemas.alerts import (
    AlertPreviewOut,
    AlertSendOut,
    ConfirmIn,
    DispatchList,
    InboxIn,
    InboxOut,
    MySubscriptionList,
    MySubscriptionOut,
    NotificationList,
    OutboxList,
    OutboxMessageOut,
    StationsIn,
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
SubscriptionId = Annotated[int, Path(ge=1, le=MAX_ID)]


@router.post(
    "/subscriptions",
    response_model=SubscriptionStatusOut,
    status_code=202,
    summary="Pedir avisos: se manda un código de confirmación (canal simulado)",
)
def subscribe(
    data: SubscribeIn,
    service: Service,
    user: Annotated[User | None, Depends(current_user)],
) -> SubscriptionStatusOut:
    """Con sesión iniciada, la suscripción queda a nombre de esa cuenta."""
    return service.subscribe(data.phone, data.station_ids, data.email, user.id if user else None)


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
def send(
    station_id: StationId,
    day: Day,
    service: Service,
    actor: Annotated[Actor, Depends(require_admin)],
) -> AlertSendOut:
    return service.send(station_id, day, actor.user_id)


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


@router.get(
    "/dispatches",
    response_model=DispatchList,
    dependencies=[Depends(require_admin)],
    summary="Historial de avisos mandados (solo personal)",
)
def dispatches(
    service: Service,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DispatchList:
    return service.dispatches(limit, offset)


@router.get(
    "/mine",
    response_model=MySubscriptionList,
    summary="Mis suscripciones (requiere sesión)",
)
def my_subscriptions(
    service: Service, user: Annotated[User, Depends(require_user)]
) -> MySubscriptionList:
    return service.list_mine(user)


@router.get(
    "/mine/notifications",
    response_model=NotificationList,
    summary="Mis notificaciones dentro del sistema (requiere sesión)",
)
def my_notifications(
    service: Service,
    user: Annotated[User, Depends(require_user)],
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> NotificationList:
    items = service.notifications_mine(user, limit)
    return NotificationList(items=[OutboxMessageOut.model_validate(i) for i in items])


@router.put(
    "/mine/{subscription_id}/stations",
    response_model=MySubscriptionOut,
    summary="Cambiar las estaciones de una de mis suscripciones (vacío = todas)",
)
def set_my_stations(
    subscription_id: SubscriptionId,
    data: StationsIn,
    service: Service,
    user: Annotated[User, Depends(require_user)],
) -> MySubscriptionOut:
    return service.set_mine_stations(user, subscription_id, data.station_ids)


@router.post(
    "/mine/{subscription_id}/unsubscribe",
    response_model=MySubscriptionOut,
    summary="Darme de baja de una de mis suscripciones, sin necesidad del teléfono",
)
def unsubscribe_mine(
    subscription_id: SubscriptionId,
    service: Service,
    user: Annotated[User, Depends(require_user)],
) -> MySubscriptionOut:
    return service.unsubscribe_mine(user, subscription_id)
