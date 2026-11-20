"""Avisos a la población (canal simulado): suscripción, confirmación, baja y aviso por umbral."""

from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import Settings
from app.db.base import Base
from app.domain.alerts import alert_message, level_for, normalize_phone
from app.domain.enums import DataCategory, RainState, Validation
from app.main import create_app
from app.models import AlertOutbox, AlertSubscription, RainfallRecord, Source, Station

KEY = "clave-admin-de-prueba"
H = {"X-API-Key": KEY}
TEL = "+54 370 4123456"
DIA = date(2026, 10, 20)


@pytest.fixture
def client(tmp_path) -> TestClient:
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url=f"sqlite:///{tmp_path / 'a.db'}",
        admin_api_key=KEY,
        alerts_secret="secreto-de-prueba-para-avisos",  # noqa: S106
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
        estacion = Station(source_id=fuente.id, code="424", name="El Colorado")
        db.add(estacion)
        db.flush()
        dias = [
            (DIA, RainState.DATO, 112.0),
            (DIA + timedelta(days=1), RainState.DATO, 20.0),
            (DIA + timedelta(days=2), RainState.SIN_FILA, None),
            (DIA + timedelta(days=3), RainState.FILA_SIN_VALOR, None),
            (DIA + timedelta(days=4), RainState.DATO, 0.0),
        ]
        for dia, estado, mm in dias:
            db.add(
                RainfallRecord(
                    station_id=estacion.id,
                    obs_date=dia,
                    state=estado,
                    mm=mm,
                    category=DataCategory.OBSERVADO,
                    validation=Validation.SIN_VALIDAR,
                )
            )
        db.commit()
    return TestClient(app)


def _mensajes(client: TestClient) -> list[AlertOutbox]:
    with client.app.state.session_factory() as db:
        return list(db.scalars(select(AlertOutbox).order_by(AlertOutbox.id)))


def _suscribir_y_confirmar(client: TestClient, telefono: str = TEL, **extra) -> None:
    assert (
        client.post("/api/alerts/subscriptions", json={"phone": telefono, **extra}).status_code
        == 202
    )
    codigos = [m for m in _mensajes(client) if m.kind == "codigo"]
    codigo = codigos[-1].body.split("es ")[1][:6]
    r = client.post("/api/alerts/subscriptions/confirm", json={"phone": telefono, "code": codigo})
    assert r.status_code == 200 and r.json()["status"] == "confirmada"


# --- reglas puras ---------------------------------------------------------------------------


def test_los_umbrales_son_50_y_100_y_bajo_50_no_avisa():
    assert (level_for(49.9), level_for(50), level_for(99.9), level_for(100)) == (None, 50, 50, 100)


@pytest.mark.parametrize("malo", ["", "abc", "123", "+54 370 4123456789012345", "12; DROP TABLE"])
def test_un_telefono_invalido_se_rechaza(malo):
    with pytest.raises(ValueError):
        normalize_phone(malo)


def test_el_telefono_se_normaliza():
    assert normalize_phone(" +54 (370) 412-3456 ") == "+543704123456"


def test_el_mensaje_no_ordena_evacuar_y_lleva_fuente_categoria_y_leyenda():
    texto = alert_message("El Colorado", "424", DIA, 112.0, 100, validated=False)
    assert "dato observado, sin validar" in texto and "424" in texto and "20/10/2026" in texto
    assert "No es una orden ni una recomendación de evacuar" in texto
    assert "Defensa Civil" in texto and "PROTOTIPO" in texto


# --- suscripción ----------------------------------------------------------------------------


def test_sin_clave_de_avisos_la_suscripcion_queda_cerrada(tmp_path):
    cerrado = create_app(
        Settings(_env_file=None, app_env="test", database_url=f"sqlite:///{tmp_path / 'c.db'}")
    )
    Base.metadata.create_all(cerrado.state.engine)
    r = TestClient(cerrado).post("/api/alerts/subscriptions", json={"phone": TEL})
    assert r.status_code == 403


