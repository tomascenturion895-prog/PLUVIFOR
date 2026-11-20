"""Estimación de días sin dato (SCRUM-93): matemática y reglas puras, sin base de datos."""

import pytest

from app.domain.estimation import (
    METODO_CHIRPS,
    METODO_VECINAS,
    Contexto,
    EstimadorChirps,
    EstimadorVecinas,
    Vecina,
    distancia_km,
    mismo_horario,
    promedio_idw,
)


def vecina(km: float, mm: float, sid: int = 1) -> Vecina:
    return Vecina(station_id=sid, name=f"E{sid}", distance_km=km, mm=mm)


def test_la_distancia_entre_las_estaciones_de_el_colorado_es_de_unos_4_5_km():
    km = distancia_km(-26.3, -59.38, -26.33, -59.35)
    assert 4.3 < km < 4.7
    assert distancia_km(-26.3, -59.38, -26.3, -59.38) == 0
    assert distancia_km(-26.3, -59.38, -26.33, -59.35) == pytest.approx(
        distancia_km(-26.33, -59.35, -26.3, -59.38)
    )


def test_con_una_sola_vecina_se_copia_su_valor():
    assert promedio_idw([vecina(4.5, 12.5)]) == 12.5


def test_la_vecina_mas_cercana_pesa_mas():
    cerca, lejos = vecina(2, 10, 1), vecina(10, 0, 2)
    estimado = promedio_idw([cerca, lejos])
    assert 9 < estimado < 10  # pesos 1/4 y 1/100: queda casi igual a la cercana


def test_sin_vecinas_no_hay_estimacion_ni_un_cero():
    assert promedio_idw([]) is None


def test_si_todas_las_vecinas_midieron_cero_la_estimacion_es_cero_y_es_un_valor():
    assert promedio_idw([vecina(3, 0), vecina(5, 0, 2)]) == 0.0


def test_dos_estaciones_casi_en_el_mismo_lugar_no_rompen_los_pesos():
    assert promedio_idw([vecina(0.0, 7), vecina(10, 1, 2)]) is not None


def test_el_estimador_de_vecinas_respeta_el_radio():
    estimador = EstimadorVecinas(max_km=25)
    assert estimador.estimar(Contexto([vecina(26, 5)], None)) is None
    hecho = estimador.estimar(Contexto([vecina(24.9, 5)], None))
    assert hecho is not None and hecho.mm == 5 and hecho.method == METODO_VECINAS


def test_el_estimador_exige_la_cantidad_minima_de_vecinas():
    estimador = EstimadorVecinas(min_vecinas=2)
    assert estimador.estimar(Contexto([vecina(3, 5)], None)) is None
    assert estimador.estimar(Contexto([vecina(3, 5, 1), vecina(4, 5, 2)], None)) is not None


def test_el_detalle_dice_que_vecinas_y_que_parametros_se_usaron():
    hecho = EstimadorVecinas().estimar(Contexto([vecina(8, 2, 2), vecina(3, 6, 1)], None))
    assert [v["station_id"] for v in hecho.detail["vecinas"]] == [1, 2]  # la más cercana primero
    assert hecho.detail["vecinas"][0] == {
        "station_id": 1,
        "name": "E1",
        "distance_km": 3.0,
        "mm": 6,
    }
    assert hecho.detail["parametros"]["max_km"] == 25.0


def test_chirps_solo_responde_si_hay_un_valor_cargado():
    assert EstimadorChirps().estimar(Contexto([], None)) is None
    hecho = EstimadorChirps().estimar(Contexto([], 3.4))
    assert hecho is not None and hecho.mm == 3.4 and hecho.method == METODO_CHIRPS
    assert EstimadorChirps().estimar(Contexto([], 0.0)).mm == 0.0  # un cero de CHIRPS es un valor


@pytest.mark.parametrize(
    ("a", "b", "esperado"),
    [
        (("Convencional", "09:00"), ("Convencional", "09:00"), True),
        ((" convencional ", "09:00"), ("Convencional", "09:00"), True),
        (("Convencional", None), ("Convencional", None), True),
        (("Convencional", "09:00"), ("Automática (Nimbus THP)", "09:00"), False),
        (("Convencional", "09:00"), ("Convencional", "07:00"), False),
        (("Convencional", "09:00"), ("Convencional", None), False),
        ((None, "09:00"), (None, "09:00"), False),  # no se sabe el tipo: no se asume
        (("", "09:00"), ("Convencional", "09:00"), False),
    ],
)
def test_solo_se_comparan_estaciones_que_cuentan_el_dia_igual(a, b, esperado):
    assert mismo_horario(a[0], a[1], b[0], b[1]) is esperado
