"""Cuentas: registro, inicio de sesión, roles y quién cargó qué."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import Settings
from app.db.base import Base
from app.domain.auth import (
    Role,
    hash_password,
    token_digest,
    validate_password,
    verify_password,
)
from app.main import create_app
from app.models import AuthSession, FieldReport, ImportLog, User

KEY = "clave-admin-de-prueba"
CLAVE = "una-clave-larga-1"
REPORTE = {
    "obs_date": "2026-10-20",
    "mm": 35.5,
    "place": "Comisaría de Laguna Yema",
    "reporter": "Agente Pérez",
}
ESTACIONES = (
    "estacion_id,id_interno,nombre,tipo,localidad,provincia,lat,lon,altura_m,desde_siga,hasta_siga\n"
    "424,A1,El Colorado,Automática,Pirané,Formosa,-26.33,-59.35,106,2013-10-07,2022-12-07\n"
)
LLUVIA = (
    "estacion_id,estacion,fecha,mm_pluviometrica,mm_cronologica,unidad,estado,bandera,"
    "categoria,fuente\n424,x,2016-01-01,12.5,,mm,dato,,OBSERVADO,SIGA\n"
)


def _cliente(tmp_path, **extra) -> TestClient:
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url=f"sqlite:///{tmp_path / 'u.db'}",
        admin_api_key=KEY,
        rate_limit_per_minute=0,
        rate_limit_auth_per_minute=0,
        **extra,
    )
    app = create_app(settings)
    Base.metadata.create_all(app.state.engine)
    return TestClient(app)


@pytest.fixture
def client(tmp_path) -> TestClient:
    return _cliente(tmp_path)


def registrar(client, email="ana@correo.com", password=CLAVE, **extra):
    return client.post("/api/auth/register", json={"email": email, "password": password, **extra})


def ingresar(client, email="ana@correo.com", password=CLAVE) -> dict:
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def con_rol(client, email: str, rol: Role) -> str:
    """Crea una cuenta, le asigna el rol directo en la base y devuelve un token vigente."""
    registrar(client, email)
    with client.app.state.session_factory() as db:
        db.scalars(select(User).where(User.email == email)).one().role = rol
        db.commit()
    return ingresar(client, email)["token"]


# --- dominio --------------------------------------------------------------------------------


def test_la_contrasena_se_guarda_con_sal_y_se_verifica():
    uno, otro = hash_password(CLAVE), hash_password(CLAVE)
    assert uno != otro and CLAVE not in uno  # sal distinta en cada alta y nunca en claro
    assert verify_password(CLAVE, uno) and not verify_password("otra-clave-larga", uno)


@pytest.mark.parametrize("malo", ["", "scrypt", "scrypt$1$2", "md5$a$b$c$d$e", "scrypt$x$1$1$a$b"])
def test_un_hash_mal_formado_nunca_verifica(malo):
    assert verify_password(CLAVE, malo) is False


@pytest.mark.parametrize(
    "clave", ["corta", "a" * 129, " con-espacios-al-borde ", "ana@correo.com", "ana"]
)
def test_una_contrasena_floja_se_rechaza(clave):
    with pytest.raises(ValueError):
        validate_password(clave, "ana@correo.com")


# --- registro -------------------------------------------------------------------------------


def test_el_registro_crea_un_ciudadano_y_nunca_devuelve_la_contrasena(client):
    r = registrar(client, display_name="  Ana  ")
    body = r.json()
    assert r.status_code == 201 and body["role"] == "ciudadano" and body["display_name"] == "Ana"
    assert CLAVE not in r.text and "password" not in body and "password_hash" not in body
    with client.app.state.session_factory() as db:
        usuario = db.scalars(select(User)).one()
        assert usuario.password_hash.startswith("scrypt$") and CLAVE not in usuario.password_hash


def test_quien_se_registra_no_puede_elegir_su_rol(client):
    for extra in ({"role": "administrador"}, {"is_active": True}, {"id": 1}):
        assert registrar(client, **extra).status_code == 422


def test_el_correo_se_normaliza_y_no_se_repite(client):
    assert registrar(client, "Ana@Correo.com").json()["email"] == "ana@correo.com"
    r = registrar(client, "ANA@correo.com")
    assert r.status_code == 409 and r.json()["error"]["code"] == "email_taken"


@pytest.mark.parametrize("correo", ["", "sin-arroba", "a@b", "x@@y.com", "a b@c.com"])
def test_un_correo_invalido_se_rechaza(client, correo):
    assert registrar(client, correo).status_code == 422


def test_una_contrasena_floja_se_rechaza_con_el_motivo(client):
    r = registrar(client, password="corta")  # noqa: S106
    assert r.status_code == 422 and "al menos 10" in r.json()["error"]["message"]
    assert registrar(client, password="ana@correo.com").status_code == 422  # noqa: S106


def test_con_el_registro_cerrado_no_se_pueden_crear_cuentas(tmp_path):
    cerrado = _cliente(tmp_path, registration_open=False)
    assert registrar(cerrado).status_code == 403


# --- inicio de sesión -----------------------------------------------------------------------


def test_iniciar_sesion_devuelve_un_token_que_en_la_base_solo_esta_resumido(client):
    registrar(client)
    sesion = ingresar(client)
    assert sesion["user"]["email"] == "ana@correo.com" and sesion["token"]
    with client.app.state.session_factory() as db:
        guardada = db.scalars(select(AuthSession)).one()
        assert guardada.token_hash == token_digest(sesion["token"])
        assert sesion["token"] not in guardada.token_hash


def test_no_se_distingue_un_correo_inexistente_de_una_clave_incorrecta(client):
    registrar(client)
    mala = client.post("/api/auth/login", json={"email": "ana@correo.com", "password": "x" * 12})
    nada = client.post("/api/auth/login", json={"email": "nadie@correo.com", "password": "x" * 12})
    assert mala.status_code == nada.status_code == 401
    assert mala.json() == nada.json() and "incorrectos" in mala.json()["error"]["message"]


def test_tras_5_intentos_fallidos_la_cuenta_se_bloquea_aun_con_la_clave_correcta(client):
    registrar(client)
    for _ in range(5):
        r = client.post("/api/auth/login", json={"email": "ana@correo.com", "password": "x" * 12})
        assert r.status_code == 401
    r = client.post("/api/auth/login", json={"email": "ana@correo.com", "password": CLAVE})
    assert r.status_code == 429 and r.json()["error"]["code"] == "account_locked"


def test_el_bloqueo_vence(client):
    registrar(client)
    for _ in range(5):
        client.post("/api/auth/login", json={"email": "ana@correo.com", "password": "x" * 12})
    with client.app.state.session_factory() as db:
        db.scalars(select(User)).one().locked_until = datetime.now(UTC) - timedelta(minutes=1)
        db.commit()
    assert ingresar(client)["token"]


def test_un_ingreso_correcto_reinicia_el_conteo_de_fallos(client):
    registrar(client)
    for _ in range(4):
        client.post("/api/auth/login", json={"email": "ana@correo.com", "password": "x" * 12})
    ingresar(client)
    for _ in range(4):
        client.post("/api/auth/login", json={"email": "ana@correo.com", "password": "x" * 12})
    assert ingresar(client)["token"]  # 4 + 4 no bloquean porque el conteo se reinició


def test_una_cuenta_desactivada_no_puede_ingresar(client):
    registrar(client)
    with client.app.state.session_factory() as db:
        db.scalars(select(User)).one().is_active = False
        db.commit()
    r = client.post("/api/auth/login", json={"email": "ana@correo.com", "password": CLAVE})
    assert r.status_code == 401


def test_la_ruta_de_ingreso_no_acepta_campos_de_mas(client):
    r = client.post("/api/auth/login", json={"email": "a@b.co", "password": "x" * 12, "role": "x"})
    assert r.status_code == 422


# --- sesión ---------------------------------------------------------------------------------


def test_me_devuelve_la_cuenta_y_sin_sesion_pide_ingresar(client):
    registrar(client)
    token = ingresar(client)["token"]
    assert client.get("/api/auth/me", headers=bearer(token)).json()["email"] == "ana@correo.com"
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers=bearer("token-inventado")).status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Basic abc"}).status_code == 401


def test_cerrar_sesion_revoca_el_token(client):
    registrar(client)
    token = ingresar(client)["token"]
    assert client.post("/api/auth/logout", headers=bearer(token)).status_code == 204
    assert client.get("/api/auth/me", headers=bearer(token)).status_code == 401
    assert client.post("/api/auth/logout").status_code == 204  # sin sesión no falla


def test_un_token_vencido_no_sirve(client):
    registrar(client)
    token = ingresar(client)["token"]
    with client.app.state.session_factory() as db:
        db.scalars(select(AuthSession)).one().expires_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()
    assert client.get("/api/auth/me", headers=bearer(token)).status_code == 401


# --- roles ----------------------------------------------------------------------------------


def test_un_ciudadano_no_puede_cargar_datos_ni_con_sesion(client):
    registrar(client)
    token = ingresar(client)["token"]
    r = client.post("/api/field-reports", json=REPORTE, headers=bearer(token))
    assert r.status_code == 403 and r.json()["error"]["code"] == "forbidden"


def test_un_operador_carga_un_reporte_y_queda_registrado_quien_fue(client):
    token = con_rol(client, "olga@correo.com", Role.OPERADOR)
    r = client.post("/api/field-reports", json=REPORTE, headers=bearer(token))
    assert r.status_code == 201
    with client.app.state.session_factory() as db:
        reporte = db.scalars(select(FieldReport)).one()
        operador = db.scalars(select(User).where(User.email == "olga@correo.com")).one()
        assert reporte.created_by_user_id == operador.id


def test_la_clave_de_administracion_sigue_funcionando_y_no_deja_autor(client):
    r = client.post("/api/field-reports", json=REPORTE, headers={"X-API-Key": KEY})
    assert r.status_code == 201
    with client.app.state.session_factory() as db:
        assert db.scalars(select(FieldReport)).one().created_by_user_id is None


def test_sin_sesion_ni_clave_la_escritura_se_rechaza(client):
    assert client.post("/api/field-reports", json=REPORTE).status_code == 401
    r = client.post("/api/field-reports", json=REPORTE, headers=bearer("token-inventado"))
    assert r.status_code == 401


def test_una_sesion_de_ciudadano_junto_con_la_clave_correcta_si_pasa(client):
    registrar(client)
    token = ingresar(client)["token"]
    headers = {**bearer(token), "X-API-Key": KEY}
    assert client.post("/api/field-reports", json=REPORTE, headers=headers).status_code == 201


def test_una_importacion_registra_quien_la_hizo(client):
    token = con_rol(client, "olga@correo.com", Role.OPERADOR)
    headers = {**bearer(token), "Content-Type": "text/csv"}
    for tipo, cuerpo in (("stations", ESTACIONES), ("rainfall", LLUVIA)):
        r = client.post(
            "/api/import/commit",
            params={"kind": tipo, "filename": "datos.csv"},
            content=cuerpo.encode(),
            headers=headers,
        )
        assert r.status_code == 200, r.text
    with client.app.state.session_factory() as db:
        log = db.scalars(select(ImportLog)).one()
        assert log.created_by_user_id is not None
    historial = client.get("/api/import/logs", headers=bearer(token)).json()
    assert historial[0]["created_by_user_id"] == log.created_by_user_id


# --- gestión de cuentas ---------------------------------------------------------------------


def test_solo_un_administrador_lista_y_cambia_cuentas(client):
    admin = con_rol(client, "root@correo.com", Role.ADMINISTRADOR)
    operador = con_rol(client, "olga@correo.com", Role.OPERADOR)
    ciudadano = (
        registrar(client, "cris@correo.com"),
        ingresar(client, "cris@correo.com")["token"],
    )[1]
    assert client.get("/api/users").status_code == 401
    assert client.get("/api/users", headers=bearer(ciudadano)).status_code == 403
    assert client.get("/api/users", headers=bearer(operador)).status_code == 403
    assert (
        client.get("/api/users", headers={"X-API-Key": KEY}).status_code == 401
    )  # no alcanza la clave
    lista = client.get("/api/users", headers=bearer(admin)).json()
    assert lista["total"] == 3 and "password_hash" not in str(lista)


def test_el_administrador_asciende_a_un_ciudadano_a_operador(client):
    admin = con_rol(client, "root@correo.com", Role.ADMINISTRADOR)
    registrar(client, "cris@correo.com")
    cris = ingresar(client, "cris@correo.com")["token"]
    objetivo = client.get("/api/users", headers=bearer(admin)).json()["items"][-1]["id"]
    r = client.patch(f"/api/users/{objetivo}", json={"role": "operador"}, headers=bearer(admin))
    assert r.status_code == 200 and r.json()["role"] == "operador"
    # El permiso cambió: la sesión vieja se cierra y tiene que ingresar de nuevo.
    assert client.get("/api/auth/me", headers=bearer(cris)).status_code == 401
    nuevo = ingresar(client, "cris@correo.com")["token"]
    assert client.post("/api/field-reports", json=REPORTE, headers=bearer(nuevo)).status_code == 201


def test_desactivar_una_cuenta_cierra_sus_sesiones(client):
    admin = con_rol(client, "root@correo.com", Role.ADMINISTRADOR)
    registrar(client, "cris@correo.com")
    cris = ingresar(client, "cris@correo.com")["token"]
    objetivo = client.get("/api/users", headers=bearer(admin)).json()["items"][-1]["id"]
    client.patch(f"/api/users/{objetivo}", json={"is_active": False}, headers=bearer(admin))
    assert client.get("/api/auth/me", headers=bearer(cris)).status_code == 401


def test_un_administrador_no_puede_cambiarse_a_si_mismo(client):
    admin = con_rol(client, "root@correo.com", Role.ADMINISTRADOR)
    yo = client.get("/api/auth/me", headers=bearer(admin)).json()["id"]
    for cambio in ({"role": "ciudadano"}, {"is_active": False}):
        r = client.patch(f"/api/users/{yo}", json=cambio, headers=bearer(admin))
        assert r.status_code == 409 and r.json()["error"]["code"] == "cannot_modify_self"


def test_entradas_invalidas_al_cambiar_una_cuenta(client):
    admin = con_rol(client, "root@correo.com", Role.ADMINISTRADOR)
    h = bearer(admin)
    assert client.patch("/api/users/9999", json={"role": "operador"}, headers=h).status_code == 404
    assert client.patch("/api/users/0", json={"role": "operador"}, headers=h).status_code == 422
    assert client.patch("/api/users/2", json={"role": "dios"}, headers=h).status_code == 422
    # Solo se puede cambiar el rol y si está activa: nada de contraseñas ni correos ajenos.
    r = client.patch("/api/users/2", json={"password": "otra-clave-larga"}, headers=h)
    assert r.status_code == 422


# --- línea de comandos ----------------------------------------------------------------------


def test_create_user_crea_el_primer_administrador_con_la_clave_del_entorno(
    tmp_path, monkeypatch, capsys
):
    from app import cli
    from app.config import get_settings

    url = f"sqlite:///{tmp_path / 'cli.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("PLUVIFOR_NEW_USER_PASSWORD", CLAVE)
    get_settings.cache_clear()
    try:
        app = create_app(Settings(_env_file=None, app_env="test", database_url=url))
        Base.metadata.create_all(app.state.engine)
        assert cli.main(["create-user", "--email", "Root@Correo.com"]) == 0
        assert "administrador" in capsys.readouterr().out
        sesion = TestClient(app).post(
            "/api/auth/login", json={"email": "root@correo.com", "password": CLAVE}
        )
        assert sesion.status_code == 200 and sesion.json()["user"]["role"] == "administrador"
        assert cli.main(["create-user", "--email", "root@correo.com"]) == 1  # ya existe
        assert "Ya hay una cuenta" in capsys.readouterr().err
    finally:
        get_settings.cache_clear()


def test_create_user_rechaza_una_clave_floja_y_un_correo_invalido(tmp_path, monkeypatch, capsys):
    from app import cli
    from app.config import get_settings

    url = f"sqlite:///{tmp_path / 'cli2.db'}"
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    try:
        app = create_app(Settings(_env_file=None, app_env="test", database_url=url))
        Base.metadata.create_all(app.state.engine)
        monkeypatch.setenv("PLUVIFOR_NEW_USER_PASSWORD", "corta")
        assert cli.main(["create-user", "--email", "a@correo.com"]) == 1
        assert "al menos 10" in capsys.readouterr().err
        monkeypatch.setenv("PLUVIFOR_NEW_USER_PASSWORD", CLAVE)
        assert cli.main(["create-user", "--email", "no-es-un-correo"]) == 1
        assert "Error" in capsys.readouterr().err
    finally:
        get_settings.cache_clear()
