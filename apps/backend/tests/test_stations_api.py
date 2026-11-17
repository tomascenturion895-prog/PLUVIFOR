import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.enums import CoordsStatus, DataCategory
from app.models import Source, Station


@pytest.fixture
def seeded(db: Session) -> None:
    siga = Source(
        code="siga_inta",
        name="SIGA INTA",
        network="INTA",
        category=DataCategory.OBSERVADO,
        day_cutoff_local="09:00",
    )
    prov = Source(
        code="provincial",
        name="Red provincial",
        network="Provincial",
        category=DataCategory.OBSERVADO,
    )
    db.add_all([siga, prov])
    db.flush()
    db.add_all(
        [
            Station(
                source_id=siga.id,
                code="424",
                name="El Colorado - EEA",
                locality="Pirané",
                lat=-26.33,
                lon=-59.35,
                coords_status=CoordsStatus.VERIFICADA,
            ),
            Station(source_id=siga.id, code="425", name="Bartolomé de las Casas", locality="BDLC"),
            Station(source_id=prov.id, code="P1", name="Clorinda", department="Pilcomayo"),
        ]
    )
    db.commit()


def test_lists_all_stations_with_source(client: TestClient, seeded: None) -> None:
    body = client.get("/stations").json()
    assert body["total"] == 3
    first = body["items"][0]
    assert first["source"]["category"] == "observado"
    assert "code" in first["source"]


def test_pending_coordinates_are_null_not_zero(client: TestClient, seeded: None) -> None:
    items = client.get("/stations", params={"q": "bartolom"}).json()["items"]
    assert len(items) == 1
    assert items[0]["lat"] is None and items[0]["lon"] is None
    assert items[0]["coords_status"] == "pendiente"


def test_filters_by_source(client: TestClient, seeded: None) -> None:
    body = client.get("/stations", params={"source": "provincial"}).json()
    assert [s["code"] for s in body["items"]] == ["P1"]


def test_filters_by_coords_status(client: TestClient, seeded: None) -> None:
    body = client.get("/stations", params={"coords_status": "verificada"}).json()
    assert body["total"] == 1


def test_pagination(client: TestClient, seeded: None) -> None:
    body = client.get("/stations", params={"limit": 2, "offset": 2}).json()
    assert body["total"] == 3
    assert len(body["items"]) == 1


def test_station_detail(client: TestClient, seeded: None) -> None:
    station_id = client.get("/stations", params={"q": "colorado"}).json()["items"][0]["id"]
    body = client.get(f"/stations/{station_id}").json()
    assert body["code"] == "424"
    assert body["source"]["day_cutoff_local"] == "09:00"


def test_unknown_station_is_404_in_spanish(client: TestClient, seeded: None) -> None:
    response = client.get("/stations/9999")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "station_not_found"


@pytest.mark.parametrize(
    "params", [{"limit": 0}, {"limit": 1000}, {"offset": -1}, {"coords_status": "inventada"}]
)
def test_invalid_query_is_rejected(client: TestClient, params: dict) -> None:
    assert client.get("/stations", params=params).status_code == 422


def test_search_text_is_not_executed_as_sql(client: TestClient, seeded: None) -> None:
    response = client.get("/stations", params={"q": "'; DROP TABLE stations; --"})
    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert client.get("/stations").json()["total"] == 3
