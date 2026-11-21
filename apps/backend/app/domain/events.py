"""Eventos de lluvia intensa y rachas secas de una serie diaria. Descriptivo: no predice nada.

Regla central: un hueco no es 0 mm. Un día sin dato no es un día seco: no suma a una racha seca
y la corta. Un día con dato y 0 mm sí es seco.
"""

from dataclasses import dataclass
from datetime import date

from app.domain.enums import RainState
from app.domain.quality import DayValue

LEVEL_50 = 50.0
LEVEL_100 = 100.0
ZERO_RUN_CODE = "ceros_prolongados"


@dataclass(frozen=True)
class IntenseDay:
    obs_date: date
    mm: float


@dataclass(frozen=True)
class DryStreak:
    start_date: date
    end_date: date
    days: int
    # La racha toca un período con la advertencia de ceros prolongados: puede ser un sensor
    # sin registrar, no ausencia de lluvia. No se da por buena.
    zero_run_warning: bool


@dataclass(frozen=True)
class EventsAnalysis:
    ge50: list[IntenseDay]  # incluye los días de 100 mm o más
    ge100: list[IntenseDay]
    dry_streaks: list[DryStreak]  # solo las de al menos `min_dry_days`
    longest: DryStreak | None  # la más larga del período, sin importar `min_dry_days`


def analyze(
    days: list[DayValue], zero_runs: list[tuple[date, date]], min_dry_days: int
) -> EventsAnalysis:
    ge50: list[IntenseDay] = []
    ge100: list[IntenseDay] = []
    streaks: list[DryStreak] = []
    longest: DryStreak | None = None
    run_start: date | None = None
    run_end: date | None = None
    run_days = 0

    def flush() -> None:
        nonlocal run_start, run_end, run_days, longest
        if run_start is None or run_end is None:
            return
        touches = any(run_end >= a and run_start <= b for a, b in zero_runs)
        streak = DryStreak(run_start, run_end, run_days, touches)
        if longest is None or streak.days > longest.days:
            longest = streak
        if streak.days >= min_dry_days:
            streaks.append(streak)
        run_start = run_end = None
        run_days = 0

    for d in days:
        if d.state is not RainState.DATO or d.mm is None:
            flush()  # un hueco corta la racha y no cuenta como seco
            continue
        if d.mm >= LEVEL_50:
            ge50.append(IntenseDay(d.obs_date, d.mm))
        if d.mm >= LEVEL_100:
            ge100.append(IntenseDay(d.obs_date, d.mm))
        if d.mm != 0:
            flush()
            continue
        if run_start is None:
            run_start = d.obs_date
        run_end = d.obs_date
        run_days += 1
    flush()
    return EventsAnalysis(ge50, ge100, streaks, longest)