def test_suscribirse_manda_un_codigo_simulado_y_no_guarda_el_numero(client):
    r = client.post("/api/alerts/subscriptions", json={"phone": TEL})
    assert r.status_code == 202 and r.json()["status"] == "pendiente"
    assert "simulado" in r.json()["notice"]
    assert "code" not in r.text and TEL not in r.text  # el código nunca vuelve en la respuesta
    (mensaje,) = _mensajes(client)
    assert mensaje.kind == "codigo" and mensaje.category == "simulado"
    with client.app.state.session_factory() as db:
        sub = db.scalars(select(AlertSubscription)).one()
        assert sub.phone_last4 == "3456" and "3704123456" not in sub.phone_hash
        assert sub.status == "pendiente" and sub.code_hash and "3704123456" not in sub.code_hash


def test_confirmar_con_el_codigo_correcto_activa_la_suscripcion(client):
    _suscribir_y_confirmar(client)


def test_un_codigo_incorrecto_se_rechaza_y_tras_5_intentos_se_bloquea(client):
    client.post("/api/alerts/subscriptions", json={"phone": TEL})
    codigo = _mensajes(client)[-1].body.split("es ")[1][:6]
    malo = "000000" if codigo != "000000" else "111111"
    for _ in range(5):
        r = client.post("/api/alerts/subscriptions/confirm", json={"phone": TEL, "code": malo})
        assert r.status_code == 422
    # Aun con el código correcto, ya hay que pedir uno nuevo.
    r = client.post("/api/alerts/subscriptions/confirm", json={"phone": TEL, "code": codigo})
    assert r.status_code == 429


def test_un_codigo_vencido_no_sirve(client):
    client.post("/api/alerts/subscriptions", json={"phone": TEL})
    codigo = _mensajes(client)[-1].body.split("es ")[1][:6]
    with client.app.state.session_factory() as db:
        sub = db.scalars(select(AlertSubscription)).one()
        sub.code_expires_at = datetime.now(UTC) - timedelta(minutes=1)
        db.commit()
    r = client.post("/api/alerts/subscriptions/confirm", json={"phone": TEL, "code": codigo})
    assert r.status_code == 422


@pytest.mark.parametrize("codigo", ["12345", "1234567", "abcdef", ""])
def test_el_formato_del_codigo_se_valida(client, codigo):
    r = client.post("/api/alerts/subscriptions/confirm", json={"phone": TEL, "code": codigo})
    assert r.status_code == 422


