from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models import AuthSession, User


class SqlUserRepository:
    def __init__(self, session: Session):
        self._session = session

    def by_email(self, email: str) -> User | None:
        return self._session.scalar(select(User).where(User.email == email))

    def get(self, user_id: int) -> User | None:
        return self._session.get(User, user_id)

    def add(self, user: User) -> User:
        self._session.add(user)
        self._session.flush()
        return user

    def add_session(self, auth_session: AuthSession) -> AuthSession:
        self._session.add(auth_session)
        return auth_session

    def session_by_hash(self, token_hash: str) -> tuple[AuthSession, User] | None:
        row = self._session.execute(
            select(AuthSession, User)
            .join(User, User.id == AuthSession.user_id)
            .where(AuthSession.token_hash == token_hash)
        ).first()
        return (row[0], row[1]) if row else None

    def revoke_sessions(self, user_id: int, when: datetime) -> None:
        self._session.execute(
            update(AuthSession)
            .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=when)
        )

    def list_users(self, limit: int, offset: int) -> tuple[list[User], int]:
        total = self._session.scalar(select(func.count()).select_from(User)) or 0
        rows = self._session.scalars(select(User).order_by(User.id).limit(limit).offset(offset))
        return list(rows), total

    def commit(self) -> None:
        self._session.commit()
