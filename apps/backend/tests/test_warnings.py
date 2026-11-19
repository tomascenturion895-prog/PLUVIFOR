import csv
from datetime import date, timedelta
from pathlib import Path

import pytest

from app.domain.enums import DataCategory, RainState
from app.domain.quality import DayValue
from app.domain.warnings import (
    CODE_CATEGORY,
    CODE_COVERAGE,
    CODE_CUTOFF,
    CODE_NEIGHBORS,
    CODE_UNVALIDATED,
    CODE_ZERO_STREAK,
    Advisory,
    NotApplied,
    SeriesInput,
    distance_km,
    evaluate_warnings,
)

START = date(2016, 1, 1)
OBS = DataCategory.OBSERVADO


def run(spec: list[tuple[RainState, float | None]]) -> list[DayValue]:
    return [DayValue(START + timedelta(days=i), s, mm) for i, (s, mm) in enumerate(spec)]


def zeros(n: int):
    return [(RainState.DATO, 0.0)] * n


def rainy(n: int, mm: float = 2.0):
    return [(RainState.DATO, mm)] * n


def series(code="A", spec=None, **kw) -> SeriesInput:
    kw.setdefault("category", OBS)
    return SeriesInput(code, days=run(spec if spec is not None else rainy(10)), **kw)


def codes(result) -> list[str]:
    return [a.code for a in result.advisories]


def test_clean_single_series_has_no_advisories():
    result = evaluate_warnings(series(lat=-26.0, lon=-59.0))
    assert result.advisories == []


# 1. horario de corte
def test_different_cutoff_hours_are_warned():
    a, b = series("A", day_cutoff_local="07:00"), series("B", day_cutoff_local="09:00")
    advisory = [x for x in evaluate_warnings(a, [b]).advisories if x.code == CODE_CUTOFF]
    assert len(advisory) == 1 and advisory[0].detail["cortes"] == ["07:00", "09:00"]


def test_same_cutoff_hour_is_not_warned():
    a, b = series("A", day_cutoff_local="09:00"), series("B", day_cutoff_local="09:00")
    assert CODE_CUTOFF not in codes(evaluate_warnings(a, [b]))


def test_unknown_cutoff_is_reported_as_not_applied_not_as_ok():
    result = evaluate_warnings(series("A", day_cutoff_local="09:00"), [series("B")])
    assert CODE_CUTOFF not in codes(result)
    assert CODE_CUTOFF in [n.code for n in result.not_applied]


# 2. observado vs estimado
def test_mixed_categories_are_warned():
    a, b = series("A"), series("B", category=DataCategory.ESTIMADO)
    assert CODE_CATEGORY in codes(evaluate_warnings(a, [b]))


def test_same_category_is_not_warned():
    assert CODE_CATEGORY not in codes(evaluate_warnings(series("A"), [series("B")]))


# 3. cobertura despareja
def test_uneven_coverage_is_warned():
    full = series("A", rainy(10))
    sparse = series("B", rainy(5) + [(RainState.SIN_FILA, None)] * 5)
    assert CODE_COVERAGE in codes(evaluate_warnings(full, [sparse]))


def test_similar_coverage_is_not_warned():
    a, b = series("A", rainy(10)), series("B", rainy(9) + [(RainState.SIN_FILA, None)])
    assert CODE_COVERAGE not in codes(evaluate_warnings(a, [b]))


# 4. dato sin validar
def test_unvalidated_days_are_warned_and_counted():
    result = evaluate_warnings(series("A", unvalidated_days=3), [series("B", unvalidated_days=2)])
    advisory = next(a for a in result.advisories if a.code == CODE_UNVALIDATED)
    assert advisory.detail["dias_sin_validar"] == 5


def test_validated_data_is_not_warned():
    assert CODE_UNVALIDATED not in codes(evaluate_warnings(series("A")))


# 5. racha de ceros
def test_zero_streak_of_60_is_warned_with_its_range():
    result = evaluate_warnings(series("A", zeros(60)))
    advisory = next(a for a in result.advisories if a.code == CODE_ZERO_STREAK)
    assert (advisory.start_date, advisory.end_date) == (START, START + timedelta(days=59))


def test_zero_streak_of_59_or_broken_by_a_gap_is_not_warned():
    assert CODE_ZERO_STREAK not in codes(evaluate_warnings(series("A", zeros(59))))
    gap = zeros(40) + [(RainState.SIN_FILA, None)] + zeros(40)
    assert CODE_ZERO_STREAK not in codes(evaluate_warnings(series("A", gap)))


