"""POST/GET /api/sensor-readings (SCRUM-94): lecturas de dispositivos, hoy siempre simuladas."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.config import Settings
from app.db.base import Base
from app.main import create_app
from app.models import RainfallRecord, SensorReading

KEY = "clave-de-prueba-dispositivos"
H = {"X-Device-Key": KEY}
VALIDA = {"device_id": "SIM-001", "read_at": "2026-10-20T07:00:00-03:00", "mm": 12.5}


def _cliente(tmp_path, **extra) -> TestClient:
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url=f"sqlite:///{tmp_path / 's.db'}",
        **extra,
    )
    app = create_app(settings)
    Base.metadata.create_all(app.state.engine)
    return TestClient(app)


@pytest.fixture
def client(tmp_path) -> TestClient:
    return _cliente(tmp_path, admin_api_key="otra-clave-de-admin", device_api_key=KEY)


def contar(client, modelo=SensorReading) -> int:
    with client.app.state.session_factory() as db:
        return db.scalar(select(func.count()).select_from(modelo)) or 0


def test_una_lectura_valida_entra_como_simulada_con_su_fuente(client):
    r = client.post("/api/sensor-readings", json=VALIDA, headers=H)
    assert r.status_code == 201
    body = r.json()
    assert (body["category"], body["source"]) == ("simulado", "sensor_simulado")
    assert body["mm"] == 12.5 and body["device_id"] == "SIM-001"
    assert (body["lat"], body["lon"]) == (None, None)
    # La hora se guarda y se devuelve en UTC: 07:00 en Argentina son las 10:00 UTC.
    assert body["read_at"].startswith("2026-10-20T10:00:00")
    assert body["read_at"].endswith(("Z", "+00:00"))
    assert contar(client) == 1


def test_el_cliente_no_puede_declarar_la_categoria(client):
    for extra in ({"category": "observado"}, {"category": "simulado"}, {"validation": "validado"}):
        r = client.post("/api/sensor-readings", json={**VALIDA, **extra}, headers=H)
        assert r.status_code == 422
    assert contar(client) == 0


def test_sin_clave_se_rechaza(client):
    r = client.post("/api/sensor-readings", json=VALIDA)
    assert r.status_code == 401 and r.json()["error"]["code"] == "unauthorized"
    assert contar(client) == 0


def test_clave_incorrecta_se_rechaza_y_la_de_administrador_no_sirve(client):
    assert (
        client.post("/api/sensor-readings", json=VALIDA, headers={"X-Device-Key": "x"}).status_code
        == 401
    )
    admin = {"X-Device-Key": "otra-clave-de-admin", "X-API-Key": "otra-clave-de-admin"}
    assert client.post("/api/sensor-readings", json=VALIDA, headers=admin).status_code == 401
    assert contar(client) == 0


def test_sin_clave_configurada_la_ingesta_queda_cerrada(tmp_path):
    cerrado = _cliente(tmp_path, device_api_key=None)
    r = cerrado.post("/api/sensor-readings", json=VALIDA, headers=H)
    assert r.status_code == 403 and "DEVICE_API_KEY" in r.json()["error"]["message"]


@pytest.mark.parametrize(
    "cambio",
    [
        {"mm": -1},
        {"mm": 1000.5},
        {"mm": "mucho"},
        {"mm": None},  # un dato que falta no es 0 mm: no se acepta como lectura
        {"device_id": ""},
        {"device_id": "../etc"},
        {"device_id": "sensor con espacios"},
        {"device_id": "a" * 65},
        {"read_at": "2026-10-20T07:00:00"},  # sin zona horaria: ambigua
        {"read_at": "ayer"},
        {"lat": -24.0},  # latitud sin longitud
        {"lon": -60.0},
        {"lat": 91, "lon": -60.0},
    ],
)
def test_entradas_invalidas_se_rechazan_sin_guardar_nada(client, cambio):
    r = client.post("/api/sensor-readings", json={**VALIDA, **cambio}, headers=H)
    assert r.status_code == 422, cambio
    assert contar(client) == 0


def test_falta_un_campo_obligatorio(client):
    for campo in ("device_id", "read_at", "mm"):
        sin = {k: v for k, v in VALIDA.items() if k != campo}
        assert client.post("/api/sensor-readings", json=sin, headers=H).status_code == 422


def test_un_cero_medido_es_una_lectura_valida(client):
    body = client.post("/api/sensor-readings", json={**VALIDA, "mm": 0}, headers=H).json()
    assert body["mm"] == 0


def test_con_ubicacion_completa_se_guarda_tal_cual(client):
    r = client.post(
        "/api/sensor-readings", json={**VALIDA, "lat": -24.25, "lon": -61.25}, headers=H
    )
    assert (r.json()["lat"], r.json()["lon"]) == (-24.25, -61.25)


def test_no_se_aceptan_lecturas_posteriores_al_corte(client):
    r = client.post(
        "/api/sensor-readings", json={**VALIDA, "read_at": "2026-11-01T07:00:00-03:00"}, headers=H
    )
    assert r.status_code == 422 and r.json()["error"]["code"] == "date_after_cutoff"
    assert contar(client) == 0


def test_el_corte_cuenta_por_dia_de_argentina_no_de_utc(client):
    # 23:00 del 31/10 en Argentina ya es 01/11 en UTC, pero sigue siendo el 31/10 acá.
    r = client.post(
        "/api/sensor-readings", json={**VALIDA, "read_at": "2026-10-31T23:00:00-03:00"}, headers=H
    )
    assert r.status_code == 201


def test_reenviar_la_misma_lectura_no_la_duplica(client):
    assert client.post("/api/sensor-readings", json=VALIDA, headers=H).status_code == 201
    otra_vez = client.post("/api/sensor-readings", json=VALIDA, headers=H)
    assert otra_vez.status_code == 200 and otra_vez.json()["mm"] == 12.5
    assert contar(client) == 1


def test_misma_hora_con_otro_valor_es_un_conflicto_y_no_pisa_el_dato(client):
    client.post("/api/sensor-readings", json=VALIDA, headers=H)
    r = client.post("/api/sensor-readings", json={**VALIDA, "mm": 99}, headers=H)
    assert r.status_code == 409 and r.json()["error"]["code"] == "reading_conflict"
    assert client.get("/api/sensor-readings").json()["items"][0]["mm"] == 12.5


def test_la_misma_hora_en_otra_zona_es_la_misma_lectura(client):
    client.post("/api/sensor-readings", json=VALIDA, headers=H)
    en_utc = {**VALIDA, "read_at": "2026-10-20T10:00:00Z"}
    assert client.post("/api/sensor-readings", json=en_utc, headers=H).status_code == 200
    assert contar(client) == 1


def test_una_lectura_nunca_entra_a_las_series_de_estaciones(client):
    antes = contar(client, RainfallRecord)
    client.post("/api/sensor-readings", json=VALIDA, headers=H)
    assert contar(client, RainfallRecord) == antes == 0


def test_listar_es_publico_rotula_todo_como_simulado_y_filtra_por_dispositivo(client):
    for dispositivo, hora in (("SIM-001", "07"), ("SIM-002", "08"), ("SIM-001", "09")):
        cuerpo = {**VALIDA, "device_id": dispositivo, "read_at": f"2026-10-20T{hora}:00:00-03:00"}
        client.post("/api/sensor-readings", json=cuerpo, headers=H)
    body = client.get("/api/sensor-readings").json()  # sin clave: la lectura es pública
    assert body["total"] == 3
    assert {i["category"] for i in body["items"]} == {"simulado"}
    assert "simuladas" in body["notice"] and "no son datos de sensores reales" in body["notice"]
    horas = [i["read_at"] for i in body["items"]]
    assert horas == sorted(horas, reverse=True)
    solo = client.get("/api/sensor-readings", params={"device_id": "SIM-002"}).json()
    assert solo["total"] == 1 and solo["items"][0]["device_id"] == "SIM-002"


def test_listar_valida_la_paginacion_y_sin_lecturas_devuelve_lista_vacia(client):
    vacio = client.get("/api/sensor-readings").json()
    assert vacio["items"] == [] and vacio["total"] == 0 and vacio["notice"]
    assert client.get("/api/sensor-readings", params={"limit": 201}).status_code == 422
    assert client.get("/api/sensor-readings", params={"offset": -1}).status_code == 422


def test_dispositivos_resume_cada_uno_con_su_ultima_lectura(client):
    for device, hora, mm in [
        ("SIM-001", "2026-10-20T07:00:00-03:00", 12.5),
        ("SIM-001", "2026-10-22T07:00:00-03:00", 0),
        ("SIM-002", "2026-10-21T07:00:00-03:00", 3),
    ]:
        client.post(
            "/api/sensor-readings",
            json={"device_id": device, "read_at": hora, "mm": mm},
            headers=H,
        )
    r = client.get("/api/sensor-readings/devices")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2 and "simuladas" in body["notice"]
    uno, dos = body["items"]
    assert uno["device_id"] == "SIM-001" and uno["readings"] == 2
    # La última lectura es un 0 real (midió y no llovió): se devuelve como 0, no como vacío.
    assert uno["last_mm"] == 0 and uno["last_read_at"].startswith("2026-10-22T10:00:00")
    assert uno["first_read_at"].startswith("2026-10-20T10:00:00")
    assert (dos["device_id"], dos["last_mm"], dos["category"]) == ("SIM-002", 3, "simulado")


def test_dispositivos_sin_lecturas_devuelve_lista_vacia_y_no_inventa_ninguno(client):
    body = client.get("/api/sensor-readings/devices").json()
    assert body["items"] == [] and body["total"] == 0


def _enviar(client, device, dia, mm=1.0):
    client.post(
        "/api/sensor-readings",
        json={"device_id": device, "read_at": f"{dia}T07:00:00-03:00", "mm": mm},
        headers=H,
    )


def test_dispositivo_sin_lecturas_recientes_queda_en_silencio_contra_el_corte(client):
    _enviar(client, "SIM-001", "2026-10-30")  # a 1 día del corte (31/10/2026)
    _enviar(client, "SIM-002", "2026-09-20")  # a 41 días del corte
    body = client.get("/api/sensor-readings/devices").json()
    activo, silencio = body["items"]
    assert (activo["state"], activo["days_since_last"]) == ("activa", 1)
    assert (silencio["state"], silencio["days_since_last"]) == ("en_silencio", 41)
    assert silencio["last_read_date"] == "2026-09-20"
    assert (body["active"], body["silent"], body["silent_after_days"]) == (1, 1, 30)
    assert body["data_cutoff_date"] == "2026-10-31"


def test_el_umbral_de_silencio_se_puede_cambiar_y_se_valida(client):
    _enviar(client, "SIM-002", "2026-09-20")
    ok = client.get("/api/sensor-readings/devices", params={"silent_after_days": 60}).json()
    assert ok["items"][0]["state"] == "activa" and ok["silent_after_days"] == 60
    for invalido in (0, -1, 366, "abc"):
        r = client.get("/api/sensor-readings/devices", params={"silent_after_days": invalido})
        assert r.status_code == 422


def test_un_silencio_no_se_devuelve_como_0_mm(client):
    _enviar(client, "SIM-002", "2026-09-20", mm=7.5)
    item = client.get("/api/sensor-readings/devices").json()["items"][0]
    # En silencio sigue mostrando la última lectura real, no la rellena con 0.
    assert item["state"] == "en_silencio" and item["last_mm"] == 7.5
