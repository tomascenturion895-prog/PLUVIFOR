from sqlalchemy import delete, exists, func, or_, select
from sqlalchemy.orm import Session

from app.domain.alerts import Channel, SubscriptionStatus
from app.models import (
    AlertDispatch,
    AlertOutbox,
    AlertSubscription,
    AlertSubscriptionStation,
    Station,
)


class SqlAlertRepository:
    def __init__(self, session: Session):
        self._session = session

    # --- estaciones ------------------------------------------------------------------------

    def stations_by_ids(self, station_ids: list[int]) -> list[Station]:
        if not station_ids:
            return []
        return list(
            self._session.scalars(
                select(Station).where(Station.id.in_(station_ids)).order_by(Station.id)
            )
        )

    def stations_of(self, subscription_id: int) -> list[Station]:
        return list(
            self._session.scalars(
                select(Station)
                .join(AlertSubscriptionStation, AlertSubscriptionStation.station_id == Station.id)
                .where(AlertSubscriptionStation.subscription_id == subscription_id)
                .order_by(Station.id)
            )
        )

    def set_stations(self, subscription_id: int, station_ids: list[int]) -> None:
        """Reemplaza las estaciones de interés. Sin ninguna, la suscripción es a todas."""
        self._session.execute(
            delete(AlertSubscriptionStation).where(
                AlertSubscriptionStation.subscription_id == subscription_id
            )
        )
        for station_id in station_ids:
            self._session.add(
                AlertSubscriptionStation(subscription_id=subscription_id, station_id=station_id)
            )

    # --- suscripciones ---------------------------------------------------------------------

    def find(self, phone_hash: str) -> AlertSubscription | None:
        return self._session.scalar(
            select(AlertSubscription).where(AlertSubscription.phone_hash == phone_hash)
        )

    def get(self, subscription_id: int) -> AlertSubscription | None:
        return self._session.get(AlertSubscription, subscription_id)

    def of_user(self, user_id: int) -> list[AlertSubscription]:
        return list(
            self._session.scalars(
                select(AlertSubscription)
                .where(AlertSubscription.user_id == user_id)
                .order_by(AlertSubscription.id)
            )
        )

    def add(self, subscription: AlertSubscription) -> AlertSubscription:
        self._session.add(subscription)
        return subscription

    def confirmed_for(self, station_id: int) -> list[AlertSubscription]:
        """Confirmadas que pidieron esa estación o que no eligieron ninguna (= todas)."""
        pidio_alguna = exists().where(
            AlertSubscriptionStation.subscription_id == AlertSubscription.id
        )
        pidio_esta = exists().where(
            AlertSubscriptionStation.subscription_id == AlertSubscription.id,
            AlertSubscriptionStation.station_id == station_id,
        )
        return list(
            self._session.scalars(
                select(AlertSubscription)
                .where(
                    AlertSubscription.status == SubscriptionStatus.CONFIRMADA,
                    or_(~pidio_alguna, pidio_esta),
                )
                .order_by(AlertSubscription.id)
            )
        )

    # --- mensajes e historial --------------------------------------------------------------

    def add_message(self, message: AlertOutbox) -> None:
        self._session.add(message)

    def add_dispatch(self, dispatch: AlertDispatch) -> AlertDispatch:
        self._session.add(dispatch)
        self._session.flush()
        return dispatch

    def messages_for(self, subscription_id: int, limit: int = 100) -> list[AlertOutbox]:
        return list(
            self._session.scalars(
                select(AlertOutbox)
                .where(AlertOutbox.subscription_id == subscription_id)
                .order_by(AlertOutbox.id)
                .limit(limit)
            )
        )

    def notifications_of_user(self, user_id: int, limit: int) -> list[AlertOutbox]:
        """Las notificaciones dentro del sistema de las suscripciones de una cuenta."""
        return list(
            self._session.scalars(
                select(AlertOutbox)
                .join(AlertSubscription, AlertSubscription.id == AlertOutbox.subscription_id)
                .where(AlertSubscription.user_id == user_id, AlertOutbox.channel == Channel.SISTEMA)
                .order_by(AlertOutbox.id.desc())
                .limit(limit)
            )
        )

    def outbox(self, limit: int, offset: int) -> tuple[list[AlertOutbox], int]:
        total = self._session.scalar(select(func.count()).select_from(AlertOutbox)) or 0
        rows = self._session.scalars(
            select(AlertOutbox).order_by(AlertOutbox.id.desc()).limit(limit).offset(offset)
        ).all()
        return list(rows), total

    def dispatches(self, limit: int, offset: int) -> tuple[list[tuple[AlertDispatch, str]], int]:
        total = self._session.scalar(select(func.count()).select_from(AlertDispatch)) or 0
        rows = self._session.execute(
            select(AlertDispatch, Station.name)
            .join(Station, Station.id == AlertDispatch.station_id)
            .order_by(AlertDispatch.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        return [(d, name) for d, name in rows], total

    # --- transacción -----------------------------------------------------------------------

    def flush(self) -> None:
        self._session.flush()

    def commit(self) -> None:
        self._session.commit()
