"""Estimación de días sin dato (SCRUM-93): se guarda como estimado y no se suma a lo observado."""

from datetime import date, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import cli
from app.config import get_settings
from app.domain.enums import CoordsStatus, DataCategory, RainState, Severity, Validation
from app.models import GapEstimate, QualityFlag, RainfallRecord, Source, Station
from app.repositories.gap_estimates import SqlGapEstimateRepository
from app.services.gap_estimation import GapEstimationService

D1 = date(2020, 1, 1)
CORTE = date(2026, 10, 31)


def dia(n: int) -> date:
    return D1 + timedelta(days=n - 1)


def estacion(db, fuente, codigo, lat, lon, kind="Convencional", coords=CoordsStatus.VERIFICADA):
    est = Station(
        source_id=fuente.id,
        code=codigo,
        name=f"Estación {codigo}",
        kind=kind,
        lat=lat if coords == CoordsStatus.VERIFICADA else None,
        lon=lon if coords == CoordsStatus.VERIFICADA else None,
        coords_status=coords,
    )
    db.add(est)
    db.flush()
    return est


def cargar(db, est, plan: dict[int, float | str | None], categoria=DataCategory.OBSERVADO):
    """plan: día -> mm (dato), 'sin_fila' o 'sin_valor'."""
    for n, valor in plan.items():
        if valor == "sin_fila":
            estado, mm = RainState.SIN_FILA, None
        elif valor == "sin_valor":
            estado, mm = RainState.FILA_SIN_VALOR, None
        else:
            estado, mm = RainState.DATO, valor
        db.add(
            RainfallRecord(
                station_id=est.id,
                obs_date=dia(n),
                state=estado,
                mm=mm,
                category=categoria,
                validation=Validation.VALIDADO,
            )
        )


@pytest.fixture
def mundo(db: Session):
    fuente = Source(
        code="siga_inta",
        name="SIGA",
        network="INTA",
        category=DataCategory.OBSERVADO,
        day_cutoff_local="09:00",
    )
    db.add(fuente)
    db.flush()
    a = estacion(db, fuente, "A", -26.30, -59.38)  # la que tiene huecos
    b = estacion(db, fuente, "B", -26.33, -59.35)  # vecina del mismo tipo, a ~4,5 km
    c = estacion(db, fuente, "C", -26.31, -59.37, kind="Automática (Nimbus THP)")  # otro tipo
    lejana = estacion(db, fuente, "D", -25.40, -59.50)  # mismo tipo pero a ~100 km
    # A mide los días 1 a 10, salvo el 4 (sin fila) y el 5 (fila sin valor).
    cargar(
        db,
        a,
        {
            1: 0.0,
            2: 1.0,
            3: 2.0,
            4: "sin_fila",
            5: "sin_valor",
            6: 0.0,
            7: 0.0,
            8: 3.0,
            9: 0.0,
            10: 0.0,
        },
    )
    cargar(db, b, {4: 10.0, 5: 20.0, 6: 0.0})
    cargar(db, c, {4: 99.0, 5: 99.0})
    cargar(db, lejana, {4: 77.0, 5: 77.0})
    db.commit()
    return a, b, c, lejana


def servicio(db) -> GapEstimationService:
    return GapEstimationService(SqlGapEstimateRepository(db), CORTE)


def estimaciones(db) -> dict[date, GapEstimate]:
    return {
        e.obs_date: e for e in db.scalars(select(GapEstimate).where(GapEstimate.station_id == 1))
    }


def test_estima_los_huecos_solo_con_la_vecina_del_mismo_tipo_y_cercana(db, mundo):
    r = servicio(db).run(D1, dia(10))
    est = estimaciones(db)
    assert set(est) == {dia(4), dia(5)}
    assert (
        est[dia(4)].mm == 10.0 and est[dia(5)].mm == 20.0
    )  # ni la automática (99) ni la lejana (77)
    assert est[dia(4)].gap_state == RainState.SIN_FILA
    assert est[dia(5)].gap_state == RainState.FILA_SIN_VALOR
    assert (r.huecos, r.estimados, r.sin_estimar) >= (2, 2, 0)
    assert r.por_metodo["vecinas_idw_v1"] >= 2


