import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.base import Base
from app.main import create_app


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        app_env="test",
        cors_origins=["http://localhost:5173"],
        # TEST_DATABASE_URL permite correr estas pruebas contra PostgreSQL (ver docs/ENTORNO.md).
        database_url=os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{tmp_path / 'test.db'}",
    )


@pytest.fixture
def app(settings: Settings):
    application = create_app(settings)
    # En PostgreSQL la base persiste entre pruebas: se parte siempre de tablas vacías.
    Base.metadata.drop_all(application.state.engine)
    Base.metadata.create_all(application.state.engine)
    yield application
    Base.metadata.drop_all(application.state.engine)
    application.state.engine.dispose()


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


@pytest.fixture
def db(app) -> Iterator[Session]:
    """Sesión para sembrar datos de prueba (se confirma antes de consultar por la API)."""
    with app.state.session_factory() as session:
        yield session
