"""Avisos vinculados a cuentas y a varias estaciones, con historial de envíos."""

import re
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import Settings
from app.db.base import Base
from app.domain.auth import Role
from app.domain.enums import DataCategory, RainState, Validation
from app.main import create_app
from app.models import (
    AlertDispatch,
    AlertOutbox,
    AlertSubscription,
    AlertSubscriptionStation,
    RainfallRecord,
    Source,
    Station,
    User,
)

KEY = "clave-admin-de-prueba"
H = {"X-API-Key": KEY}
CLAVE = "una-clave-larga-1"
DIA = date(2026, 10, 20)
TEL = "+54 370 4123456"
TEL2 = "+54 370 4222222"


@pytest.fixture
def client(tmp_path) -> TestClient:
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url=f"sqlite:///{tmp_path / 'v.db'}",
        admin_api_key=KEY,
        alerts_secret="secreto-de-prueba-para-avisos",  # noqa: S106
        rate_limit_per_minute=0,
        rate_limit_auth_per_minute=0,
    )
    app = create_app(settings)
    Base.metadata.create_all(app.state.engine)
    with app.state.session_factory() as db:
        fuente = Source(
            code="siga_inta",
            name="SIGA",
            network="INTA",
            category=DataCategory.OBSERVADO,
            day_cutoff_local="09:00",
        )
        db.add(fuente)
        db.flush()
        for codigo, nombre in (("424", "El Colorado"), ("425", "Bartolomé"), ("51", "EMC")):
            est = Station(source_id=fuente.id, code=codigo, name=nombre)
            db.add(est)
            db.flush()
            db.add(
                RainfallRecord(
                    station_id=est.id,
                    obs_date=DIA,
                    state=RainState.DATO,
                    mm=120.0,
                    category=DataCategory.OBSERVADO,
                    validation=Validation.SIN_VALIDAR,
                )
            )
        db.commit()
    return TestClient(app)


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def cuenta(client, email="ana@correo.com", rol: Role | None = None) -> str:
    client.post("/api/auth/register", json={"email": email, "password": CLAVE})
    if rol is not None:
        with client.app.state.session_factory() as db:
            db.scalars(select(User).where(User.email == email)).one().role = rol
            db.commit()
    return client.post("/api/auth/login", json={"email": email, "password": CLAVE}).json()["token"]


def codigo_de(client, telefono: str) -> str:
    with client.app.state.session_factory() as db:
        mensajes = list(db.scalars(select(AlertOutbox).where(AlertOutbox.kind == "codigo")))
        sub = db.scalars(select(AlertSubscription)).all()
        assert sub
        return re.search(r"es (\d{6})", mensajes[-1].body).group(1)


def suscribir(client, telefono=TEL, token: str | None = None, **extra) -> None:
    headers = bearer(token) if token else {}
    r = client.post("/api/alerts/subscriptions", json={"phone": telefono, **extra}, headers=headers)
    assert r.status_code == 202, r.text
    r = client.post(
        "/api/alerts/subscriptions/confirm",
        json={"phone": telefono, "code": codigo_de(client, telefono)},
    )
    assert r.status_code == 200, r.text


# --- varias estaciones ----------------------------------------------------------------------


def test_una_suscripcion_puede_pedir_varias_estaciones(client):
    suscribir(client, station_ids=[1, 3])
    with client.app.state.session_factory() as db:
        pares = db.scalars(select(AlertSubscriptionStation)).all()
        assert sorted(p.station_id for p in pares) == [1, 3]


def test_las_estaciones_repetidas_se_unifican_y_una_inexistente_se_rechaza(client):
    suscribir(client, station_ids=[2, 2, 2])
    with client.app.state.session_factory() as db:
        assert len(db.scalars(select(AlertSubscriptionStation)).all()) == 1
    r = client.post("/api/alerts/subscriptions", json={"phone": TEL2, "station_ids": [1, 9999]})
    assert r.status_code == 404


@pytest.mark.parametrize("malo", [[0], [-1], ["x"], list(range(1, 22)), 5])
def test_las_estaciones_se_validan(client, malo):
    r = client.post("/api/alerts/subscriptions", json={"phone": TEL, "station_ids": malo})
    assert r.status_code == 422