def test_lo_estimado_se_guarda_siempre_como_estimado_con_el_metodo_y_lo_que_se_uso(db, mundo):
    servicio(db).run(D1, dia(10))
    e = estimaciones(db)[dia(4)]
    assert e.category == DataCategory.ESTIMADO and e.method == "vecinas_idw_v1"
    assert '"station_id": 2' in e.detail and "distance_km" in e.detail and "max_km" in e.detail


def test_no_toca_ninguna_lectura_observada_y_el_hueco_sigue_siendo_hueco(db, mundo):
    antes = [
        (r.station_id, r.obs_date, r.state, r.mm, r.category)
        for r in db.scalars(select(RainfallRecord))
    ]
    servicio(db).run(D1, dia(10))
    despues = [
        (r.station_id, r.obs_date, r.state, r.mm, r.category)
        for r in db.scalars(select(RainfallRecord))
    ]
    assert antes == despues
    hueco = db.scalar(
        select(RainfallRecord).where(
            RainfallRecord.station_id == 1, RainfallRecord.obs_date == dia(4)
        )
    )
    assert (hueco.state, hueco.mm) == (RainState.SIN_FILA, None)


def test_el_acumulado_observado_no_cambia_ni_aparece_nada_en_el_estimado(client, db, mundo):
    pedido = {"from": dia(1).isoformat(), "to": dia(10).isoformat(), "station_id": 1}
    observado_antes = client.get("/api/rainfall/accumulated", params=pedido).json()
    servicio(db).run(D1, dia(10))
    observado_despues = client.get("/api/rainfall/accumulated", params=pedido).json()
    assert observado_antes == observado_despues
    assert (
        observado_despues["stations"][0]["accumulated_mm"] == 6.0
    )  # 0+1+2+0+0+3+0+0: sin 10 ni 20
    estimado = client.get(
        "/api/rainfall/accumulated", params={**pedido, "category": "estimado"}
    ).json()
    assert estimado["stations"][0]["accumulated_mm"] is None  # las estimaciones no entran ahí
    serie = client.get(
        "/api/rainfall",
        params={"station_id": 1, "from": dia(1).isoformat(), "to": dia(10).isoformat()},
    ).json()
    dias = {d["obs_date"]: d for d in serie["days"]}
    assert dias[dia(4).isoformat()]["mm"] is None and dias[dia(5).isoformat()]["mm"] is None


def test_repetir_la_corrida_no_duplica_nada(db, mundo):
    servicio(db).run(D1, dia(10))
    primero = db.scalar(select(func.count()).select_from(GapEstimate))
    servicio(db).run(D1, dia(10))
    assert db.scalar(select(func.count()).select_from(GapEstimate)) == primero


def test_dry_run_cuenta_pero_no_guarda(db, mundo):
    r = servicio(db).run(D1, dia(10), dry_run=True)
    assert r.estimados >= 2 and r.guardado is False
    assert db.scalar(select(func.count()).select_from(GapEstimate)) == 0


def test_sin_vecina_con_dato_ese_dia_el_hueco_sigue_sin_dato(db, mundo):
    a, *_ = mundo
    cargar(db, a, {11: "sin_fila", 12: 5.0})  # el día 11 la vecina B no midió
    db.commit()
    servicio(db).run(D1, dia(12))
    assert dia(11) not in estimaciones(db)


def test_un_dia_de_la_vecina_con_advertencia_de_calidad_no_se_usa(db, mundo):
    _, b, *_ = mundo
    db.add(
        QualityFlag(
            station_id=b.id,
            code="ceros_prolongados",
            start_date=dia(5),
            end_date=dia(5),
            severity=Severity.ALERTA,
            rule_version="t",
        )
    )
    db.commit()
    servicio(db).run(D1, dia(10))
    assert set(estimaciones(db)) == {dia(4)}  # el 5 queda sin dato


def test_no_se_estima_fuera_del_periodo_con_datos_de_la_estacion(db, mundo):
    a, b, *_ = mundo
    # La vecina midió antes de que A empezara y después de que terminara: no son huecos de A.
    cargar(db, a, {-5: "sin_fila", 30: "sin_fila"})
    cargar(db, b, {-5: 4.0, 30: 4.0})
    db.commit()
    servicio(db).run(dia(-10), dia(40))
    assert dia(-5) not in estimaciones(db) and dia(30) not in estimaciones(db)


