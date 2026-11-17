def test_health_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["env"] == "test"
    assert body["data_cutoff_date"] == "2026-10-31"


def test_health_no_expone_configuracion_sensible(client):
    body = client.get("/health").json()
    assert "database_url" not in body
    assert "admin_api_key" not in body
