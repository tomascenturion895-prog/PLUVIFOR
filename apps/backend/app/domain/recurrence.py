"""Recurrencia histórica de días de lluvia intensa. **Descriptiva: no es una predicción.**

Cuenta cuántas veces una estación registró 50 mm o más (y 100 mm o más) en un día y cada cuánto,
en promedio, ocurrió *en el pasado observado*. No proyecta nada hacia adelante ni dice qué va a
pasar: la frecuencia pasada no garantiza la futura.

Reglas de integridad:
- Un hueco (`sin_fila` o `fila_sin_valor`) no es un día de lluvia ni un día seco: no entra en el
  conteo ni en el período observado.
- Los días con dato dentro de una racha de ceros prolongados (advertencia `ceros_prolongados`) se
  excluyen: pueden ser un sensor sin registrar, y contarlos achicaría la frecuencia real.
- Con menos de `MIN_OBSERVED_YEARS` años de días con dato válido no se calcula ninguna frecuencia.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from app.domain.enums import RainState
from app.domain.quality import DayValue

# Umbrales de lluvia intensa en mm por día (AGENTS.md), los mismos de GET /api/events.
UMBRAL_INTENSO_MM = 50.0
UMBRAL_MUY_INTENSO_MM = 100.0
DAYS_PER_YEAR = 365.25
# Con menos historia que esto, una frecuencia sería ruido: se informa el conteo y nada más.
MIN_OBSERVED_YEARS = 5.0
ZERO_RUN_CODE = "ceros_prolongados"


@dataclass(frozen=True)
class YearCount:
    year: int
    valid_days: int
    ge50: int
    ge100: int


@dataclass(frozen=True)
class Recurrence:
    valid_days: int
    excluded_zero_run_days: int
    gap_days: int
    observed_years: float
    sufficient: bool
    ge50: int
    ge100: int
    # Eventos por año observado y años entre eventos. None si falta historia o no hubo eventos.
    ge50_per_year: float | None
    ge100_per_year: float | None
    ge50_every_years: float | None
    ge100_every_years: float | None
    by_year: list[YearCount]


def _in_ranges(day: date, ranges: list[tuple[date, date]]) -> bool:
    return any(start <= day <= end for start, end in ranges)


def _rate(count: int, years: float, sufficient: bool) -> tuple[float | None, float | None]:
    if not sufficient or count == 0:
        return None, None
    return round(count / years, 3), round(years / count, 1)


def compute(days: list[DayValue], zero_runs: list[tuple[date, date]]) -> Recurrence:
    """`days` es la serie diaria ya completada (un valor por día, con los huecos como tales)."""
    valid: dict[int, list[float]] = defaultdict(list)
    excluded = gaps = 0
    for d in days:
        if d.state is not RainState.DATO or d.mm is None:
            gaps += 1  # un hueco no es 0 mm: ni cuenta ni resta
            continue
        if _in_ranges(d.obs_date, zero_runs):
            excluded += 1
            continue
        valid[d.obs_date.year].append(d.mm)

    by_year = [
        YearCount(
            year=year,
            valid_days=len(values),
            ge50=sum(v >= UMBRAL_INTENSO_MM for v in values),
            ge100=sum(v >= UMBRAL_MUY_INTENSO_MM for v in values),
        )
        for year, values in sorted(valid.items())
    ]
    valid_days = sum(y.valid_days for y in by_year)
    years = valid_days / DAYS_PER_YEAR
    sufficient = years >= MIN_OBSERVED_YEARS
    ge50 = sum(y.ge50 for y in by_year)
    ge100 = sum(y.ge100 for y in by_year)
    per50, every50 = _rate(ge50, years, sufficient)
    per100, every100 = _rate(ge100, years, sufficient)
    return Recurrence(
        valid_days=valid_days,
        excluded_zero_run_days=excluded,
        gap_days=gaps,
        observed_years=round(years, 2),
        sufficient=sufficient,
        ge50=ge50,
        ge100=ge100,
        ge50_per_year=per50,
        ge100_per_year=per100,
        ge50_every_years=every50,
        ge100_every_years=every100,
        by_year=by_year,
    )