def test_un_vecino_con_coordenadas_pendientes_no_cuenta(db, mundo):
    a, *_ = mundo
    fuente = db.scalar(select(Source))
    sin_coords = estacion(db, fuente, "P", 0, 0, coords=CoordsStatus.PENDIENTE)
    cargar(db, sin_coords, {4: 55.0})
    db.commit()
    servicio(db).run(D1, dia(10))
    assert estimaciones(db)[dia(4)].mm == 10.0


def test_chirps_cargado_cubre_donde_no_hay_vecinas_y_pierde_contra_las_vecinas(db, mundo):
    a, *_ = mundo
    cargar(
        db, a, {13: "sin_fila", 14: 1.0}
    )  # A vuelve a medir el 14: el 13 queda dentro de su período
    cargar(db, a, {13: 6.5, 4: 50.0}, categoria=DataCategory.ESTIMADO)  # CHIRPS ya cargado
    db.commit()
    servicio(db).run(D1, dia(14))
    est = estimaciones(db)
    assert est[dia(13)].mm == 6.5 and est[dia(13)].method == "chirps_v3_punto"
    assert est[dia(4)].mm == 10.0 and est[dia(4)].method == "vecinas_idw_v1"


def test_sin_chirps_cargado_no_se_inventa_nada(db, mundo):
    a, *_ = mundo
    cargar(db, a, {13: "sin_fila", 14: 1.0})
    db.commit()
    servicio(db).run(D1, dia(14))
    assert dia(13) not in estimaciones(db)


def test_no_pasa_del_corte_de_datos(db, mundo):
    r = servicio(db).run(D1, date(2030, 1, 1))
    assert r.estimados >= 2
    assert db.scalar(select(func.max(GapEstimate.obs_date))) <= CORTE


def test_entradas_invalidas(db, mundo):
    with pytest.raises(ValueError, match="no puede ser posterior"):
        servicio(db).run(dia(5), dia(1))
    with pytest.raises(ValueError, match="No existe esa estación"):
        servicio(db).run(D1, dia(10), station_id=9999)


def test_una_estacion_sola(db, mundo):
    servicio(db).run(D1, dia(10), station_id=1)
    assert db.scalar(select(func.count()).select_from(GapEstimate)) == 2


# --- API de lectura ---------------------------------------------------------


def test_la_api_lista_las_estimaciones_rotuladas_como_estimado(client, db, mundo):
    servicio(db).run(D1, dia(10))
    body = client.get("/api/estimates", params={"station_id": 1}).json()
    assert body["category"] == "estimado" and "no medidos" in body["notice"]
    assert body["total"] == 2
    primero = body["items"][0]
    assert primero["category"] == "estimado" and primero["method"] == "vecinas_idw_v1"
    assert primero["gap_state"] == "sin_fila" and primero["mm"] == 10.0
    assert primero["detail"]["vecinas"][0]["station_id"] == 2  # el JSON llega como objeto


def test_la_api_filtra_por_periodo_y_valida(client, db, mundo):
    servicio(db).run(D1, dia(10))
    una = client.get(
        "/api/estimates",
        params={"station_id": 1, "from": dia(5).isoformat(), "to": dia(5).isoformat()},
    ).json()
    assert una["total"] == 1 and una["items"][0]["obs_date"] == dia(5).isoformat()
    for malo in (
        {"station_id": 0},
        {"limit": 501},
        {"offset": -1},
        {"from": "ayer"},
        {"from": dia(5).isoformat(), "to": dia(1).isoformat()},
    ):
        assert client.get("/api/estimates", params=malo).status_code == 422, malo


def test_la_api_sin_estimaciones_devuelve_una_lista_vacia(client):
    body = client.get("/api/estimates").json()
    assert body["items"] == [] and body["total"] == 0 and body["category"] == "estimado"


# --- Línea de comandos ------------------------------------------------------


def test_el_comando_estima_y_cuenta(db, mundo, app, monkeypatch, capsys):
    url = str(app.state.engine.url)
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    try:
        assert (
            cli.main(
                ["estimate-gaps", "--from", "2020-01-01", "--to", "2020-01-10", "--station-id", "1"]
            )
            == 0
        )
        salida = capsys.readouterr().out
        assert "estimados: 2" in salida and "vecinas_idw_v1: 2" in salida and "ESTIMADO" in salida
        assert cli.main(["estimate-gaps", "--from", "2020-01-10", "--to", "2020-01-01"]) == 1
        assert "no puede ser posterior" in capsys.readouterr().err
    finally:
        get_settings.cache_clear()