def test_confirmar_un_numero_que_no_pidio_avisos_falla_igual_que_un_codigo_malo(client):
    r = client.post("/api/alerts/subscriptions/confirm", json={"phone": TEL, "code": "123456"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_code"


def test_la_estacion_elegida_tiene_que_existir(client):
    r = client.post("/api/alerts/subscriptions", json={"phone": TEL, "station_id": 9999})
    assert r.status_code == 404


def test_no_se_aceptan_campos_de_mas(client):
    r = client.post("/api/alerts/subscriptions", json={"phone": TEL, "status": "confirmada"})
    assert r.status_code == 422


# --- aviso ----------------------------------------------------------------------------------


def test_vista_previa_de_un_dia_intenso_arma_el_aviso_observado_sin_validar(client):
    r = client.get("/api/alerts/preview", params={"station_id": 1, "date": DIA}, headers=H)
    body = r.json()
    assert r.status_code == 200 and body["would_send"] and body["level"] == 100
    assert body["mm"] == 112.0 and body["category"] == "observado"
    assert "sin validar" in body["message"] and "evacuar" in body["message"]


def test_un_dia_bajo_el_umbral_no_avisa(client):
    body = client.get(
        "/api/alerts/preview", params={"station_id": 1, "date": DIA + timedelta(days=1)}, headers=H
    ).json()
    assert (body["would_send"], body["reason"], body["mm"]) == (False, "bajo_umbral", 20.0)


@pytest.mark.parametrize("dias", [2, 3])
def test_un_hueco_no_avisa_ni_se_cuenta_como_0_mm(client, dias):
    body = client.get(
        "/api/alerts/preview",
        params={"station_id": 1, "date": DIA + timedelta(days=dias)},
        headers=H,
    ).json()
    assert (body["would_send"], body["reason"]) == (False, "sin_dato")
    assert body["mm"] is None and body["message"] is None


def test_no_se_avisa_sobre_un_dia_posterior_al_corte(client):
    r = client.get("/api/alerts/preview", params={"station_id": 1, "date": "2026-11-05"}, headers=H)
    assert r.status_code == 422 and r.json()["error"]["code"] == "date_after_cutoff"


def test_la_vista_previa_y_el_envio_piden_la_clave_de_administracion(client):
    params = {"station_id": 1, "date": DIA}
    assert client.get("/api/alerts/preview", params=params).status_code == 401
    assert client.post("/api/alerts/send", params=params).status_code == 401
    assert client.get("/api/alerts/outbox").status_code == 401
    assert client.get("/api/alerts/outbox", headers={"X-API-Key": "otra"}).status_code == 401


def test_el_envio_llega_solo_a_las_suscripciones_confirmadas_y_a_nadie_real(client):
    _suscribir_y_confirmar(client, "+54 370 4111111")  # confirmada, cualquier estación
    _suscribir_y_confirmar(client, "+54 370 4222222", station_id=1)  # confirmada, estación 1
    client.post("/api/alerts/subscriptions", json={"phone": "+54 370 4333333"})  # sin confirmar
    antes = len(_mensajes(client))
    r = client.post("/api/alerts/send", params={"station_id": 1, "date": DIA}, headers=H)
    assert r.status_code == 200 and r.json()["queued"] == 2
    nuevos = _mensajes(client)[antes:]
    # Cada persona recibe el aviso por WhatsApp y por el sistema (sin correo, no hay correo).
    assert [m.kind for m in nuevos] == ["aviso"] * 4
    assert sorted(m.channel for m in nuevos) == ["sistema", "sistema", "whatsapp", "whatsapp"]
    assert {m.category for m in nuevos} == {"simulado"}
    assert "simulado" in r.json()["notice"]


def test_quien_se_dio_de_baja_no_recibe_mas_avisos(client):
    _suscribir_y_confirmar(client)
    assert (
        client.post("/api/alerts/subscriptions/unsubscribe", json={"phone": TEL}).status_code == 200
    )
    r = client.post("/api/alerts/send", params={"station_id": 1, "date": DIA}, headers=H)
    assert r.json()["queued"] == 0


def test_darse_de_baja_responde_igual_si_el_numero_no_existe(client):
    r = client.post("/api/alerts/subscriptions/unsubscribe", json={"phone": "+54 370 4999999"})
    assert r.status_code == 200 and r.json()["status"] == "baja"


def test_un_dia_sin_dato_no_manda_nada_aunque_haya_suscriptos(client):
    _suscribir_y_confirmar(client)
    antes = len(_mensajes(client))
    r = client.post(
        "/api/alerts/send",
        params={"station_id": 1, "date": DIA + timedelta(days=2)},
        headers=H,
    )
    assert r.json()["queued"] == 0 and len(_mensajes(client)) == antes


def test_la_bandeja_lista_lo_que_se_enviaria(client):
    _suscribir_y_confirmar(client)
    body = client.get("/api/alerts/outbox", headers=H).json()
    # Código por WhatsApp, y la bienvenida por WhatsApp y por el sistema.
    assert body["total"] == 3 and body["items"][0]["category"] == "simulado"
    assert "simulado" in body["notice"]


# --- canales: WhatsApp, correo y sistema (todo simulado) -------------------------------------

CORREO = "Tomas.Ejemplo@Correo.com"


def test_un_correo_invalido_se_rechaza(client):
    for malo in ("sin-arroba", "a@b", "x@@y.com", "a b@c.com", "a@" + "d" * 300 + ".com"):
        r = client.post("/api/alerts/subscriptions", json={"phone": TEL, "email": malo})
        assert r.status_code == 422, malo


def test_al_registrarse_con_correo_llega_un_correo_simulado_y_el_correo_se_enmascara(client):
    client.post("/api/alerts/subscriptions", json={"phone": TEL, "email": CORREO})
    codigo, correo = _mensajes(client)
    assert (codigo.channel, codigo.kind) == ("whatsapp", "codigo")
    assert (correo.channel, correo.kind) == ("email", "bienvenida")
    assert correo.subject and "registro" in correo.subject
    assert correo.recipient == "t******@correo.com" and "Tomas" not in (correo.recipient or "")
    assert "código" in correo.body and codigo.body.split("es ")[1][:6] not in correo.body
    with client.app.state.session_factory() as db:
        sub = db.scalars(select(AlertSubscription)).one()
        assert sub.email_masked == "t******@correo.com"  # el correo completo no se guarda


def test_sin_correo_no_se_genera_ningun_correo(client):
    client.post("/api/alerts/subscriptions", json={"phone": TEL})
    assert {m.channel for m in _mensajes(client)} == {"whatsapp"}


def test_el_aviso_llega_por_whatsapp_correo_y_sistema(client):
    _suscribir_y_confirmar(client, email=CORREO)
    antes = len(_mensajes(client))
    r = client.post("/api/alerts/send", params={"station_id": 1, "date": DIA}, headers=H)
    assert r.json()["queued"] == 1
    nuevos = _mensajes(client)[antes:]
    assert sorted(m.channel for m in nuevos) == ["email", "sistema", "whatsapp"]
    correo = next(m for m in nuevos if m.channel == "email")
    assert correo.subject and "aviso" in correo.subject.lower()
    assert all("evacuar" in m.body for m in nuevos)  # nunca ordena evacuar, en ningún canal
    assert all(m.category == "simulado" for m in nuevos)


def test_la_confirmacion_manda_la_bienvenida_por_whatsapp_y_por_el_sistema(client):
    _suscribir_y_confirmar(client)
    bienvenidas = [m for m in _mensajes(client) if m.kind == "bienvenida"]
    assert sorted(m.channel for m in bienvenidas) == ["sistema", "whatsapp"]


# --- demostración: ver el propio celular y correo ---------------------------------------------


@pytest.fixture
def demo(tmp_path) -> TestClient:
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url=f"sqlite:///{tmp_path / 'd.db'}",
        admin_api_key=KEY,
        alerts_secret="secreto-de-prueba-para-avisos",  # noqa: S106
        alerts_demo=True,
    )
    app = create_app(settings)
    Base.metadata.create_all(app.state.engine)
    return TestClient(app)


def test_la_vista_de_demostracion_esta_apagada_por_defecto(client):
    client.post("/api/alerts/subscriptions", json={"phone": TEL})
    r = client.post("/api/alerts/inbox", json={"phone": TEL})
    assert r.status_code == 403 and "ALERTS_DEMO" in r.json()["error"]["message"]


def test_en_demostracion_cada_persona_ve_solo_sus_mensajes(demo):
    demo.post("/api/alerts/subscriptions", json={"phone": TEL, "email": CORREO})
    demo.post("/api/alerts/subscriptions", json={"phone": "+54 370 4999888"})
    mio = demo.post("/api/alerts/inbox", json={"phone": TEL}).json()
    assert mio["status"] == "pendiente" and "simulado" in mio["notice"]
    assert [m["channel"] for m in mio["items"]] == ["whatsapp", "email"]
    assert all("8888" not in (m["recipient"] or "") for m in mio["items"])
    otro = demo.post("/api/alerts/inbox", json={"phone": "+54 370 4999888"}).json()
    assert [m["channel"] for m in otro["items"]] == ["whatsapp"]


def test_en_demostracion_un_numero_desconocido_no_ve_nada_ni_se_revela_si_existe(demo):
    r = demo.post("/api/alerts/inbox", json={"phone": "+54 370 4000000"})
    assert r.status_code == 200 and r.json()["items"] == []


def test_la_vista_de_demostracion_valida_el_telefono(demo):
    assert demo.post("/api/alerts/inbox", json={"phone": "abc"}).status_code == 422
