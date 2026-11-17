import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings
from app.main import create_app


def test_cors_origins_se_leen_separados_por_coma():
    s = Settings(_env_file=None, cors_origins="http://a.com, http://b.com")
    assert s.cors_origins == ["http://a.com", "http://b.com"]


def test_cors_no_acepta_comodin():
    with pytest.raises(ValidationError):
        Settings(_env_file=None, cors_origins="*")


def test_cors_permite_solo_el_origen_configurado(settings):
    client = TestClient(create_app(settings))
    ok = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    otro = client.get("/health", headers={"Origin": "http://sitio-malicioso.com"})
    assert "access-control-allow-origin" not in otro.headers


def test_documentacion_apagada_en_produccion():
    prod = Settings(_env_file=None, app_env="production")
    client = TestClient(create_app(prod))
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_documentacion_disponible_en_desarrollo(settings):
    client = TestClient(create_app(settings))
    assert client.get("/docs").status_code == 200


def test_la_clave_de_administrador_no_se_imprime():
    s = Settings(_env_file=None, admin_api_key="clave-super-secreta")
    assert "clave-super-secreta" not in repr(s)
