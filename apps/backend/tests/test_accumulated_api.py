"""GET /api/rainfall/accumulated (SCRUM-46): totales contra cálculos hechos a mano."""

from datetime import date, timedelta

import pytest
from sqlalchemy.orm import Session

from app.domain.enums import DataCategory, RainState, Severity, Validation
from app.models import QualityFlag, RainfallRecord, Source, Station

START = date(2016, 1, 1)
D, SF, FSV = RainState.DATO, RainState.SIN_FILA, RainState.FILA_SIN_VALOR


@pytest.fixture
def datos(db: Session) -> dict[str, int]:
    src = Source(code="s", name="S", network="R", category=DataCategory.OBSERVADO)
    db.add(src)
    db.flush()

    def estacion(code: str, zone: str, plan: list[tuple[RainState, float | None]]) -> int:
        st = Station(source_id=src.id, code=code, name=f"Est {code}", zone=zone)
        db.add(st)
        db.flush()
        for i, (state, mm) in enumerate(plan):
            if state is SF:
                continue  # el día no existe en la fuente: no se guarda fila
            db.add(
                RainfallRecord(
                    station_id=st.id, obs_date=START + timedelta(days=i), state=state, mm=mm,
                    category=DataCategory.OBSERVADO, validation=Validation.VALIDADO,
                )
            )  # fmt: skip
        return st.id

    ids = {
        # Caso 1 (zona «norte», 10 días): A = 10+0+2,5+0 = 12,5 con 4 días de dato; 6 sin dato.
        "A": estacion(
            "A", "norte", [(D, 10.0), (D, 0.0), (SF, None), (D, 2.5), (FSV, None), (D, 0.0)]
        ),
        # B = 7,25 con 3 días de dato; 7 sin dato
        "B": estacion("B", "norte", [(D, 7.25), (SF, None), (SF, None), (D, 0.0), (D, 0.0)]),
        # Caso 2: zona «sur» sin ningún día con dato: null, no 0
        "C": estacion("C", "sur", [(FSV, None), (FSV, None)]),
        "D": estacion("D", "sur", []),
    }
    db.commit()
    return ids


def pedir(client, **extra):
    params = {"from": "2016-01-01", "to": "2016-01-10", **extra}
    return client.get("/api/rainfall/accumulated", params=params)


def por_estacion(body) -> dict[str, dict]:
    return {s["station_name"]: s for s in body["stations"]}


class TestTotales:
    def test_zona_con_huecos_suma_solo_los_dias_con_dato(self, client, datos):
        body = pedir(client, zone="norte").json()
        est = por_estacion(body)
        assert est["Est A"]["accumulated_mm"] == 12.5
        assert est["Est A"]["days_with_data"] == 4
        assert est["Est A"]["days_without_data"] == 6
        assert est["Est B"]["accumulated_mm"] == 7.25
        assert est["Est B"]["days_with_data"] == 3
        assert est["Est B"]["days_without_data"] == 7
        assert body["days_in_period"] == 10

    def test_las_estaciones_no_se_suman_entre_si(self, client, datos):
        body = pedir(client, zone="norte").json()
        assert len(body["stations"]) == 2
        assert "accumulated_mm" not in body  # no hay un total de la zona

    def test_zona_sin_ningun_dato_da_null_no_cero(self, client, datos):
        body = pedir(client, zone="sur").json()
        est = por_estacion(body)
        assert est["Est C"]["accumulated_mm"] is None
        assert est["Est D"]["accumulated_mm"] is None
        assert est["Est C"]["days_with_data"] == 0
        assert est["Est C"]["days_without_data"] == 10

    def test_una_estacion_sola(self, client, datos):
        body = pedir(client, station_id=datos["A"]).json()
        assert [s["accumulated_mm"] for s in body["stations"]] == [12.5]

    def test_un_cero_real_es_cero_y_no_null(self, client, datos, db):
        solo_ceros = Station(source_id=1, code="Z", name="Est Z", zone="este")
        db.add(solo_ceros)
        db.flush()
        db.add(
            RainfallRecord(
                station_id=solo_ceros.id, obs_date=START, state=D, mm=0.0,
                category=DataCategory.OBSERVADO, validation=Validation.VALIDADO,
            )
        )  # fmt: skip
        db.commit()
        est = por_estacion(pedir(client, zone="este").json())
        assert est["Est Z"]["accumulated_mm"] == 0.0

    def test_las_categorias_no_se_mezclan(self, client, datos):
        body = pedir(client, zone="norte", category="estimado").json()
        assert all(s["accumulated_mm"] is None for s in body["stations"])


class TestAdvertencias:
    def test_cobertura_baja(self, client, datos):
        warnings = por_estacion(pedir(client, zone="norte").json())["Est A"]["warnings"]
        assert "cobertura_baja" in [w["code"] for w in warnings]

    def test_racha_de_ceros_marcada(self, client, datos, db):
        db.add(
            QualityFlag(
                station_id=datos["A"],
                code="ceros_prolongados",
                start_date=START,
                end_date=START + timedelta(days=9),
                severity=Severity.AVISO,
                rule_version="ceros_prolongados/1",
            )
        )
        db.commit()
        warnings = por_estacion(pedir(client, zone="norte").json())["Est A"]["warnings"]
        assert "ceros_prolongados" in [w["code"] for w in warnings]

    def test_declara_lo_que_no_evalua(self, client, datos):
        assert pedir(client, zone="norte").json()["not_evaluated"] == ["dato_sin_validar"]


class TestEntradaInvalida:
    def test_rango_invertido_da_422(self, client, datos):
        r = pedir(client, zone="norte", **{"from": "2016-02-01", "to": "2016-01-01"})
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "invalid_range"

    def test_posterior_al_corte_da_422(self, client, datos):
        r = pedir(client, zone="norte", **{"from": "2026-11-05", "to": "2026-11-10"})
        assert r.status_code == 422
        assert r.json()["error"]["code"] == "after_cutoff"

    def test_el_periodo_se_recorta_al_corte(self, client, datos):
        body = pedir(client, zone="norte", **{"from": "2026-10-01", "to": "2026-12-31"}).json()
        assert body["clipped_to_cutoff"] is True
        assert body["date_to"] == "2026-10-31"

    def test_sin_estacion_ni_zona_da_422(self, client, datos):
        assert pedir(client).status_code == 422

    def test_con_estacion_y_zona_a_la_vez_da_422(self, client, datos):
        assert pedir(client, zone="norte", station_id=datos["A"]).status_code == 422

    def test_estacion_inexistente_da_404(self, client, datos):
        assert pedir(client, station_id=999).status_code == 404

    def test_zona_inexistente_da_404(self, client, datos):
        r = pedir(client, zone="no-existe")
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "zone_not_found"

    def test_fecha_mal_escrita_da_422(self, client, datos):
        assert pedir(client, zone="norte", **{"from": "ayer"}).status_code == 422
