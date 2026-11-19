"""GET /api/network/health (SCRUM-89): activas, en silencio y sin datos. Un silencio no es 0 mm."""

from datetime import date, timedelta

import pytest
from sqlalchemy.orm import Session

from app.domain.enums import DataCategory, RainState, Validation
from app.domain.network_health import NetworkState, classify
from app.models import RainfallRecord, Source, Station

CUTOFF = date(2026, 10, 31)


def dia(db, station_id, obs_date, state, mm, category=DataCategory.OBSERVADO):
    db.add(
        RainfallRecord(
            station_id=station_id, obs_date=obs_date, state=state, mm=mm,
            category=category, validation=Validation.SIN_VALIDAR,
        )
    )  # fmt: skip


@pytest.fixture
def red(db: Session) -> dict[str, int]:
    src = Source(code="s", name="S", network="Red", category=DataCategory.OBSERVADO)
    db.add(src)
    db.flush()
    ids = {}
    for code in ("activa0", "activa_limite", "silencio", "vacia", "huecos", "solo_ref"):
        st = Station(source_id=src.id, code=code, name=f"E {code}")
        db.add(st)
        db.flush()
        ids[code] = st.id
    # Activa con un 0 real el último día: es lluvia cero medida, no silencio.
    dia(db, ids["activa0"], CUTOFF, RainState.DATO, 0.0)
    # Justo en el límite (30 días): todavía activa.
    dia(db, ids["activa_limite"], CUTOFF - timedelta(days=30), RainState.DATO, 4.5)
    # Silencio: última lectura hace 31 días; después solo filas sin valor.
    dia(db, ids["silencio"], CUTOFF - timedelta(days=31), RainState.DATO, 12.0)
    for n in range(1, 10):
        dia(db, ids["silencio"], CUTOFF - timedelta(days=n), RainState.FILA_SIN_VALOR, None)
    # Solo huecos: sin datos (no 0 mm).
    dia(db, ids["huecos"], CUTOFF, RainState.FILA_SIN_VALOR, None)
    # Una referencia reciente no cuenta como lectura observada.
    dia(db, ids["solo_ref"], CUTOFF, RainState.DATO, 9.0, DataCategory.REFERENCIA)
    # Un dato posterior al corte no se usa.
    dia(db, ids["vacia"], CUTOFF + timedelta(days=5), RainState.DATO, 3.0)
    db.commit()
    return ids


def por_codigo(body):
    return {s["code"]: s for s in body["stations"]}


def test_clasifica_activa_en_silencio_y_sin_datos(client, red):
    body = client.get("/api/network/health").json()
    est = por_codigo(body)
    assert est["activa0"]["state"] == "activa"
    assert est["activa_limite"]["state"] == "activa"
    assert est["silencio"]["state"] == "en_silencio"
    for sin in ("vacia", "huecos", "solo_ref"):
        assert est[sin]["state"] == "sin_datos"
    assert (body["active"], body["silent"], body["no_data"]) == (2, 1, 3)
    assert body["category"] == "observado" and body["data_cutoff_date"] == "2026-10-31"


def test_un_cero_real_se_distingue_de_un_silencio(client, red):
    est = por_codigo(client.get("/api/network/health").json())
    assert est["activa0"]["last_reading_mm"] == 0.0 and est["activa0"]["days_since_last"] == 0
    # El silencio muestra su última lectura real (12 mm, hace 31 días), jamás un 0 de hoy.
    assert est["silencio"]["last_reading_mm"] == 12.0 and est["silencio"]["days_since_last"] == 31
    # Sin datos: todo vacío (null), no 0.
    assert est["huecos"]["last_reading_mm"] is None
    assert est["huecos"]["last_reading_date"] is None and est["huecos"]["days_since_last"] is None


def test_el_umbral_se_puede_cambiar_por_consulta(client, red):
    body = client.get("/api/network/health", params={"silent_after_days": 60}).json()
    assert por_codigo(body)["silencio"]["state"] == "activa"
    assert body["silent_after_days"] == 60


@pytest.mark.parametrize("valor", ["0", "-3", "366", "abc"])
def test_umbral_invalido_se_rechaza(client, valor):
    r = client.get("/api/network/health", params={"silent_after_days": valor})
    assert r.status_code == 422
    assert r.json()["error"]["code"]


def test_base_vacia_devuelve_listas_vacias(client):
    body = client.get("/api/network/health").json()
    assert (body["active"], body["silent"], body["no_data"], body["stations"]) == (0, 0, 0, [])


def test_classify_unitario():
    assert classify(None, CUTOFF, 30).state is NetworkState.SIN_DATOS
    assert classify(CUTOFF - timedelta(days=30), CUTOFF, 30).state is NetworkState.ACTIVA
    assert classify(CUTOFF - timedelta(days=31), CUTOFF, 30).state is NetworkState.EN_SILENCIO