# 6. inconsistencia con vecinas
def neighbor_case(neighbor_spec, neighbor_lat=-25.5):
    target = series("T", zeros(70), lat=-26.3, lon=-59.3)
    neighbor = series("N", neighbor_spec, lat=neighbor_lat, lon=-59.3)
    return evaluate_warnings(target, [neighbor])


def test_neighbor_with_rain_contradicts_the_zero_streak():
    result = neighbor_case(rainy(70, 1.0))
    advisory = next(a for a in result.advisories if a.code == CODE_NEIGHBORS)
    assert advisory.detail["vecina"] == "N" and advisory.detail["mm_vecina"] == 70.0
    assert advisory.severity.value == "alerta"


def test_neighbor_without_rain_does_not_contradict():
    assert CODE_NEIGHBORS not in codes(neighbor_case(zeros(70)))


def test_neighbor_with_gaps_is_not_used_as_evidence():
    spec = [(RainState.SIN_FILA, None)] * 60 + rainy(10, 20.0)
    assert CODE_NEIGHBORS not in codes(neighbor_case(spec))


def test_neighbor_too_far_is_not_applied():
    result = neighbor_case(rainy(70, 1.0), neighbor_lat=-20.0)
    assert CODE_NEIGHBORS not in codes(result)
    assert CODE_NEIGHBORS in [n.code for n in result.not_applied]


def test_station_without_coordinates_skips_the_rule_and_says_so():
    target = series("T", zeros(70))  # sin lat/lon
    result = evaluate_warnings(target, [series("N", rainy(70), lat=-25.5, lon=-59.3)])
    not_applied = next(n for n in result.not_applied if n.code == CODE_NEIGHBORS)
    assert isinstance(not_applied, NotApplied) and "coordenadas" in not_applied.reason
    assert CODE_NEIGHBORS not in codes(result)


def test_neighbor_without_coordinates_is_ignored():
    target = series("T", zeros(70), lat=-26.3, lon=-59.3)
    result = evaluate_warnings(target, [series("N", rainy(70))])
    assert CODE_NEIGHBORS in [n.code for n in result.not_applied]


def test_distance_between_known_points():
    assert distance_km(-26.33, -59.35, -26.33, -59.35) == 0
    assert 95 < distance_km(-26.33, -59.35, -25.45, -59.5) < 105


def test_custom_rules_can_be_injected():
    class Always:
        code = "x"

        def evaluate(self, target, others):
            return [Advisory("x", "siempre")]

    assert codes(evaluate_warnings(series("A"), rules=[Always()])) == ["x"]


# Caso real: 424 (281 días en 0 mm) contra 425 (1.265 mm en el mismo tramo)
DATA = Path(__file__).resolve().parents[3] / "docs" / "datos"


def _load_siga() -> dict[str, SeriesInput]:
    coords = {}
    with (DATA / "estaciones_siga_formosa.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            coords[row["estacion_id"]] = (float(row["lat"]), float(row["lon"]))
    days: dict[str, list[DayValue]] = {}
    with (DATA / "lluvia_diaria_siga_formosa.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            mm = float(row["mm_pluviometrica"]) if row["mm_pluviometrica"] else None
            days.setdefault(row["estacion_id"], []).append(
                DayValue(date.fromisoformat(row["fecha"]), RainState(row["estado"]), mm)
            )
    return {
        code: SeriesInput(code, OBS, days[code], lat=coords[code][0], lon=coords[code][1])
        for code in days
    }


@pytest.mark.skipif(not DATA.exists(), reason="docs/datos no está disponible")
def test_real_case_424_vs_425():
    siga = _load_siga()
    result = evaluate_warnings(siga["424"], [siga["425"]])

    streak = next(
        a
        for a in result.advisories
        if a.code == CODE_ZERO_STREAK and a.end_date == date(2016, 6, 26)
    )
    assert streak.start_date == date(2015, 9, 20) and streak.detail["days"] == 281

    contradiction = next(
        a for a in result.advisories if a.code == CODE_NEIGHBORS and a.end_date == date(2016, 6, 26)
    )
    assert contradiction.detail["vecina"] == "425"
    assert contradiction.detail["mm_vecina"] == pytest.approx(1265, abs=1)
    assert CODE_COVERAGE in codes(result)  # la 425 tiene mucha menos cobertura
