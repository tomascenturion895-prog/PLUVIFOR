from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.alerts import Channel, MessageKind, SubscriptionStatus
from app.models._types import text_enum


class AlertSubscription(Base):
    """Quien pidió avisos. Del teléfono solo se guarda un resumen y los últimos dígitos.

    Guardar el número completo para enviar de verdad queda pendiente: hace falta cifrarlo y
    decidir quién lo custodia (ver docs/decisiones/temas/avisos-a-la-poblacion.md).
    """

    __tablename__ = "alert_subscriptions"
    __table_args__ = (
        CheckConstraint("attempts >= 0", name="attempts_non_negative"),
        Index("ix_alert_subscriptions_station_id", "station_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    phone_hash: Mapped[str] = mapped_column(String(64), unique=True)
    phone_last4: Mapped[str] = mapped_column(String(4))
    # Solo el correo enmascarado (t****@dominio); el completo queda pendiente, como el teléfono.
    email_masked: Mapped[str | None] = mapped_column(String(120))
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
        Index("ix_alert_outbox_subscription_id", "subscription_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Si se borra una suscripción (derecho a que borren los datos de uno), se borran sus mensajes.
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("alert_subscriptions.id", ondelete="CASCADE")
    )
    kind: Mapped[MessageKind] = mapped_column(text_enum(MessageKind, "alert_message_kind"))
    channel: Mapped[Channel] = mapped_column(
        text_enum(Channel, "alert_message_channel"), default=Channel.WHATSAPP
    )
    # A quién iría: «+54 …3456» o «t****@dominio». Nunca el dato completo.
    recipient: Mapped[str | None] = mapped_column(String(120))
    subject: Mapped[str | None] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(16), default="simulado")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
