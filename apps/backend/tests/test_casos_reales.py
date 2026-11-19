"""Casos con datos reales del SIGA (SCRUM-42).

Los valores esperados se calcularon aparte, leyendo `docs/datos/lluvia_diaria_siga_formosa.csv`
con el módulo `csv` y sin usar código de la aplicación. La tabla con la explicación de cada caso
está en `docs/qa/casos-de-prueba-reales.md`. Los datos de `tests/fixtures/siga_casos_reales.csv`
son filas reales del CSV, sin modificar, de las ventanas que usan los casos.
"""

from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.domain.enums import ImportMode
from app.repositories.ingestion import SqlIngestionRepository
from app.repositories.quality import SqlQualityRepository
from app.services.importer import ImportService
from app.services.quality import QualityService

FIXTURES = Path(__file__).parent / "fixtures"
CUTOFF = date(2026, 10, 31)


@pytest.fixture
def ids(app, client: TestClient) -> dict[str, int]:
    """Carga las filas reales y devuelve el id interno de cada estación por su código SIGA."""
    with app.state.session_factory() as session:
        service = ImportService(SqlIngestionRepository(session), CUTOFF)
        stations = service.import_stations(
            "siga_inta", "e.csv", (FIXTURES / "siga_estaciones.csv").read_bytes()
        )
        assert stations.rows_rejected == 0
        rain = service.import_rainfall(
            "siga_inta",
            "l.csv",
            (FIXTURES / "siga_casos_reales.csv").read_bytes(),
            ImportMode.COMMIT,
        )
        assert (rain.rows_read, rain.rows_rejected) == (654, 0)
        QualityService(SqlQualityRepository(session)).recompute_zero_streaks()
    items = client.get("/api/stations").json()["items"]
    return {item["code"]: item["id"] for item in items}


def resumen(client: TestClient, ids: dict[str, int], code: str, desde: str, hasta: str) -> dict:
    response = client.get(
        "/api/rainfall", params={"station_id": ids[code], "from": desde, "to": hasta}
    )
    assert response.status_code == 200
    return response.json()


def codigos(body: dict) -> set[str]:
    return {w["code"] for w in body["warnings"]}


def test_caso1_racha_de_ceros_de_la_424(client, ids):
    """424: 281 días seguidos con 0 mm (2015-09-20 a 2016-06-26); no se da por bueno."""
    body = resumen(client, ids, "424", "2015-09-20", "2016-06-26")
    assert body["summary"] == {
        "days_in_period": 281,
        "days_with_data": 281,
        "days_sin_fila": 0,
        "days_fila_sin_valor": 0,
        "coverage": 1.0,
        "accumulated_mm": 0.0,
    }
    racha = next(w for w in body["warnings"] if w["code"] == "ceros_prolongados")
    assert (racha["start_date"], racha["end_date"]) == ("2015-09-20", "2016-06-26")


def test_caso2_la_425_llovio_1265_mm_en_el_mismo_periodo(client, ids):
    """425, mismo período: 1.265 mm con todos los días con dato y sin racha de ceros."""
    body = resumen(client, ids, "425", "2015-09-20", "2016-06-26")
    assert body["summary"]["accumulated_mm"] == 1265.0
    assert body["summary"]["days_with_data"] == 281
    assert "ceros_prolongados" not in codigos(body)


def test_caso3_la_racha_termina_donde_hay_un_hueco_no_un_cero(client, ids):
    """El 2016-06-27 y 28 son fila sin valor en la 424: el hueco corta la racha, no la alarga."""
    body = resumen(client, ids, "424", "2016-06-27", "2016-06-28")
    assert body["summary"]["days_fila_sin_valor"] == 2
    assert body["summary"]["days_with_data"] == 0
    assert body["summary"]["accumulated_mm"] is None  # sin dato, no 0
    assert "ceros_prolongados" not in codigos(body)


