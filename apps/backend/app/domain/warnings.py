"""Las seis advertencias de comparabilidad. Módulo puro: sin base de datos ni framework.

Cada regla es independiente y se registra en `DEFAULT_RULES`: sumar una advertencia nueva es
agregar una clase, sin tocar las demás (abierto a extensión, cerrado a modificación).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Protocol

from app.domain.enums import DataCategory, RainState, Severity
from app.domain.quality import (
    ZERO_STREAK_CODE,
    ZERO_STREAK_MIN_DAYS,
    DayValue,
    find_zero_streaks,
)

# Valores provisionales, pendientes de confirmar con la mentoría.
COVERAGE_GAP_THRESHOLD = 0.2  # diferencia de cobertura entre series a partir de la cual se avisa
NEIGHBOR_RADIUS_KM = 150.0  # «vecina»: estación con coordenadas dentro de este radio
NEIGHBOR_MIN_MM = 50.0  # lluvia de la vecina en el tramo para considerar la inconsistencia
NEIGHBOR_MIN_COVERAGE = 0.5  # la vecina debe tener dato en al menos esta parte del tramo

CODE_CUTOFF = "horario_corte_distinto"
CODE_CATEGORY = "observado_vs_estimado"
CODE_COVERAGE = "cobertura_despareja"
CODE_UNVALIDATED = "dato_sin_validar"
CODE_ZERO_STREAK = ZERO_STREAK_CODE
CODE_NEIGHBORS = "inconsistente_con_vecinas"


@dataclass(frozen=True)
class SeriesInput:
    """Una serie diaria lista para evaluar (el período ya está completo, día por día)."""

    station_code: str
    category: DataCategory
    days: Sequence[DayValue]
    day_cutoff_local: str | None = None  # «07:00» / «09:00»; None = desconocido
    lat: float | None = None
    lon: float | None = None
    unvalidated_days: int = 0

    @property
    def coverage(self) -> float:
        if not self.days:
            return 0.0
        with_data = sum(d.state is RainState.DATO for d in self.days)
        return with_data / len(self.days)


@dataclass(frozen=True)
class Advisory:
    code: str
    message: str
    severity: Severity = Severity.AVISO
    start_date: date | None = None
    end_date: date | None = None
    detail: dict = field(default_factory=dict)


@dataclass(frozen=True)
class NotApplied:
    """La regla no se pudo evaluar. Se informa: callar sería hacer pasar un «no sé» por «ok»."""

    code: str
    reason: str


@dataclass(frozen=True)
class Evaluation:
    advisories: list[Advisory]
    not_applied: list[NotApplied]


class Rule(Protocol):
    code: str

    def evaluate(
        self, target: SeriesInput, others: Sequence[SeriesInput]
    ) -> list[Advisory] | NotApplied: ...


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia entre dos puntos (fórmula de haversine)."""
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlmb = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class CutoffHourRule:
    code = CODE_CUTOFF

    def evaluate(
        self, target: SeriesInput, others: Sequence[SeriesInput]
    ) -> list[Advisory] | NotApplied:
        if not others:
            return []
        if target.day_cutoff_local is None or any(o.day_cutoff_local is None for o in others):
            return NotApplied(self.code, "Falta el horario de corte de alguna de las redes.")
        cutoffs = {target.day_cutoff_local, *(o.day_cutoff_local for o in others)}
        if len(cutoffs) == 1:
            return []
        return [
            Advisory(
                self.code,
                "Las redes cierran el «día» de lluvia a horas distintas: "
                "comparar día contra día puede dar diferencias que no son reales.",
                detail={"cortes": sorted(cutoffs)},
            )
        ]


class CategoryRule:
    code = CODE_CATEGORY

    def evaluate(
        self, target: SeriesInput, others: Sequence[SeriesInput]
    ) -> list[Advisory] | NotApplied:
        categories = {target.category, *(o.category for o in others)}
        if len(categories) == 1:
            return []
        return [
            Advisory(
                self.code,
                "Se están comparando series de distinta categoría (observado, referencia, "
                "estimado). No se suman ni se promedian entre sí.",
                detail={"categorias": sorted(c.value for c in categories)},
            )
        ]


