from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.alerts import Channel, MessageKind, SubscriptionStatus
from app.models._types import text_enum


class AlertSubscription(Base):
    """Quien pidió avisos. Del teléfono solo se guarda un resumen y los últimos dígitos.

    Guardar el número completo para enviar de verdad queda pendiente: hace falta cifrarlo y
    decidir quién lo custodia (ver docs/decisiones/temas/avisos-a-la-poblacion.md).
    Las estaciones de interés están en `alert_subscription_stations`; sin ninguna = todas.
    """

    __tablename__ = "alert_subscriptions"
    __table_args__ = (
        CheckConstraint("attempts >= 0", name="attempts_non_negative"),
        Index("ix_alert_subscriptions_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # La cuenta dueña, si se suscribió con sesión iniciada. Si se borra la cuenta se borra la
    # suscripción (y sus mensajes): son datos personales.
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    phone_hash: Mapped[str] = mapped_column(String(64), unique=True)
    phone_last4: Mapped[str] = mapped_column(String(4))
    # Solo el correo enmascarado (t****@dominio); el completo queda pendiente, como el teléfono.
    email_masked: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[SubscriptionStatus] = mapped_column(
        text_enum(SubscriptionStatus, "alert_subscription_status"),
        default=SubscriptionStatus.PENDIENTE,
    )
    code_hash: Mapped[str | None] = mapped_column(String(64))
    code_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AlertSubscriptionStation(Base):
    """Una estación de interés de una suscripción (una suscripción puede tener varias)."""

    __tablename__ = "alert_subscription_stations"
    __table_args__ = (
        PrimaryKeyConstraint("subscription_id", "station_id"),
        Index("ix_alert_subscription_stations_station_id", "station_id"),
    )

    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("alert_subscriptions.id", ondelete="CASCADE")
    )
    # Una estación con suscripciones no se puede borrar (no se borra en cascada).
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"))


class AlertDispatch(Base):
    """Un aviso que el personal mandó: de qué estación y día, cuánto llovió y a cuántas personas.

    Es el historial de avisos. Guarda el valor tal como estaba al enviarlo.
    """

    __tablename__ = "alert_dispatches"
    __table_args__ = (
        CheckConstraint("mm >= 0", name="mm_non_negative"),
        CheckConstraint("queued >= 0", name="queued_non_negative"),
        Index("ix_alert_dispatches_station_id", "station_id"),
        Index("ix_alert_dispatches_created_at", "created_at"),
        Index("ix_alert_dispatches_created_by_user_id", "created_by_user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"))
    obs_date: Mapped[date] = mapped_column(Date)
    mm: Mapped[float] = mapped_column(Float)
    level: Mapped[int] = mapped_column(Integer)
    queued: Mapped[int] = mapped_column(Integer)
    # Quién lo mandó; nulo si fue la clave de administración. Si se borra la cuenta queda nulo.
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AlertOutbox(Base):
    """Mensajes que se enviarían. Canal simulado: no sale nada a nadie, y se rotula así."""

    __tablename__ = "alert_outbox"
    __table_args__ = (
        CheckConstraint("category = 'simulado'", name="always_simulated"),
        Index("ix_alert_outbox_created_at", "created_at"),
        Index("ix_alert_outbox_subscription_id", "subscription_id"),
        Index("ix_alert_outbox_dispatch_id", "dispatch_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Si se borra una suscripción (derecho a que borren los datos de uno), se borran sus mensajes.
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("alert_subscriptions.id", ondelete="CASCADE")
    )
    # A qué aviso del historial pertenece (nulo en los códigos y las bienvenidas).
    dispatch_id: Mapped[int | None] = mapped_column(
        ForeignKey("alert_dispatches.id", ondelete="SET NULL")
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