def test_caso4_dias_sin_fila_y_fila_sin_valor_se_cuentan_aparte(client, ids):
    """425, 2018-05-01 a 2018-05-15: 3 días con dato, 11 sin fila y 1 fila sin valor."""
    body = resumen(client, ids, "425", "2018-05-01", "2018-05-15")
    assert body["summary"] == {
        "days_in_period": 15,
        "days_with_data": 3,
        "days_sin_fila": 11,
        "days_fila_sin_valor": 1,
        "coverage": 0.2,
        "accumulated_mm": 0.0,
    }
    assert "cobertura_baja" in codigos(body)


def test_caso5_un_mes_de_filas_sin_valor_no_suma_cero(client, ids):
    """51, 2014-08-15 a 2014-09-20: 29 filas sin valor y 8 con dato (115,5 mm)."""
    body = resumen(client, ids, "51", "2014-08-15", "2014-09-20")
    assert body["summary"] == {
        "days_in_period": 37,
        "days_with_data": 8,
        "days_sin_fila": 0,
        "days_fila_sin_valor": 29,
        "coverage": 0.2162,
        "accumulated_mm": 115.5,
    }


@pytest.mark.parametrize(
    ("code", "dia", "mm"),
    [
        ("51", "2014-04-10", 0.0),
        ("424", "2014-04-10", 138.0),
        ("51", "2014-04-11", 143.0),
        ("424", "2014-04-11", 11.75),
    ],
)
def test_caso6_el_mismo_evento_cae_un_dia_despues_en_la_51(client, ids, code, dia, mm):
    """La 51 fecha un día después: 138 mm el 10/04 en la 424 y 143 mm el 11/04 en la 51."""
    body = resumen(client, ids, code, dia, dia)
    assert body["summary"]["accumulated_mm"] == mm


def test_caso6b_la_semana_completa_no_coincide_entre_redes(client, ids):
    """Mismo período 2014-04-08 a 2014-04-13: 159 mm en la 51 y 153,25 mm en la 424."""
    assert (
        resumen(client, ids, "51", "2014-04-08", "2014-04-13")["summary"]["accumulated_mm"] == 159.0
    )
    assert (
        resumen(client, ids, "424", "2014-04-08", "2014-04-13")["summary"]["accumulated_mm"]
        == 153.25
    )


def test_caso7_un_periodo_que_pasa_el_corte_se_recorta_al_31_de_octubre(client, ids):
    """424, 2017-01-01 a 2026-12-31: se recorta a 2026-10-31 (3.591 días) y no hay dato."""
    body = resumen(client, ids, "424", "2017-01-01", "2026-12-31")
    assert body["clipped_to_cutoff"] is True
    assert body["date_to"] == "2026-10-31"
    assert body["summary"]["days_in_period"] == 3591
    assert body["summary"]["accumulated_mm"] is None  # nada cargado en esos años: sin dato, no 0


def test_caso7b_un_periodo_de_mas_de_diez_anos_se_rechaza_antes_de_recortar(client, ids):
    """Del 2016-06-20 al 2026-12-31 son 3.817 días: pasa el máximo de 3.660 antes de recortar."""
    response = client.get(
        "/api/rainfall",
        params={"station_id": ids["424"], "from": "2016-06-20", "to": "2026-12-31"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "range_too_large"


def test_caso8_un_periodo_posterior_al_corte_se_rechaza(client, ids):
    response = client.get(
        "/api/rainfall", params={"station_id": ids["424"], "from": "2026-11-01", "to": "2026-11-30"}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "after_cutoff"


def test_caso9_el_acumulado_por_zona_o_estacion_repite_el_resultado_de_la_serie(client, ids):
    """El acumulado de la 424 en la racha coincide con la serie y repite la advertencia."""
    response = client.get(
        "/api/rainfall/accumulated",
        params={"station_id": ids["424"], "from": "2015-09-20", "to": "2016-06-26"},
    )
    assert response.status_code == 200
    entry = response.json()["stations"][0]
    assert (entry["accumulated_mm"], entry["days_with_data"]) == (0.0, 281)
    assert "ceros_prolongados" in {w["code"] for w in entry["warnings"]}
