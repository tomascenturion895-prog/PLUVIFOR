"""Métricas de una serie diaria. Puras y sin framework."""

from dataclasses import dataclass
from datetime import date

from app.domain.enums import RainState
from app.domain.quality import DayValue

# Umbral de cobertura bajo el cual se advierte. Valor provisional: pendiente de confirmar.
LOW_COVERAGE_THRESHOLD = 0.8


@dataclass(frozen=True)
class Summary:
    days_in_period: int
    days_with_data: int
    days_sin_fila: int
    days_fila_sin_valor: int
    coverage: float
    # None cuando no hay ningún día con dato: «sin dato» no es 0 mm.
    accumulated_mm: float | None


def fill_calendar(days: list[DayValue], date_from: date, date_to: date) -> list[DayValue]:
    """Un valor por día del período; el día que la base no tiene figura como `sin_fila`."""
    by_date = {d.obs_date: d for d in days}
    total = (date_to - date_from).days + 1
    result: list[DayValue] = []
    for offset in range(total):
        current = date.fromordinal(date_from.toordinal() + offset)
        result.append(by_date.get(current) or DayValue(current, RainState.SIN_FILA, None))
    return result


def summarize(calendar: list[DayValue]) -> Summary:
    with_data = [d for d in calendar if d.state is RainState.DATO and d.mm is not None]
    total = len(calendar)
    return Summary(
        days_in_period=total,
        days_with_data=len(with_data),
        days_sin_fila=sum(d.state is RainState.SIN_FILA for d in calendar),
        days_fila_sin_valor=sum(d.state is RainState.FILA_SIN_VALOR for d in calendar),
        coverage=round(len(with_data) / total, 4) if total else 0.0,
        accumulated_mm=round(sum(d.mm for d in with_data), 2) if with_data else None,
    )
