from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.alerts import MessageKind, SubscriptionStatus, normalize_phone
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
    # Estación de interés; sin ella, recibe los avisos de cualquier estación.
    station_id: Annotated[int | None, Field(ge=1, le=MAX_ID)] = None


class ConfirmIn(_Telefono):
    code: Annotated[str, Field(pattern=r"^[0-9]{6}$")]


class UnsubscribeIn(_Telefono):
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
    body: str
    category: str
    created_at: datetime


class OutboxList(BaseModel):
    items: list[OutboxMessageOut]
    total: int
    notice: str = AVISO_CANAL_SIMULADO
