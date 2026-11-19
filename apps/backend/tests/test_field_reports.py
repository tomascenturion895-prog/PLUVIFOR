"""POST /api/field-reports (SCRUM-90): reporte policial observado, sin validar, con su ubicación."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.config import Settings
from app.db.base import Base
from app.main import create_app
from app.models import FieldReport, RainfallRecord

KEY = "clave-de-prueba-reportes"
H = {"X-API-Key": KEY}
VALIDO = {
    "obs_date": "2026-10-20",
    "mm": 35.5,
    "place": "Comisaría de Laguna Yema",
    "reporter": "Agente Pérez",
    "lat": -24.25,
    "lon": -61.25,
    "location_source": "dispositivo",
}


@pytest.fixture
def client(tmp_path) -> TestClient:
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url=f"sqlite:///{tmp_path / 'r.db'}",
        admin_api_key=KEY,
    )
    app = create_app(settings)
    Base.metadata.create_all(app.state.engine)
    return TestClient(app)


def contar(client, modelo=FieldReport) -> int:
    with client.app.state.session_factory() as db:
        return db.scalar(select(func.count()).select_from(modelo)) or 0


def test_un_reporte_valido_entra_como_observado_sin_validar_con_su_fuente(client):
    r = client.post("/api/field-reports", json=VALIDO, headers=H)
    assert r.status_code == 201
    body = r.json()
    assert (body["category"], body["validation"], body["source"]) == (
        "observado",
        "sin_validar",
        "reporte_policial",
    )
    assert (body["lat"], body["lon"], body["location_status"]) == (-24.25, -61.25, "informada")
    assert body["location_source"] == "dispositivo" and body["mm"] == 35.5
    assert contar(client) == 1


def test_sin_ubicacion_queda_pendiente_y_no_se_inventa(client):
    sin = {k: v for k, v in VALIDO.items() if k not in ("lat", "lon", "location_source")}
    body = client.post("/api/field-reports", json=sin, headers=H).json()
    assert body["location_status"] == "pendiente"
    assert body["lat"] is None and body["lon"] is None and body["location_source"] is None


def test_ubicacion_sin_origen_se_toma_como_manual(client):
    data = {**VALIDO}
    del data["location_source"]
    assert client.post("/api/field-reports", json=data, headers=H).json()["location_source"] == (
        "manual"
    )


def test_cero_mm_es_un_dato_valido(client):
    r = client.post("/api/field-reports", json={**VALIDO, "mm": 0}, headers=H)
    assert r.status_code == 201 and r.json()["mm"] == 0


@pytest.mark.parametrize(
    "cambio",
    [
        {"mm": -1},
        {"mm": 1000.5},
        {"mm": "mucho"},
        {"obs_date": "2026-11-01"},  # posterior al corte
        {"obs_date": "2030-01-01"},  # futura
        {"obs_date": "no-es-fecha"},
        {"place": ""},
        {"place": "   "},
        {"place": "x" * 201},
        {"reporter": ""},
        {"reporter": "Ana\x00Pérez"},
        {"lat": 95},
        {"lon": -200},
        {"lat": None},  # latitud sin longitud
        {"lon": None},  # longitud sin latitud
        {"extra": 1},
    ],
)
def test_entradas_invalidas_se_rechazan_y_no_se_guardan(client, cambio):
    r = client.post("/api/field-reports", json={**VALIDO, **cambio}, headers=H)
    assert r.status_code == 422
    assert r.json()["error"]["code"] and r.json()["error"]["message"]
    assert contar(client) == 0


def test_origen_sin_ubicacion_se_rechaza(client):
    data = {k: v for k, v in VALIDO.items() if k not in ("lat", "lon")}
    assert client.post("/api/field-reports", json=data, headers=H).status_code == 422


def test_la_fecha_posterior_al_corte_dice_el_corte(client):
    r = client.post("/api/field-reports", json={**VALIDO, "obs_date": "2026-11-01"}, headers=H)
    assert r.json()["error"]["code"] == "date_after_cutoff"
    assert "31/10/2026" in r.json()["error"]["message"]


def test_exige_la_clave_de_administracion(client):
    assert client.post("/api/field-reports", json=VALIDO).status_code == 401
    assert (
        client.post("/api/field-reports", json=VALIDO, headers={"X-API-Key": "x"}).status_code
        == 401
    )
    assert client.get("/api/field-reports").status_code == 401
    assert contar(client) == 0


def test_un_reporte_no_es_una_lectura_de_estacion(client):
    client.post("/api/field-reports", json=VALIDO, headers=H)
    assert contar(client, RainfallRecord) == 0


def test_el_listado_devuelve_los_ultimos_primero(client):
    for dia in ("2026-10-01", "2026-10-03", "2026-10-02"):
        client.post("/api/field-reports", json={**VALIDO, "obs_date": dia}, headers=H)
    body = client.get("/api/field-reports", params={"limit": 2}, headers=H).json()
    assert body["total"] == 3
    assert [i["obs_date"] for i in body["items"]] == ["2026-10-03", "2026-10-02"]


def test_un_intento_de_inyeccion_se_guarda_como_texto(client):
    texto = "x'); DROP TABLE field_reports;--"
    assert (
        client.post("/api/field-reports", json={**VALIDO, "place": texto}, headers=H).status_code
        == 201
    )
    assert contar(client) == 1
    assert client.get("/api/field-reports", headers=H).json()["items"][0]["place"] == texto


def test_nan_e_infinito_se_rechazan(client):
    for crudo in ("NaN", "Infinity", "-Infinity"):
        cuerpo = f'{{"obs_date":"2026-10-20","mm":{crudo},"place":"x","reporter":"y"}}'
        r = client.post(
            "/api/field-reports",
            content=cuerpo,
            headers={**H, "Content-Type": "application/json"},
        )
        assert r.status_code == 422, crudo
    assert contar(client) == 0
