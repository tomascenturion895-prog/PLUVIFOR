"""Fábrica de motor y sesiones. La URL llega por configuración, nunca fija en el código."""

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker


def create_db_engine(database_url: str) -> Engine:
    engine = create_engine(database_url)
    if engine.dialect.name == "sqlite":
        # SQLite no aplica claves foráneas salvo que se lo pidan en cada conexión.
        @event.listens_for(engine, "connect")
        def _enable_foreign_keys(dbapi_connection, _record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False)


def get_session(request: Request) -> Iterator[Session]:
    """Dependencia de FastAPI: una sesión por solicitud, cerrada al terminar."""
    factory: sessionmaker[Session] = request.app.state.session_factory
    with factory() as session:
        yield session
