"""POST /api/reports/summary (SCRUM-62): parte pluvial con huecos declarados y advertencias."""

from datetime import date, timedelta

import pytest
from sqlalchemy.orm import Session

from app.domain.enums import DataCategory, RainState, Validation
from app.domain.quality import DayValue
from app.domain.report import compose_text, fmt_mm, intense_events
from app.models import RainfallRecord, Source, Station

START = date(2016, 1, 1)
URL = "/api/reports/summary"


def source(db: Session, code: str, cutoff: str) -> Source:
    src = Source(
        code=code, name=code.upper(), network="RED", category=DataCategory.OBSERVADO,
        day_cutoff_local=cutoff,
    )  # fmt: skip
    db.add(src)
    db.flush()
    return src


def station(db: Session, src: Source, code: str, name: str, plan: list, **extra) -> int:
    st = Station(source_id=src.id, code=code, name=name, **extra)
    db.add(st)
    db.flush()
    for i, (state, mm) in enumerate(plan):
        db.add(
            RainfallRecord(
                station_id=st.id, obs_date=START + timedelta(days=i), state=state, mm=mm,
                category=DataCategory.OBSERVADO, validation=Validation.VALIDADO,
            )
        )  # fmt: skip
    db.commit()
    return st.id


D = RainState.DATO
PLAN = [
    (D, 12.5),
    (D, 0.0),
    (RainState.SIN_FILA, None),
    (RainState.FILA_SIN_VALOR, None),
    (D, 55.0),
]


@pytest.fixture
def uno(db: Session) -> int:
    return station(db, source(db, "siga_inta", "09:00"), "424", "El Colorado", PLAN)


def pedir(client, ids, **extra):
    body = {"station_ids": ids, "from": "2016-01-01", "to": "2016-01-05", **extra}
    return client.post(URL, json=body)


class TestParte:
    def test_acumulado_y_dias_con_dato_sin_contar_huecos_como_cero(self, client, uno):
        body = pedir(client, [uno]).json()
        s = body["stations"][0]
        assert s["summary"]["accumulated_mm"] == 67.5
        assert s["summary"]["days_with_data"] == 3
        assert s["summary"]["days_sin_fila"] == 1
        assert s["summary"]["days_fila_sin_valor"] == 1
        assert s["source"]["code"] == "siga_inta"
        assert s["category"] == "observado"

    def test_eventos_intensos_son_solo_dias_con_dato(self, client, uno):
        events = pedir(client, [uno]).json()["stations"][0]["intense_events"]
        assert events == [{"obs_date": "2016-01-05", "mm": 55.0, "level_mm": 50.0}]

    def test_el_texto_declara_los_huecos_la_fuente_y_el_corte(self, client, uno):
        body = pedir(client, [uno]).json()
        text = body["text"]
        assert "PARTE PLUVIAL" in text
        assert "El Colorado (SIGA_INTA, RED)" in text
        assert "67,5 mm en 3 de 5 días" in text
        assert "2 días sin dato (1 sin fila, 1 con fila sin valor): no se cuentan como 0 mm" in text
        assert "Eventos intensos: 05/01 55,0 mm (≥50 mm)" in text
        assert "Fecha de corte de los datos: 31/10/2026" in text
        assert "Categoría: observado" in text
        assert text.rstrip().endswith("no es una herramienta oficial")
        assert body["data_cutoff_date"] == "2026-10-31"

    def test_periodo_sin_datos_lo_dice_y_no_informa_cero(self, client, db):
        sid = station(db, source(db, "s", "09:00"), "1", "Vacía", [])
        body = pedir(client, [sid]).json()
        assert body["stations"][0]["summary"]["accumulated_mm"] is None
        assert "Sin datos en el período" in body["text"]
        assert "no significa que no haya llovido" in body["text"]
        assert "0,0 mm" not in body["text"]

    def test_una_racha_de_ceros_sale_como_advertencia(self, client, db):
        plan = [(D, 0.0)] * 70
        sid = station(db, source(db, "s", "09:00"), "2", "Seca", plan)
        from app.repositories.quality import SqlQualityRepository
        from app.services.quality import QualityService

        QualityService(SqlQualityRepository(db)).recompute_zero_streaks()
        body = client.post(
            URL, json={"station_ids": [sid], "from": "2016-01-01", "to": "2016-03-10"}
        ).json()
        codes = [w["code"] for w in body["stations"][0]["warnings"]]
        assert "ceros_prolongados" in codes
        assert "Racha de 60 días" in body["text"]

    def test_recorta_al_corte_y_lo_avisa(self, client, uno):
        body = pedir(client, [uno], **{"from": "2026-10-01", "to": "2026-12-31"}).json()
        assert body["clipped_to_cutoff"] is True
        assert body["date_to"] == "2026-10-31"
        assert "se recortó" in body["text"]

    def test_sin_comparaciones_con_una_sola_estacion(self, client, uno):
        body = pedir(client, [uno]).json()
        assert body["comparability_warnings"] == []
        assert "no se suman entre sí" not in body["text"]


