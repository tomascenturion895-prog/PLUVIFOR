from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.alerts import MessageKind, SubscriptionStatus
from app.models._types import text_enum


class AlertSubscription(Base):
    """Quien pidió avisos. Del teléfono solo se guarda un resumen y los últimos dígitos.

    Guardar el número completo para enviar de verdad queda pendiente: hace falta cifrarlo y
    decidir quién lo custodia (ver docs/decisiones/temas/avisos-a-la-poblacion.md).
    """

    __tablename__ = "alert_subscriptions"
    __table_args__ = (CheckConstraint("attempts >= 0", name="attempts_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    phone_hash: Mapped[str] = mapped_column(String(64), unique=True)
    phone_last4: Mapped[str] = mapped_column(String(4))
    station_id: Mapped[int | None] = mapped_column(ForeignKey("stations.id"))
    status: Mapped[SubscriptionStatus] = mapped_column(
        text_enum(SubscriptionStatus, "alert_subscription_status"),
        default=SubscriptionStatus.PENDIENTE,
    )
    code_hash: Mapped[str | None] = mapped_column(String(64))
    code_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AlertOutbox(Base):
    """Mensajes que se enviarían. Canal simulado: no sale nada a nadie, y se rotula así."""

    __tablename__ = "alert_outbox"
    __table_args__ = (
        CheckConstraint("category = 'simulado'", name="always_simulated"),
        Index("ix_alert_outbox_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("alert_subscriptions.id"))
    kind: Mapped[MessageKind] = mapped_column(text_enum(MessageKind, "alert_message_kind"))
    body: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(16), default="simulado")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
