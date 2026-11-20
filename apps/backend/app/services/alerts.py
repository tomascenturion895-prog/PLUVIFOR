"""Suscripción a avisos y envío por canales **simulados** (nada sale a nadie).

Reglas (ver docs/decisiones/temas/avisos-a-la-poblacion.md): solo un día observado con dato
que pasa el umbral genera un aviso; un hueco no avisa; el teléfono y el correo se guardan
resumidos o enmascarados; quien no confirma el código no recibe nada; la baja se respeta siempre.

Cada aviso se «entrega» por tres canales simulados: WhatsApp, correo (si dejó uno) y una
notificación dentro del propio sistema. Un canal real sería otro adaptador en `_emit`.
"""

import hmac
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta

from app.domain.alerts import (
    CODE_TTL_MINUTES,
    MAX_CODE_ATTEMPTS,
    Channel,
    MessageKind,
    SubscriptionStatus,
    alert_message,
    code_message,
    digest,
    email_alert,
    email_registration,
    level_for,
    mask_email,
    new_code,
    welcome_message,
)
from app.domain.enums import DataCategory, RainState
from app.errors import ApiError
from app.models import AlertDispatch, AlertOutbox, AlertSubscription, Station, User
from app.repositories.alerts import SqlAlertRepository
from app.schemas.alerts import (
    AlertPreviewOut,
    AlertSendOut,
    DispatchList,
    DispatchOut,
    InboxOut,
    MySubscriptionList,
    MySubscriptionOut,
    OutboxMessageOut,
    StationRefOut,
    SubscriptionStatusOut,
)
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
        demo: bool = False,
    ):
        self._repository = repository
        self._series = series
        self._secret = secret
        self._cutoff = cutoff
        self._now = now
        self._demo = demo

    def _key(self) -> str:
        if not self._secret:
            raise ApiError(
                403, "forbidden", "Los avisos están deshabilitados: falta configurar ALERTS_SECRET."
            )
        return self._secret

    def _emit(
        self,
        subscription: AlertSubscription,
        kind: MessageKind,
        channel: Channel,
        body: str,
        subject: str | None = None,
        dispatch_id: int | None = None,
    ) -> None:
        """Deja el mensaje en la bandeja simulada. Un canal real reemplazaría esta escritura."""
        recipient = (
            subscription.email_masked
            if channel is Channel.EMAIL
            else f"…{subscription.phone_last4}"
        )
        self._repository.add_message(
            AlertOutbox(
                subscription_id=subscription.id,
                dispatch_id=dispatch_id,
                kind=kind,
                channel=channel,
                recipient=recipient,
                subject=subject,
                body=body,
            )
        )

    def _stations(self, station_ids: list[int]) -> list[Station]:
        ids = sorted(set(station_ids))
        stations = self._repository.stations_by_ids(ids)
        if len(stations) != len(ids):
            raise ApiError(404, "station_not_found", "No existe alguna de las estaciones pedidas.")
        return stations

    def subscribe(
        self,
        phone: str,
        station_ids: list[int],
        email: str | None = None,
        user_id: int | None = None,
    ) -> SubscriptionStatusOut:
        key = self._key()
        stations = self._stations(station_ids)
        if not stations:
            station_name = None
        elif len(stations) == 1:
            station_name = stations[0].name
        else:
            station_name = f"{len(stations)} estaciones"
        subscription = self._repository.find(digest(phone, key))
        if subscription is not None and subscription.status == SubscriptionStatus.CONFIRMADA:
            # No se revela si el número ya estaba suscripto: la respuesta es la misma.
            return SubscriptionStatusOut(status=SubscriptionStatus.PENDIENTE)
        if subscription is None:
            subscription = self._repository.add(
                AlertSubscription(phone_hash=digest(phone, key), phone_last4=phone[-4:])
            )
        code = new_code()
        subscription.user_id = user_id
        subscription.email_masked = mask_email(email) if email else None
        subscription.status = SubscriptionStatus.PENDIENTE
        subscription.code_hash = digest(code, key)
        subscription.code_expires_at = self._now() + timedelta(minutes=CODE_TTL_MINUTES)
        subscription.attempts = 0
        self._repository.flush()
        self._repository.set_stations(subscription.id, [s.id for s in stations])
        self._emit(subscription, MessageKind.CODIGO, Channel.WHATSAPP, code_message(code))
        if email:
            subject, body = email_registration(station_name)
            self._emit(subscription, MessageKind.BIENVENIDA, Channel.EMAIL, body, subject)
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
        text = welcome_message()
        self._emit(subscription, MessageKind.BIENVENIDA, Channel.WHATSAPP, text)
        self._emit(subscription, MessageKind.BIENVENIDA, Channel.SISTEMA, text)
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

    def inbox(self, phone: str) -> InboxOut:
        """Lo que la persona vería en su celular y su correo. Solo con ALERTS_DEMO activado."""
        if not self._demo:
            raise ApiError(
                403,
                "forbidden",
                "La vista de demostración está apagada (ALERTS_DEMO). Con canales reales, "
                "nadie puede leer los mensajes de otra persona.",
            )
        subscription = self._repository.find(digest(phone, self._key()))
        if subscription is None:
            return InboxOut(status=SubscriptionStatus.BAJA, items=[])
        items = [
            OutboxMessageOut.model_validate(m)
            for m in self._repository.messages_for(subscription.id)
        ]
        return InboxOut(status=subscription.status, items=items)

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

    def send(
        self, station_id: int, day: date, created_by_user_id: int | None = None
    ) -> AlertSendOut:
        """Entrega el aviso (simulado) a cada suscripción confirmada, por todos sus canales.

        Deja un renglón en el historial (`alert_dispatches`): quién lo mandó y a cuántas personas.
        """
        preview = self.preview(station_id, day)
        queued = 0
        if preview.would_send and preview.message is not None and preview.mm is not None:
            message = preview.message
            recipients = self._repository.confirmed_for(station_id)
            dispatch = self._repository.add_dispatch(
                AlertDispatch(
                    station_id=station_id,
                    obs_date=day,
                    mm=preview.mm,
                    level=preview.level or 0,
                    queued=len(recipients),
                    created_by_user_id=created_by_user_id,
                )
            )
            for sub_ in recipients:
                self._emit(sub_, MessageKind.AVISO, Channel.WHATSAPP, message, None, dispatch.id)
                if sub_.email_masked:
                    subject, body = email_alert(message)
                    self._emit(sub_, MessageKind.AVISO, Channel.EMAIL, body, subject, dispatch.id)
                self._emit(sub_, MessageKind.AVISO, Channel.SISTEMA, message, None, dispatch.id)
                queued += 1
            self._repository.commit()
        return AlertSendOut(preview=preview, queued=queued)

    def dispatches(self, limit: int, offset: int) -> DispatchList:
        rows, total = self._repository.dispatches(limit, offset)
        items = [
            DispatchOut(
                id=d.id,
                station_id=d.station_id,
                station_name=name,
                obs_date=d.obs_date,
                mm=d.mm,
                level=d.level,
                queued=d.queued,
                created_by_user_id=d.created_by_user_id,
                created_at=d.created_at,
            )
            for d, name in rows
        ]
        return DispatchList(items=items, total=total)

    # --- «mis avisos»: una persona con cuenta gestiona sus propias suscripciones -----------

    def _mine(self, user: User, subscription_id: int) -> AlertSubscription:
        subscription = self._repository.get(subscription_id)
        if subscription is None or subscription.user_id != user.id:
            # Ajena e inexistente responden igual: no se revela qué suscripciones existen.
            raise ApiError(404, "subscription_not_found", "No existe esa suscripción.")
        return subscription

    def _mine_out(self, subscription: AlertSubscription) -> MySubscriptionOut:
        stations = self._repository.stations_of(subscription.id)
        return MySubscriptionOut(
            id=subscription.id,
            status=subscription.status,
            phone_last4=subscription.phone_last4,
            email_masked=subscription.email_masked,
            stations=[StationRefOut(id=s.id, code=s.code, name=s.name) for s in stations],
            created_at=subscription.created_at,
            confirmed_at=subscription.confirmed_at,
        )

    def list_mine(self, user: User) -> MySubscriptionList:
        items = [self._mine_out(s) for s in self._repository.of_user(user.id)]
        return MySubscriptionList(items=items, total=len(items))

    def set_mine_stations(
        self, user: User, subscription_id: int, station_ids: list[int]
    ) -> MySubscriptionOut:
        subscription = self._mine(user, subscription_id)
        self._repository.set_stations(subscription.id, [s.id for s in self._stations(station_ids)])
        self._repository.commit()
        return self._mine_out(subscription)

    def unsubscribe_mine(self, user: User, subscription_id: int) -> MySubscriptionOut:
        """Quien tiene la cuenta se da de baja sin teléfono: no hace falta adivinar nada."""
        subscription = self._mine(user, subscription_id)
        subscription.status = SubscriptionStatus.BAJA
        subscription.code_hash = None
        subscription.code_expires_at = None
        self._repository.commit()
        return self._mine_out(subscription)

    def notifications_mine(self, user: User, limit: int) -> list[AlertOutbox]:
        """Las notificaciones dentro del sistema de la cuenta (el canal que sí sería real)."""
        return self._repository.notifications_of_user(user.id, limit)

    def outbox(self, limit: int, offset: int) -> tuple[list[AlertOutbox], int]:
        return self._repository.outbox(limit, offset)
