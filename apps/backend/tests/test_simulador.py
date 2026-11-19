"""Simulador de dispositivos (SCRUM-94): lecturas inventadas a propósito y siempre rotuladas."""

from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import Settings
from app.db.base import Base
from app.main import create_app
from app.models import SensorReading
from simulador import __main__ as cli
from simulador.cliente import enviar_lecturas, validar_url
from simulador.generador import MAX_DIAS, MAX_DISPOSITIVOS, generar_lecturas

CORTE = date(2026, 10, 31)
ARGENTINA = timezone(timedelta(hours=-3))


def lecturas(**extra):
    base = {"dispositivos": 3, "dias": 30, "hasta": CORTE, "semilla": 1}
    return list(generar_lecturas(**{**base, **extra}))


def test_es_determinista_con_la_misma_semilla_y_cambia_con_otra():
    assert lecturas(semilla=7) == lecturas(semilla=7)
    assert lecturas(semilla=7) != lecturas(semilla=8)


def test_las_lecturas_respetan_el_contrato_y_el_corte():
    for lectura in lecturas(dispositivos=5, dias=120):
        assert set(lectura) == {"device_id", "read_at", "mm"}  # sin ubicación inventada
        assert isinstance(lectura["mm"], float) and 0 <= lectura["mm"] <= 400
        hora = datetime.fromisoformat(lectura["read_at"])
        assert hora.tzinfo is not None
        assert hora.astimezone(ARGENTINA).hour == 7
        assert hora.astimezone(ARGENTINA).date() <= CORTE


def test_un_dia_sin_reporte_no_se_envia_ni_como_cero_ni_como_vacio():
    todas = lecturas(dispositivos=10, dias=100)
    assert len(todas) < 10 * 100  # algunos días el dispositivo no reportó
    assert all(lectura["mm"] is not None for lectura in todas)
    assert any(lectura["mm"] == 0.0 for lectura in todas)  # un cero medido sí existe
    assert any(lectura["mm"] > 0 for lectura in todas)


def test_el_periodo_termina_en_hasta_y_cubre_los_dias_pedidos():
    horas = [datetime.fromisoformat(x["read_at"]).astimezone(ARGENTINA).date() for x in lecturas()]
    assert max(horas) <= CORTE and min(horas) >= CORTE - timedelta(days=29)


@pytest.mark.parametrize(
    "mal",
    [
        {"dispositivos": 0},
        {"dispositivos": MAX_DISPOSITIVOS + 1},
        {"dias": 0},
        {"dias": MAX_DIAS + 1},
    ],
)
def test_cantidades_fuera_de_rango_se_rechazan(mal):
    with pytest.raises(ValueError):
        lecturas(**mal)


@pytest.mark.parametrize(
    "url", ["", "ftp://x", "file:///etc/passwd", "localhost:8000", "javascript:1"]
)
def test_la_direccion_de_la_api_tiene_que_ser_http(url):
    with pytest.raises(ValueError):
        validar_url(url)


def test_valida_y_arma_la_ruta():
    assert validar_url("http://localhost:8000/") == "http://localhost:8000/api/sensor-readings"


def test_se_detiene_si_la_clave_no_sirve_y_no_sigue_enviando():
    llamadas = []

    def sin_permiso(url, clave, cuerpo):
        llamadas.append(cuerpo)
        return 401, "Falta la clave del dispositivo o es incorrecta."

    resultado = enviar_lecturas(lecturas(), "http://x/api/sensor-readings", "mala", sin_permiso)
    assert resultado.detenido and resultado.creadas == 0 and len(llamadas) == 1
    assert "clave" in resultado.errores[0]


def test_cuenta_nuevas_repetidas_y_rechazadas_sin_cortar_por_un_rechazo():
    codigos = iter([201, 200, 422, 201])

    def falso(url, clave, cuerpo):
        return next(codigos), "no valida"

    cuatro = [
        {"device_id": "SIM-001", "read_at": f"2026-10-2{n}T10:00:00Z", "mm": 1.0} for n in range(4)
    ]
    resultado = enviar_lecturas(cuatro, "http://x", "k", falso)
    assert (resultado.creadas, resultado.repetidas, resultado.rechazadas) == (2, 1, 1)
    assert not resultado.detenido


@pytest.fixture
def api(tmp_path):
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url=f"sqlite:///{tmp_path / 'sim.db'}",
        device_api_key="clave-sim",
    )
    app = create_app(settings)
    Base.metadata.create_all(app.state.engine)
    return TestClient(app)


def test_de_punta_a_punta_entran_como_simulado_y_reenviar_no_duplica(api):
    def por_la_api(url, clave, cuerpo):
        r = api.post("/api/sensor-readings", json=cuerpo, headers={"X-Device-Key": clave})
        return r.status_code, ""

    generadas = lecturas(dispositivos=2, dias=10)
    primera = enviar_lecturas(generadas, "x", "clave-sim", por_la_api)
    assert primera.creadas == len(generadas) and primera.rechazadas == 0

    with api.app.state.session_factory() as db:
        filas = db.scalars(select(SensorReading)).all()
    assert len(filas) == len(generadas)
    assert {f.category.value for f in filas} == {"simulado"}
    assert {f.source for f in filas} == {"sensor_simulado"}

    segunda = enviar_lecturas(generadas, "x", "clave-sim", por_la_api)
    assert (segunda.creadas, segunda.repetidas) == (0, len(generadas))


def test_sin_clave_el_comando_no_envia_nada(monkeypatch, capsys):
    monkeypatch.setattr(cli, "get_settings", lambda: Settings(_env_file=None, device_api_key=None))
    assert cli.main(["--dias", "1"]) == 2
    assert "DEVICE_API_KEY" in capsys.readouterr().err


def test_el_comando_no_pasa_del_corte(monkeypatch, capsys):
    monkeypatch.setattr(cli, "get_settings", lambda: Settings(_env_file=None, device_api_key="k"))
    assert cli.main(["--hasta", "2026-11-05"]) == 2
    assert "corte" in capsys.readouterr().err


def test_el_comando_rechaza_una_direccion_que_no_es_http(monkeypatch, capsys):
    monkeypatch.setattr(cli, "get_settings", lambda: Settings(_env_file=None, device_api_key="k"))
    assert cli.main(["--url", "file:///etc/passwd"]) == 2
    assert "http" in capsys.readouterr().err
