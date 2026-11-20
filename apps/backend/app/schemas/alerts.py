from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.alerts import (
    Channel,
    MessageKind,
    SubscriptionStatus,
    normalize_email,
    normalize_phone,
)
from app.schemas.ids import MAX_ID

AVISO_CANAL_SIMULADO = (
    "Canal simulado: los mensajes quedan registrados como «se enviaría» y no salen a nadie."
)


class _Telefono(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str

    @field_validator("phone")
    @classmethod
    def _telefono_valido(cls, value: str) -> str:
        return normalize_phone(value)


class SubscribeIn(_Telefono):
    # Correo opcional: si lo deja, también recibe el registro y los avisos por correo (simulado).
    email: str | None = None
    # Estaciones de interés (hasta 20); sin ninguna, recibe los avisos de cualquier estación.
    station_ids: Annotated[list[Annotated[int, Field(ge=1, le=MAX_ID)]], Field(max_length=20)] = []

    @field_validator("email")
    @classmethod
    def _correo_valido(cls, value: str | None) -> str | None:
        return None if value is None or value.strip() == "" else normalize_email(value)


class ConfirmIn(_Telefono):
    code: Annotated[str, Field(pattern=r"^[0-9]{6}$")]


class UnsubscribeIn(_Telefono):
    pass


class InboxIn(_Telefono):
    pass


class SubscriptionStatusOut(BaseModel):
    status: SubscriptionStatus
    notice: str = AVISO_CANAL_SIMULADO


class AlertPreviewOut(BaseModel):
    station_id: int
    date: date
    would_send: bool
    # `enviar`, `sin_dato` (un hueco no avisa) o `bajo_umbral`.
    reason: str
    level: int | None
    mm: float | None
    message: str | None
    category: str = "observado"


class AlertSendOut(BaseModel):
    preview: AlertPreviewOut
    queued: int
    notice: str = AVISO_CANAL_SIMULADO


class OutboxMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subscription_id: int
    kind: MessageKind
    channel: Channel
    recipient: str | None
    subject: str | None
    body: str
    category: str
    created_at: datetime


class OutboxList(BaseModel):
    items: list[OutboxMessageOut]
    total: int
    notice: str = AVISO_CANAL_SIMULADO


class InboxOut(BaseModel):
    """Lo que vería la persona en su celular y su correo, si el canal fuera real. Solo en demo."""

    status: SubscriptionStatus
    items: list[OutboxMessageOut]
    notice: str = AVISO_CANAL_SIMULADO


class StationRefOut(BaseModel):
    id: int
    code: str
    name: str


class MySubscriptionOut(BaseModel):
    """Una suscripción de la cuenta. Del teléfono solo los últimos 4 dígitos."""

    id: int
    status: SubscriptionStatus
    phone_last4: str
    email_masked: str | None
    # Vacío = recibe los avisos de todas las estaciones.
    stations: list[StationRefOut]
    created_at: datetime
    confirmed_at: datetime | None


class MySubscriptionList(BaseModel):
    items: list[MySubscriptionOut]
    total: int


class StationsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    station_ids: Annotated[list[Annotated[int, Field(ge=1, le=MAX_ID)]], Field(max_length=20)] = []


class NotificationList(BaseModel):
    """Notificaciones dentro del sistema de la cuenta, más nuevas primero."""

    items: list[OutboxMessageOut]
    notice: str = AVISO_CANAL_SIMULADO


class DispatchOut(BaseModel):
    """Un aviso mandado por el personal (historial)."""

    id: int
    station_id: int
    station_name: str
    obs_date: date
    mm: float
    level: int
    queued: int
    created_by_user_id: int | None
    created_at: datetime


class DispatchList(BaseModel):
    items: list[DispatchOut]
    total: int