def test_el_aviso_llega_a_quien_pidio_esa_estacion_y_a_quien_pidio_todas(client):
    suscribir(client, TEL, station_ids=[1])  # solo la 1
    suscribir(client, TEL2, station_ids=[2, 3])  # la 2 y la 3
    suscribir(client, "+54 370 4333333")  # ninguna = todas
    r = client.post("/api/alerts/send", params={"station_id": 1, "date": DIA}, headers=H)
    assert r.json()["queued"] == 2  # la de la estación 1 y la de «todas»
    r = client.post("/api/alerts/send", params={"station_id": 3, "date": DIA}, headers=H)
    assert r.json()["queued"] == 2  # la de las estaciones 2 y 3 y la de «todas»


# --- cuenta dueña ---------------------------------------------------------------------------


def test_con_sesion_la_suscripcion_queda_a_nombre_de_la_cuenta(client):
    token = cuenta(client)
    suscribir(client, token=token, station_ids=[1])
    mias = client.get("/api/alerts/mine", headers=bearer(token)).json()
    assert mias["total"] == 1
    sub = mias["items"][0]
    assert sub["status"] == "confirmada" and sub["phone_last4"] == "3456"
    assert [s["code"] for s in sub["stations"]] == ["424"]
    assert "phone_hash" not in str(sub) and TEL not in str(sub)


def test_sin_sesion_la_suscripcion_no_tiene_dueno_y_no_aparece_en_nadie(client):
    token = cuenta(client)
    suscribir(client, station_ids=[1])
    assert client.get("/api/alerts/mine", headers=bearer(token)).json()["total"] == 0


def test_mis_avisos_pide_sesion(client):
    for ruta in ("/api/alerts/mine", "/api/alerts/mine/notifications"):
        assert client.get(ruta).status_code == 401


def test_cada_cuenta_ve_solo_lo_suyo(client):
    ana = cuenta(client, "ana@correo.com")
    beto = cuenta(client, "beto@correo.com")
    suscribir(client, TEL, token=ana)
    suscribir(client, TEL2, token=beto)
    assert [
        s["phone_last4"]
        for s in client.get("/api/alerts/mine", headers=bearer(ana)).json()["items"]
    ] == ["3456"]
    assert [
        s["phone_last4"]
        for s in client.get("/api/alerts/mine", headers=bearer(beto)).json()["items"]
    ] == ["2222"]


def test_cambiar_las_estaciones_de_mi_suscripcion(client):
    token = cuenta(client)
    suscribir(client, token=token, station_ids=[1])
    sub_id = client.get("/api/alerts/mine", headers=bearer(token)).json()["items"][0]["id"]
    r = client.put(
        f"/api/alerts/mine/{sub_id}/stations", json={"station_ids": [2, 3]}, headers=bearer(token)
    )
    assert r.status_code == 200 and [s["code"] for s in r.json()["stations"]] == ["425", "51"]
    r = client.put(
        f"/api/alerts/mine/{sub_id}/stations", json={"station_ids": []}, headers=bearer(token)
    )
    assert r.json()["stations"] == []  # vacío = todas
    r = client.put(
        f"/api/alerts/mine/{sub_id}/stations", json={"station_ids": [9999]}, headers=bearer(token)
    )
    assert r.status_code == 404


def test_no_se_puede_tocar_la_suscripcion_de_otra_cuenta(client):
    ana = cuenta(client, "ana@correo.com")
    beto = cuenta(client, "beto@correo.com")
    suscribir(client, token=ana, station_ids=[1])
    sub_id = client.get("/api/alerts/mine", headers=bearer(ana)).json()["items"][0]["id"]
    # Ajena e inexistente responden igual: no se revela qué suscripciones hay.
    for r in (
        client.put(
            f"/api/alerts/mine/{sub_id}/stations", json={"station_ids": [2]}, headers=bearer(beto)
        ),
        client.post(f"/api/alerts/mine/{sub_id}/unsubscribe", headers=bearer(beto)),
        client.post("/api/alerts/mine/9999/unsubscribe", headers=bearer(beto)),
    ):
        assert r.status_code == 404 and r.json()["error"]["code"] == "subscription_not_found"
    assert (
        client.get("/api/alerts/mine", headers=bearer(ana)).json()["items"][0]["status"]
        == "confirmada"
    )


def test_me_doy_de_baja_sin_necesitar_el_telefono_y_dejo_de_recibir(client):
    token = cuenta(client)
    suscribir(client, token=token)
    sub_id = client.get("/api/alerts/mine", headers=bearer(token)).json()["items"][0]["id"]
    r = client.post(f"/api/alerts/mine/{sub_id}/unsubscribe", headers=bearer(token))
    assert r.status_code == 200 and r.json()["status"] == "baja"
    assert (
        client.post("/api/alerts/send", params={"station_id": 1, "date": DIA}, headers=H).json()[
            "queued"
        ]
        == 0
    )


