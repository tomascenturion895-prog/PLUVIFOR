import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.errors import ApiError
from app.main import create_app


class Item(BaseModel):
    cantidad: int


@pytest.fixture
def client_con_rutas(settings):
    app = create_app(settings)

    @app.get("/_test/boom")
    def boom():
        raise RuntimeError("detalle interno secreto")

    @app.get("/_test/negocio")
    def negocio():
        raise ApiError(409, "conflict", "Ya existe.")

    @app.get("/_test/prohibido")
    def prohibido():
        raise HTTPException(status_code=403)

    @app.post("/_test/item")
    def item(body: Item):
        return body

    return TestClient(app, raise_server_exceptions=False)


def test_ruta_inexistente_devuelve_404_con_formato_unico(client):
    response = client.get("/no-existe")
    assert response.status_code == 404
    assert response.json() == {"error": {"code": "not_found", "message": "Not Found"}}


def test_metodo_no_permitido(client):
    response = client.post("/health")
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_validacion_devuelve_422_sin_eco_del_valor(client_con_rutas):
    response = client_con_rutas.post("/_test/item", json={"cantidad": "valor-sensible"})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"][0]["field"] == "body.cantidad"
    assert "valor-sensible" not in response.text


def test_error_inesperado_no_filtra_detalles(client_con_rutas):
    response = client_con_rutas.get("/_test/boom")
    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "internal_error", "message": "Ocurrió un error interno."}
    }
    assert "secreto" not in response.text


def test_error_de_negocio_controlado(client_con_rutas):
    response = client_con_rutas.get("/_test/negocio")
    assert response.status_code == 409
    assert response.json()["error"] == {"code": "conflict", "message": "Ya existe."}


def test_http_exception_usa_el_mismo_formato(client_con_rutas):
    response = client_con_rutas.get("/_test/prohibido")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"
