"""Entradas inválidas en todos los endpoints de lectura (SCRUM-55).

Una entrada mala nunca puede dar un 500, ni un 200 con ceros: tiene que dar 404 o 422 con el
formato de error único (`error.code` y `error.message` en español).
"""

import pytest
from fastapi.testclient import TestClient

DESDE_HASTA = {"from": "2016-01-01", "to": "2016-01-31"}


def assert_error(response, status: int) -> dict:
    assert response.status_code == status, response.text
    error = response.json()["error"]
    assert error["code"] and error["message"]
    return error


@pytest.mark.parametrize("estacion", ["0", "-1", "abc", "1.5", "", "99999999999999999999"])
def test_id_de_estacion_invalido_en_la_serie(client: TestClient, estacion: str):
    response = client.get("/api/rainfall", params={"station_id": estacion, **DESDE_HASTA})
    assert response.status_code in (404, 422)
    assert response.json()["error"]["code"]


@pytest.mark.parametrize("fecha", ["2016-02-30", "2016-13-01", "2016-00-10", "01/01/2016", "ayer"])
def test_fechas_imposibles_o_mal_escritas_dan_422(client: TestClient, fecha: str):
    for campo in ("from", "to"):
        params = {"station_id": 1, "from": "2016-01-01", "to": "2016-01-31", campo: fecha}
        assert_error(client.get("/api/rainfall", params=params), 422)
        assert_error(client.get("/api/rainfall/accumulated", params=params), 422)


@pytest.mark.parametrize("estacion", ["0", "-5", "abc", "99999999999999999999"])
def test_id_de_estacion_invalido_en_el_detalle(client: TestClient, estacion: str):
    response = client.get(f"/api/stations/{estacion}")
    assert response.status_code in (404, 422)
    assert response.json()["error"]["code"]


def test_acumulado_con_un_rango_enorme_da_422(client: TestClient):
    params = {"station_id": 1, "from": "1900-01-01", "to": "2016-01-01"}
    assert assert_error(client.get("/api/rainfall/accumulated", params=params), 422)["code"] == (
        "range_too_large"
    )


@pytest.mark.parametrize("zona", ["", "x" * 101])
def test_zona_vacia_o_demasiado_larga_da_422(client: TestClient, zona: str):
    assert_error(client.get("/api/rainfall/accumulated", params={"zone": zona, **DESDE_HASTA}), 422)


@pytest.mark.parametrize("zona", ["'; DROP TABLE stations; --", "%", "<script>alert(1)</script>"])
def test_una_zona_con_texto_raro_no_se_ejecuta_ni_da_500(client: TestClient, zona: str):
    error = assert_error(
        client.get("/api/rainfall/accumulated", params={"zone": zona, **DESDE_HASTA}), 404
    )
    assert error["code"] == "zone_not_found"
    assert zona not in error["message"]  # no se devuelve lo que mandó el usuario


@pytest.mark.parametrize(
    "params",
    [{"limit": "0"}, {"limit": "-1"}, {"limit": "100000"}, {"offset": "-1"}, {"limit": "abc"}],
)
def test_paginacion_invalida_en_estaciones_da_422(client: TestClient, params: dict):
    assert_error(client.get("/api/stations", params=params), 422)


@pytest.mark.parametrize("ruta", ["/api/rainfall", "/api/rainfall/accumulated"])
def test_sin_parametros_obligatorios_da_422(client: TestClient, ruta: str):
    assert_error(client.get(ruta), 422)


def test_un_periodo_de_un_solo_dia_es_valido(client: TestClient):
    """Caso feliz en el borde: desde = hasta no es un rango inválido."""
    response = client.get(
        "/api/rainfall", params={"station_id": 1, "from": "2016-01-01", "to": "2016-01-01"}
    )
    assert response.status_code in (200, 404)  # 404 si la base de prueba no tiene estaciones
    if response.status_code == 200:
        assert response.json()["summary"]["days_in_period"] == 1


def test_un_id_gigante_no_rompe_el_parte_ni_la_referencia(client: TestClient):
    huge = 99999999999999999999
    parte = client.post(
        "/api/reports/summary",
        json={"station_ids": [huge], "from": "2016-01-01", "to": "2016-01-31"},
    )
    assert_error(parte, 422)
    assert_error(client.get("/api/climate-reference", params={"station_id": huge}), 422)
    acumulado = client.get("/api/rainfall/accumulated", params={"station_id": huge, **DESDE_HASTA})
    assert_error(acumulado, 422)
