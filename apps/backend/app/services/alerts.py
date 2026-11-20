"""Suscripción a avisos y envío por un canal **simulado** (sin mandar nada a nadie).

Reglas (ver docs/decisiones/temas/avisos-a-la-poblacion.md): solo un día observado con dato
que pasa el umbral genera un aviso; un hueco no avisa; el teléfono se guarda resumido; quien no
confirma el código no recibe nada; la baja se respeta siempre.
"""

import hmac
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta

from app.domain.alerts import (
    CODE_TTL_MINUTES,
    MAX_CODE_ATTEMPTS,
    MessageKind,
    SubscriptionStatus,
    alert_message,
    code_message,
    digest,
    level_for,
    new_code,
)
from app.domain.enums import DataCategory, RainState
from app.errors import ApiError
from app.models import AlertOutbox, AlertSubscription
from app.repositories.alerts import SqlAlertRepository
from app.schemas.alerts import AlertPreviewOut, AlertSendOut, SubscriptionStatusOut
from app.services.series import SeriesService

Now = Callable[[], datetime]


class AlertService:
    def __init__(
        self,
        repository: SqlAlertRepository,
        series: SeriesService,
        secret: str | None,
        cutoff: date,
        now: Now = lambda: datetime.now(UTC),
    ):
        self._repository = repository
        self._series = series
        self._secret = secret
        self._cutoff = cutoff
        self._now = now

    def _key(self) -> str:
        if not self._secret:
            raise ApiError(
                403, "forbidden", "Los avisos están deshabilitados: falta configurar ALERTS_SECRET."
            )
        return self._secret

    def subscribe(self, phone: str, station_id: int | None) -> SubscriptionStatusOut:
        key = self._key()
        if station_id is not None and not self._repository.station_exists(station_id):
            raise ApiError(404, "station_not_found", "No existe la estación pedida.")
        subscription = self._repository.find(digest(phone, key))
        if subscription is not None and subscription.status == SubscriptionStatus.CONFIRMADA:
            # No se revela si el número ya estaba suscripto: la respuesta es la misma.
            return SubscriptionStatusOut(status=SubscriptionStatus.PENDIENTE)
        if subscription is None:
            subscription = self._repository.add(
                AlertSubscription(phone_hash=digest(phone, key), phone_last4=phone[-4:])
            )
        code = new_code()
        subscription.station_id = station_id
        subscription.status = SubscriptionStatus.PENDIENTE
        subscription.code_hash = digest(code, key)
        subscription.code_expires_at = self._now() + timedelta(minutes=CODE_TTL_MINUTES)
        subscription.attempts = 0
        self._repository.flush()
        self._repository.add_message(
            AlertOutbox(
                subscription_id=subscription.id, kind=MessageKind.CODIGO, body=code_message(code)
            )
        )
        self._repository.commit()
        return SubscriptionStatusOut(status=SubscriptionStatus.PENDIENTE)

    def confirm(self, phone: str, code: str) -> SubscriptionStatusOut:
        key = self._key()
        invalid = ApiError(422, "invalid_code", "El código es incorrecto o venció.")
        subscription = self._repository.find(digest(phone, key))
        if (
            subscription is None
            or subscription.status != SubscriptionStatus.PENDIENTE
            or subscription.code_hash is None
            or subscription.code_expires_at is None
        ):
            raise invalid
        if subscription.attempts >= MAX_CODE_ATTEMPTS:
            raise ApiError(429, "too_many_attempts", "Demasiados intentos: pedí un código nuevo.")
        expires = subscription.code_expires_at
        if expires.tzinfo is None:  # SQLite devuelve la hora sin zona; se guarda siempre en UTC
            expires = expires.replace(tzinfo=UTC)
        if expires < self._now() or not hmac.compare_digest(
            subscription.code_hash, digest(code, key)
        ):
            subscription.attempts += 1
            self._repository.commit()
            raise invalid
        subscription.status = SubscriptionStatus.CONFIRMADA
        subscription.code_hash = None
        subscription.code_expires_at = None
        subscription.confirmed_at = self._now()
        self._repository.commit()
        return SubscriptionStatusOut(status=SubscriptionStatus.CONFIRMADA)

    def unsubscribe(self, phone: str) -> SubscriptionStatusOut:
        """La baja se respeta siempre y responde igual exista o no el número."""
        subscription = self._repository.find(digest(phone, self._key()))
        if subscription is not None:
            subscription.status = SubscriptionStatus.BAJA
            subscription.code_hash = None
            subscription.code_expires_at = None
            self._repository.commit()
        return SubscriptionStatusOut(status=SubscriptionStatus.BAJA)

    def preview(self, station_id: int, day: date) -> AlertPreviewOut:
        """Qué avisaría el sistema para ese día. Solo lo observado con dato y sobre el umbral."""
        if day > self._cutoff:
            raise ApiError(
                422,
                "date_after_cutoff",
                f"La fecha no puede ser posterior al corte de datos ({self._cutoff:%d/%m/%Y}).",
            )
        result = self._series.get_series(station_id, day, day, DataCategory.OBSERVADO)
        value = result.days[0]

        def sin_aviso(reason: str, mm: float | None = None) -> AlertPreviewOut:
            return AlertPreviewOut(
                station_id=station_id,
                date=day,
                would_send=False,
                reason=reason,
                level=None,
                mm=mm,
                message=None,
            )

        # Un hueco no es 0 mm: sin dato no se avisa nada ni se afirma que no llovió.
        if value.state != RainState.DATO or value.mm is None:
            return sin_aviso("sin_dato")
        level = level_for(value.mm)
        if level is None:
            return sin_aviso("bajo_umbral", value.mm)
        validated = not any(w.code == "dato_sin_validar" for w in result.warnings)
        station = result.station
        return AlertPreviewOut(
            station_id=station_id,
            date=day,
            would_send=True,
            reason="enviar",
            level=level,
            mm=value.mm,
            message=alert_message(station.name, station.code, day, value.mm, level, validated),
        )

    def send(self, station_id: int, day: date) -> AlertSendOut:
        """Pone el aviso en la bandeja simulada de cada suscripción confirmada (no envía nada)."""
        preview = self.preview(station_id, day)
        queued = 0
        if preview.would_send and preview.message is not None:
            for subscription in self._repository.confirmed_for(station_id):
                self._repository.add_message(
                    AlertOutbox(
                        subscription_id=subscription.id,
                        kind=MessageKind.AVISO,
                        body=preview.message,
                    )
                )
                queued += 1
            self._repository.commit()
        return AlertSendOut(preview=preview, queued=queued)

    def outbox(self, limit: int, offset: int) -> tuple[list[AlertOutbox], int]:
        return self._repository.outbox(limit, offset)