def test_mis_notificaciones_son_solo_las_del_sistema_y_solo_las_mias(client):
    ana = cuenta(client, "ana@correo.com")
    beto = cuenta(client, "beto@correo.com")
    suscribir(client, TEL, token=ana, email="ana@correo.com")
    suscribir(client, TEL2, token=beto)
    client.post("/api/alerts/send", params={"station_id": 1, "date": DIA}, headers=H)
    notas = client.get("/api/alerts/mine/notifications", headers=bearer(ana)).json()
    assert {m["channel"] for m in notas["items"]} == {"sistema"}
    assert [m["kind"] for m in notas["items"]] == ["aviso", "bienvenida"]  # más nuevas primero
    assert all("…3456" == m["recipient"] for m in notas["items"])  # nunca las de Beto


def test_las_notificaciones_mias_funcionan_sin_el_modo_demostracion(client):
    """El canal del sistema es el que sí sería real: no depende de ALERTS_DEMO."""
    token = cuenta(client)
    suscribir(client, token=token)
    assert client.post("/api/alerts/inbox", json={"phone": TEL}).status_code == 403
    assert client.get("/api/alerts/mine/notifications", headers=bearer(token)).status_code == 200


def test_borrar_la_cuenta_borra_sus_suscripciones_y_mensajes(client):
    token = cuenta(client)
    suscribir(client, token=token)
    with client.app.state.session_factory() as db:
        usuario = db.scalars(select(User)).one()
        db.delete(usuario)
        db.commit()
        assert db.scalars(select(AlertSubscription)).all() == []
        assert db.scalars(select(AlertOutbox)).all() == []


# --- historial de avisos --------------------------------------------------------------------


def test_cada_envio_queda_en_el_historial_con_quien_lo_mando(client):
    operador = cuenta(client, "olga@correo.com", Role.OPERADOR)
    suscribir(client, TEL)
    suscribir(client, TEL2)
    r = client.post(
        "/api/alerts/send", params={"station_id": 2, "date": DIA}, headers=bearer(operador)
    )
    assert r.json()["queued"] == 2
    historial = client.get("/api/alerts/dispatches", headers=bearer(operador)).json()
    assert historial["total"] == 1
    d = historial["items"][0]
    assert (d["station_name"], d["mm"], d["level"], d["queued"], str(DIA)) == (
        "Bartolomé",
        120.0,
        100,
        2,
        d["obs_date"],
    )
    with client.app.state.session_factory() as db:
        usuario = db.scalars(select(User).where(User.email == "olga@correo.com")).one()
        assert d["created_by_user_id"] == usuario.id
        enlazados = db.scalars(select(AlertOutbox).where(AlertOutbox.dispatch_id == d["id"])).all()
        assert len(enlazados) == 4  # WhatsApp y sistema, para cada una de las dos personas


def test_un_envio_con_la_clave_de_administracion_no_deja_autor(client):
    suscribir(client)
    client.post("/api/alerts/send", params={"station_id": 1, "date": DIA}, headers=H)
    d = client.get("/api/alerts/dispatches", headers=H).json()["items"][0]
    assert d["created_by_user_id"] is None


def test_un_dia_que_no_avisa_no_deja_renglon_en_el_historial(client):
    r = client.post(
        "/api/alerts/send", params={"station_id": 1, "date": DIA - timedelta(days=5)}, headers=H
    )
    assert r.json()["preview"]["reason"] == "sin_dato" and r.json()["queued"] == 0
    assert client.get("/api/alerts/dispatches", headers=H).json()["total"] == 0


def test_un_envio_sin_destinatarios_igual_queda_registrado_con_cero(client):
    client.post("/api/alerts/send", params={"station_id": 1, "date": DIA}, headers=H)
    d = client.get("/api/alerts/dispatches", headers=H).json()["items"][0]
    assert d["queued"] == 0


def test_el_historial_solo_lo_ve_el_personal(client):
    ciudadano = cuenta(client)
    assert client.get("/api/alerts/dispatches").status_code == 401
    assert client.get("/api/alerts/dispatches", headers=bearer(ciudadano)).status_code == 403
    with client.app.state.session_factory() as db:
        assert db.scalars(select(AlertDispatch)).all() == []