class TestVariasEstaciones:
    def test_horario_de_corte_distinto_y_no_se_suman(self, client, db):
        a = station(db, source(db, "a", "09:00"), "1", "Uno", PLAN)
        b = station(db, source(db, "b", "07:00"), "2", "Dos", PLAN)
        body = pedir(client, [a, b]).json()
        codes = [w["code"] for w in body["comparability_warnings"]]
        assert "horario_corte_distinto" in codes
        assert "no se suman entre sí" in body["text"]
        assert len(body["stations"]) == 2
        assert "total" not in body

    def test_cobertura_despareja(self, client, db):
        a = station(db, source(db, "a", "09:00"), "1", "Uno", [(D, 1.0)] * 5)
        b = station(db, source(db, "b", "09:00"), "2", "Dos", [(RainState.SIN_FILA, None)] * 5)
        codes = [w["code"] for w in pedir(client, [a, b]).json()["comparability_warnings"]]
        assert "cobertura_despareja" in codes

    def test_reglas_que_no_se_pudieron_evaluar_se_informan(self, client, db):
        a = station(db, source(db, "a", "09:00"), "1", "Uno", PLAN)
        b = station(
            db,
            source(
                db,
                "b",
                None,
            ),
            "2",
            "Dos",
            PLAN,
        )
        body = pedir(client, [a, b]).json()
        assert any(n["code"] == "horario_corte_distinto" for n in body["not_evaluated"])

    def test_ids_repetidos_se_cuentan_una_vez(self, client, uno):
        assert len(pedir(client, [uno, uno]).json()["stations"]) == 1


class TestEntradaInvalida:
    def test_sin_estaciones(self, client):
        assert pedir(client, []).status_code == 422

    def test_demasiadas_estaciones(self, client):
        assert pedir(client, list(range(1, 22))).status_code == 422

    def test_id_no_positivo(self, client):
        assert pedir(client, [0]).status_code == 422

    def test_estacion_inexistente(self, client):
        response = pedir(client, [999])
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "station_not_found"

    def test_periodo_invertido(self, client, uno):
        response = pedir(client, [uno], **{"from": "2016-02-01", "to": "2016-01-01"})
        assert response.status_code == 422

    def test_fecha_con_formato_invalido(self, client, uno):
        assert pedir(client, [uno], **{"from": "ayer"}).status_code == 422

    def test_periodo_posterior_al_corte(self, client, uno):
        response = pedir(client, [uno], **{"from": "2026-11-05", "to": "2026-11-10"})
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "after_cutoff"


class TestDominio:
    def test_un_hueco_nunca_es_un_evento(self):
        days = [
            DayValue(START, RainState.SIN_FILA, None),
            DayValue(START + timedelta(days=1), RainState.FILA_SIN_VALOR, None),
            DayValue(START + timedelta(days=2), RainState.DATO, 49.9),
            DayValue(START + timedelta(days=3), RainState.DATO, 50.0),
            DayValue(START + timedelta(days=4), RainState.DATO, 100.0),
        ]
        assert [(e.mm, e.level_mm) for e in intense_events(days)] == [(50.0, 50.0), (100.0, 100.0)]

    def test_formato_de_milimetros(self):
        assert fmt_mm(1265.0) == "1.265,0 mm"
        assert fmt_mm(0.0) == "0,0 mm"

    def test_texto_sin_estaciones_no_falla(self):
        text = compose_text(
            category=DataCategory.OBSERVADO, date_from=START, date_to=START,
            cutoff=date(2026, 10, 31), clipped=False, stations=[], comparability=[],
        )  # fmt: skip
        assert "PARTE PLUVIAL" in text
