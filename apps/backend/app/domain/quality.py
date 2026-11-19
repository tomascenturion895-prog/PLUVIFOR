"""Reglas de calidad del dato. Puras: sin base de datos ni framework."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta

from app.domain.enums import RainState

ZERO_STREAK_CODE = "ceros_prolongados"
ZERO_STREAK_MIN_DAYS = 60
ZERO_STREAK_RULE_VERSION = "ceros_prolongados/1"


@dataclass(frozen=True)
class DayValue:
    obs_date: date
    state: RainState
    mm: float | None


@dataclass(frozen=True)
class Streak:
    start: date
    end: date

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1


def find_zero_streaks(
    days: Iterable[DayValue], min_days: int = ZERO_STREAK_MIN_DAYS
) -> list[Streak]:
    """Tramos de `min_days` o más días corridos con 0 mm.

    Solo cuenta un `dato` igual a 0. Un hueco (`sin_fila` o `fila_sin_valor`) corta el tramo:
    no se puede afirmar que no llovió un día del que no hay dato.
    """
    streaks: list[Streak] = []
    start: date | None = None
    previous: date | None = None

    def close() -> None:
        if start is not None and previous is not None:
            streak = Streak(start, previous)
            if streak.days >= min_days:
                streaks.append(streak)

    for day in sorted(days, key=lambda d: d.obs_date):
        is_zero = day.state is RainState.DATO and day.mm == 0
        contiguous = previous is not None and day.obs_date - previous == timedelta(days=1)
        if is_zero and start is not None and contiguous:
            previous = day.obs_date
            continue
        close()
        start, previous = (day.obs_date, day.obs_date) if is_zero else (None, None)
    close()
    return streaks
