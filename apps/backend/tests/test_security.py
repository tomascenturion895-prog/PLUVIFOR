"""Seguridad de la API (SCRUM-40): CORS, encabezados, tamaño de pedidos y errores sin detalles."""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db.base import Base
from app.main import create_app

FRONT = "http://localhost:5173"
OTRO = "http://sitio-ajeno.example"


def make_client(tmp_path, **overrides) -> TestClient:
    settings = Settings(
        _env_file=None,
        app_env=overrides.pop("app_env", "test"),
        database_url=f"sqlite:///{tmp_path / 's.db'}",
        cors_origins=[FRONT],
        **overrides,
    )
    app = create_app(settings)
    Base.metadata.create_all(app.state.engine)

    @app.get("/_test/boom")
    def boom():
        raise RuntimeError("SELECT * FROM secretos /home/usuario/app.py")

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def client(tmp_path):
    return make_client(tmp_path)


class TestCors:
    def test_el_origen_del_frontend_es_aceptado(self, client):
        response = client.get("/health", headers={"Origin": FRONT})
        assert response.headers["access-control-allow-origin"] == FRONT

    def test_otro_origen_no_recibe_permiso(self, client):
        response = client.get("/health", headers={"Origin": OTRO})
        assert "access-control-allow-origin" not in response.headers

    def test_la_consulta_previa_de_otro_origen_se_rechaza(self, client):
        response = client.options(
            "/api/import/commit",
            headers={"Origin": OTRO, "Access-Control-Request-Method": "POST"},
        )
        assert response.status_code == 400
        assert "access-control-allow-origin" not in response.headers

    def test_no_se_permiten_metodos_de_escritura_ajenos(self, client):
        response = client.options(
            "/api/stations",
            headers={"Origin": FRONT, "Access-Control-Request-Method": "DELETE"},
        )
        assert response.status_code == 400


class TestEncabezados:
    def test_respuestas_normales_llevan_los_encabezados(self, client):
        h = client.get("/health").headers
        assert h["x-content-type-options"] == "nosniff"
        assert h["x-frame-options"] == "DENY"
        assert h["referrer-policy"] == "no-referrer"
        assert "frame-ancestors 'none'" in h["content-security-policy"]

    @pytest.mark.parametrize(
        ("metodo", "ruta"), [("get", "/no-existe"), ("post", "/health"), ("get", "/api/rainfall")]
    )
    def test_los_errores_tambien(self, client, metodo, ruta):
        response = getattr(client, metodo)(ruta)
        assert response.status_code >= 400
        assert response.headers["x-content-type-options"] == "nosniff"

    def test_un_error_interno_tambien_y_no_muestra_detalles(self, client):
        response = client.get("/_test/boom")
        assert response.status_code == 500
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.json() == {
            "error": {"code": "internal_error", "message": "Ocurrió un error interno."}
        }
        for secreto in ("SELECT", "secretos", "/home/usuario", "Traceback", "RuntimeError"):
            assert secreto not in response.text

    def test_hsts_solo_en_produccion(self, tmp_path):
        assert "strict-transport-security" not in make_client(tmp_path).get("/health").headers
        prod = make_client(tmp_path, app_env="production")
        assert "max-age" in prod.get("/health").headers["strict-transport-security"]

    def test_la_documentacion_conserva_sus_scripts(self, client):
        assert "content-security-policy" not in client.get("/docs").headers

    def test_no_se_anuncia_el_servidor(self, client):
        assert "server" not in client.get("/health").headers


class TestTamano:
    def test_un_json_enorme_se_rechaza_con_413(self, tmp_path):
        client = make_client(tmp_path, max_request_bytes=1000)
        body = {"station_ids": [1], "from": "2016-01-01", "to": "2016-01-02", "x": "a" * 2000}
        response = client.post("/api/reports/summary", json=body)
        assert response.status_code == 413
        assert response.json()["error"]["code"] == "payload_too_large"
        assert response.headers["x-content-type-options"] == "nosniff"

    def test_un_cuerpo_sin_content_length_tambien_se_corta(self, tmp_path):
        client = make_client(tmp_path, max_request_bytes=1000)

        def trozos():
            for _ in range(5):
                yield b"a" * 500

        response = client.post("/api/reports/summary", content=trozos())
        assert response.status_code == 413

    def test_un_pedido_chico_pasa(self, tmp_path):
        client = make_client(tmp_path, max_request_bytes=1000)
        response = client.post(
            "/api/reports/summary",
            json={"station_ids": [999], "from": "2016-01-01", "to": "2016-01-02"},
        )
        assert response.status_code == 404  # llegó a la ruta: la estación no existe

    def test_la_importacion_admite_archivos_mas_grandes_que_un_json(self, tmp_path):
        client = make_client(
            tmp_path,
            max_request_bytes=1000,
            max_upload_bytes=100_000,
            admin_api_key="clave-larga-de-prueba",
        )
        response = client.post(
            "/api/import/audit",
            content=b"a" * 5000,
            headers={"X-API-Key": "clave-larga-de-prueba", "Content-Type": "text/csv"},
        )
        assert response.status_code != 413

    def test_la_importacion_igual_tiene_tope(self, tmp_path):
        client = make_client(tmp_path, max_upload_bytes=2000, admin_api_key="clave-larga-de-prueba")
        response = client.post(
            "/api/import/audit",
            content=b"a" * 10_000,
            headers={"X-API-Key": "clave-larga-de-prueba", "Content-Type": "text/csv"},
        )
        assert response.status_code == 413
