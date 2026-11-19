"""POST /api/import/audit y /commit (SCRUM-48)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.config import Settings
from app.db.base import Base
from app.main import create_app
from app.models import ImportLog, RainfallRecord, Station

KEY = "clave-de-prueba-larga"
AUTH = {"X-API-Key": KEY}
STATIONS = (
    "estacion_id,id_interno,nombre,tipo,localidad,provincia,lat,lon,altura_m,desde_siga,hasta_siga\n"
    "424,A1,El Colorado,Automática,Pirané,Formosa,-26.33,-59.35,106,2013-10-07,2022-12-07\n"
)
HEADER = (
    "estacion_id,estacion,fecha,mm_pluviometrica,mm_cronologica,unidad,estado,bandera,"
    "categoria,fuente\n"
)
GOOD = "424,x,2016-01-01,12.5,,mm,dato,,OBSERVADO,SIGA\n"
GAP = "424,x,2016-01-02,,,mm,fila_sin_valor,,OBSERVADO,SIGA\n"
BAD = "424,x,2016-01-03,-4,,mm,dato,,OBSERVADO,SIGA\n"


@pytest.fixture
def client(tmp_path) -> TestClient:
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_url=f"sqlite:///{tmp_path / 't.db'}",
        admin_api_key=KEY,
        max_upload_bytes=10_000,
    )
    app = create_app(settings)
    Base.metadata.create_all(app.state.engine)
    return TestClient(app)


def post(client, action, body, kind="rainfall", name="datos.csv", headers=AUTH):
    return client.post(
        f"/api/import/{action}",
        params={"kind": kind, "filename": name},
        content=body if isinstance(body, bytes) else body.encode(),
        headers={"Content-Type": "text/csv", **headers},
    )


def load_stations(client):
    assert post(client, "commit", STATIONS, kind="stations", name="e.csv").status_code == 200


def counts(client) -> tuple[int, int, int]:
    with client.app.state.session_factory() as db:  # type: Session
        return tuple(
            db.scalar(select(func.count()).select_from(m))
            for m in (Station, RainfallRecord, ImportLog)
        )


def test_writing_routes_need_the_key(client):
    assert post(client, "audit", HEADER, headers={}).status_code == 401
    assert post(client, "commit", HEADER, headers={}).status_code == 401


def test_valid_file_goes_in_and_is_recorded(client):
    load_stations(client)
    response = post(client, "commit", HEADER + GOOD + GAP)
    body = response.json()
    assert response.status_code == 200
    assert (body["rows_read"], body["rows_accepted"], body["rows_rejected"]) == (2, 2, 0)
    assert body["saved"] is True and body["inserted"] == 2
    stations, records, logs = counts(client)
    assert (stations, records, logs) == (1, 2, 1)


def test_the_gap_is_stored_without_millimeters_never_zero(client):
    load_stations(client)
    post(client, "commit", HEADER + GAP)
    with client.app.state.session_factory() as db:
        record = db.scalar(select(RainfallRecord))
        assert record.mm is None and record.state.value == "fila_sin_valor"


def test_invalid_rows_are_rejected_with_a_reason_in_spanish_and_logged(client):
    load_stations(client)
    body = post(client, "commit", HEADER + GOOD + BAD).json()
    assert (body["rows_accepted"], body["rows_rejected"]) == (1, 1)
    assert body["rejections_by_reason"] == {"mm_negativo": 1}
    assert body["rejections"][0]["line"] == 3
    assert "negativos" in body["rejections"][0]["message"]
    with client.app.state.session_factory() as db:
        log = db.scalar(select(ImportLog))
        assert log.rows_rejected == 1 and "mm_negativo" in log.rejections


def test_audit_returns_the_report_without_touching_the_database(client):
    load_stations(client)
    before = counts(client)
    body = post(client, "audit", HEADER + GOOD + BAD).json()
    assert body["mode"] == "audit" and body["saved"] is False
    assert (body["rows_accepted"], body["rows_rejected"]) == (1, 1)
    assert counts(client) == before


def test_audit_of_stations_does_not_create_anything(client):
    body = post(client, "audit", STATIONS, kind="stations", name="e.csv").json()
    assert body["rows_accepted"] == 1 and body["saved"] is False
    assert counts(client) == (0, 0, 0)


def test_repeating_the_same_upload_does_not_duplicate_rows(client):
    load_stations(client)
    first = post(client, "commit", HEADER + GOOD).json()
    second = post(client, "commit", HEADER + GOOD).json()
    assert (first["inserted"], first["updated"]) == (1, 0)
    assert (second["inserted"], second["updated"]) == (0, 1)
    assert first["sha256"] == second["sha256"]
    assert counts(client)[1] == 1


def test_rainfall_before_the_catalog_is_an_error_not_a_crash(client):
    response = post(client, "audit", HEADER + GOOD)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_file"


@pytest.mark.parametrize(
    ("body", "name", "status"),
    [
        (b"PK\x03\x04" + b"x" * 20, "datos.csv", 422),
        (HEADER.encode(), "datos.xlsx", 422),
        (b"a,b\n1,2\n", "datos.csv", 422),  # faltan columnas
        (b"x" * 10_001, "datos.csv", 413),
    ],
)
def test_bad_files_are_rejected_and_nothing_is_saved(client, body, name, status):
    load_stations(client)
    before = counts(client)
    response = post(client, "commit", body, name=name)
    assert response.status_code == status
    assert counts(client) == before


def test_unknown_source_does_not_echo_what_was_sent(client):
    response = client.post(
        "/api/import/audit",
        params={"source": "inexistente"},
        content=HEADER.encode(),
        headers=AUTH,
    )
    assert response.status_code == 422
    assert "inexistente" not in response.text


def test_source_with_strange_characters_is_a_validation_error(client):
    response = client.post(
        "/api/import/audit", params={"source": "x'; DROP TABLE a;--"}, content=b"", headers=AUTH
    )
    assert response.status_code == 422


class TestHistorial:
    def test_sin_cargas_devuelve_lista_vacia(self, client):
        response = client.get("/api/import/logs", headers=AUTH)
        assert response.status_code == 200
        assert response.json() == []

    def test_lista_las_cargas_confirmadas_la_mas_nueva_primero(self, client):
        load_stations(client)
        post(client, "commit", HEADER + GOOD + BAD, name="primera.csv")
        post(client, "commit", HEADER + GAP, name="segunda.csv")
        items = client.get("/api/import/logs", headers=AUTH).json()
        assert [i["filename"] for i in items][:2] == ["segunda.csv", "primera.csv"]
        primera = items[1]
        assert primera["rows_read"] == 2
        assert primera["rows_accepted"] == 1
        assert primera["rows_rejected"] == 1
        assert primera["rejections_by_reason"] == {"mm_negativo": 1}
        assert primera["source"] == "siga_inta"
        assert primera["mode"] == "commit"

    def test_una_auditoria_no_deja_registro(self, client):
        load_stations(client)
        before = len(client.get("/api/import/logs", headers=AUTH).json())
        post(client, "audit", HEADER + GOOD, name="solo_auditoria.csv")
        assert len(client.get("/api/import/logs", headers=AUTH).json()) == before

    def test_respeta_el_limite(self, client):
        load_stations(client)
        for n in range(3):
            post(client, "commit", HEADER + GOOD, name=f"c{n}.csv")
        assert len(client.get("/api/import/logs", params={"limit": 2}, headers=AUTH).json()) == 2

    @pytest.mark.parametrize("limit", [0, 101, "abc"])
    def test_limite_invalido_se_rechaza(self, client, limit):
        response = client.get("/api/import/logs", params={"limit": limit}, headers=AUTH)
        assert response.status_code == 422

    def test_exige_la_clave_de_administracion(self, client):
        assert client.get("/api/import/logs").status_code == 401
        assert client.get("/api/import/logs", headers={"X-API-Key": "otra"}).status_code == 401
