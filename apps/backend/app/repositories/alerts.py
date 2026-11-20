from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.domain.alerts import SubscriptionStatus
from app.models import AlertOutbox, AlertSubscription, Station


class SqlAlertRepository:
    def __init__(self, session: Session):
        self._session = session

    def station(self, station_id: int) -> Station | None:
        return self._session.get(Station, station_id)

    def find(self, phone_hash: str) -> AlertSubscription | None:
        return self._session.scalar(
            select(AlertSubscription).where(AlertSubscription.phone_hash == phone_hash)
        )

    def add(self, subscription: AlertSubscription) -> AlertSubscription:
        self._session.add(subscription)
        return subscription

    def add_message(self, message: AlertOutbox) -> None:
        self._session.add(message)

    def flush(self) -> None:
        self._session.flush()

    def commit(self) -> None:
        self._session.commit()

    def confirmed_for(self, station_id: int) -> list[AlertSubscription]:
        """Confirmadas que pidieron esa estación o que no eligieron ninguna."""
        return list(
            self._session.scalars(
                select(AlertSubscription)
                .where(
                    AlertSubscription.status == SubscriptionStatus.CONFIRMADA,
                    or_(
                        AlertSubscription.station_id == station_id,
                        AlertSubscription.station_id.is_(None),
                    ),
                )
                .order_by(AlertSubscription.id)
            )
        )

    def messages_for(self, subscription_id: int, limit: int = 100) -> list[AlertOutbox]:
        return list(
            self._session.scalars(
                select(AlertOutbox)
                .where(AlertOutbox.subscription_id == subscription_id)
                .order_by(AlertOutbox.id)
                .limit(limit)
            )
        )

    def outbox(self, limit: int, offset: int) -> tuple[list[AlertOutbox], int]:
        total = self._session.scalar(select(func.count()).select_from(AlertOutbox)) or 0
        rows = self._session.scalars(
            select(AlertOutbox).order_by(AlertOutbox.id.desc()).limit(limit).offset(offset)
        ).all()
        return list(rows), total
