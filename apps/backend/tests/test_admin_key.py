"""Las operaciones de escritura exigen la clave de administración (SCRUM-54)."""

from fastapi import APIRouter, Depends
from fastapi.testclient import TestClient

from app.api.deps import require_admin
from app.config import Settings
from app.db.base import Base
from app.main import create_app

KEY = "clave-de-prueba-larga"


def make_client(tmp_path, admin_api_key) -> TestClient:
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url=f"sqlite:///{tmp_path / 't.db'}",
        admin_api_key=admin_api_key,
    )
    app = create_app(settings)
    Base.metadata.create_all(app.state.engine)
    router = APIRouter()

    @router.post("/_escritura", dependencies=[Depends(require_admin)])
    def _escritura() -> dict:
        return {"ok": True}

    app.include_router(router)
    return TestClient(app)


def test_without_key_returns_401(tmp_path):
    client = make_client(tmp_path, KEY)
    response = client.post("/_escritura")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_wrong_key_returns_401_and_never_echoes_it(tmp_path):
    client = make_client(tmp_path, KEY)
    response = client.post("/_escritura", headers={"X-API-Key": "otra-clave"})
    assert response.status_code == 401
    assert "otra-clave" not in response.text and KEY not in response.text


def test_right_key_works(tmp_path):
    client = make_client(tmp_path, KEY)
    response = client.post("/_escritura", headers={"X-API-Key": KEY})
    assert response.status_code == 200


def test_without_configured_key_writing_is_disabled_even_with_a_header(tmp_path):
    for configured in (None, ""):
        client = make_client(tmp_path, configured)
        response = client.post("/_escritura", headers={"X-API-Key": "lo-que-sea"})
        assert response.status_code == 403
        assert "ADMIN_API_KEY" in response.json()["error"]["message"]


def test_reading_stays_public(tmp_path):
    client = make_client(tmp_path, KEY)
    assert client.get("/health").status_code == 200