class CoverageGapRule:
    code = CODE_COVERAGE

    def evaluate(
        self, target: SeriesInput, others: Sequence[SeriesInput]
    ) -> list[Advisory] | NotApplied:
        if not others:
            return []
        values = [target.coverage, *(o.coverage for o in others)]
        if max(values) - min(values) < COVERAGE_GAP_THRESHOLD:
            return []
        return [
            Advisory(
                self.code,
                "Las series tienen cobertura despareja: el acumulado de la que tiene menos "
                "datos puede quedar por debajo de lo que llovió.",
                detail={
                    "cobertura_min": round(min(values), 4),
                    "cobertura_max": round(max(values), 4),
                },
            )
        ]


class UnvalidatedRule:
    code = CODE_UNVALIDATED

    def evaluate(
        self, target: SeriesInput, others: Sequence[SeriesInput]
    ) -> list[Advisory] | NotApplied:
        total = target.unvalidated_days + sum(o.unvalidated_days for o in others)
        if total == 0:
            return []
        return [
            Advisory(
                self.code,
                "Hay días con dato que no pasaron una validación externa.",
                detail={"dias_sin_validar": total},
            )
        ]


class ZeroStreakRule:
    code = CODE_ZERO_STREAK

    def evaluate(
        self, target: SeriesInput, others: Sequence[SeriesInput]
    ) -> list[Advisory] | NotApplied:
        return [
            Advisory(
                self.code,
                f"{s.days} días seguidos con 0 mm: puede ser un sensor sin registrar y no "
                "ausencia de lluvia. No se da por bueno.",
                start_date=s.start,
                end_date=s.end,
                detail={"days": s.days, "min_days": ZERO_STREAK_MIN_DAYS},
            )
            for s in find_zero_streaks(target.days)
        ]


class NeighborConsistencyRule:
    """Una racha de ceros contradicha por una estación vecina que sí registró lluvia."""

    code = CODE_NEIGHBORS

    def evaluate(
        self, target: SeriesInput, others: Sequence[SeriesInput]
    ) -> list[Advisory] | NotApplied:
        if target.lat is None or target.lon is None:
            return NotApplied(self.code, "La estación no tiene coordenadas verificadas.")
        neighbors = [
            (o, distance_km(target.lat, target.lon, o.lat, o.lon))
            for o in others
            if o.lat is not None
            and o.lon is not None
            and o.category == target.category
            and o.station_code != target.station_code
        ]
        neighbors = [(o, km) for o, km in neighbors if km <= NEIGHBOR_RADIUS_KM]
        if not neighbors:
            return NotApplied(self.code, "No hay estaciones vecinas con coordenadas en el radio.")

        advisories: list[Advisory] = []
        for streak in find_zero_streaks(target.days):
            for neighbor, km in sorted(neighbors, key=lambda item: item[1]):
                mm, coverage = _rain_between(neighbor.days, streak.start, streak.end)
                if coverage >= NEIGHBOR_MIN_COVERAGE and mm >= NEIGHBOR_MIN_MM:
                    advisories.append(
                        Advisory(
                            self.code,
                            f"La estación marca 0 mm, pero la vecina {neighbor.station_code} "
                            f"(a {km:.0f} km) registró {mm:g} mm en el mismo tramo.",
                            severity=Severity.ALERTA,
                            start_date=streak.start,
                            end_date=streak.end,
                            detail={
                                "vecina": neighbor.station_code,
                                "distancia_km": round(km, 1),
                                "mm_vecina": round(mm, 2),
                                "cobertura_vecina": round(coverage, 4),
                            },
                        )
                    )
                    break
        return advisories


def _rain_between(days: Sequence[DayValue], start: date, end: date) -> tuple[float, float]:
    total = (end - start).days + 1
    inside = [d for d in days if start <= d.obs_date <= end]
    with_data = [d for d in inside if d.state is RainState.DATO and d.mm is not None]
    return sum(d.mm for d in with_data), len(with_data) / total


DEFAULT_RULES: tuple[Rule, ...] = (
    CutoffHourRule(),
    CategoryRule(),
    CoverageGapRule(),
    UnvalidatedRule(),
    ZeroStreakRule(),
    NeighborConsistencyRule(),
)


def evaluate_warnings(
    target: SeriesInput,
    others: Sequence[SeriesInput] = (),
    rules: Sequence[Rule] = DEFAULT_RULES,
) -> Evaluation:
    advisories: list[Advisory] = []
    not_applied: list[NotApplied] = []
    for rule in rules:
        outcome = rule.evaluate(target, others)
        if isinstance(outcome, NotApplied):
            not_applied.append(outcome)
        else:
            advisories.extend(outcome)
    return Evaluation(advisories, not_applied)
