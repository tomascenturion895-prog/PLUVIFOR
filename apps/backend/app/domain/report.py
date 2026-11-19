"""Parte pluvial: eventos intensos y texto en español. Módulo puro, sin base ni framework.

El parte describe lo que pasó; no predice ni indica riesgo. Un día sin dato nunca cuenta como
0 mm y los acumulados de estaciones distintas nunca se suman entre sí.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from app.domain.enums import DataCategory, RainState
from app.domain.metrics import Summary
from app.domain.quality import DayValue

INTENSE_LEVELS_MM = (50.0, 100.0)  # umbrales descriptivos del proyecto (≥50 y ≥100 mm)
NOTICE = "PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial"


@dataclass(frozen=True)
class IntenseEvent:
    obs_date: date
    mm: float
    level_mm: float  # el umbral más alto que alcanza el día


def intense_events(days: Sequence[DayValue]) -> list[IntenseEvent]:
    """Días con dato que alcanzan algún umbral. Un hueco nunca es un evento."""
    events: list[IntenseEvent] = []
    for day in days:
        if day.state is not RainState.DATO or day.mm is None:
            continue
        reached = [level for level in INTENSE_LEVELS_MM if day.mm >= level]
        if reached:
            events.append(IntenseEvent(day.obs_date, day.mm, max(reached)))
    return events


def fmt_date(value: date) -> str:
    return f"{value:%d/%m/%Y}"


def fmt_mm(value: float) -> str:
    return f"{value:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".") + " mm"


@dataclass(frozen=True)
class StationBlock:
    """Todo lo que el texto necesita de una estación."""

    name: str
    source_name: str
    network: str
    summary: Summary
    events: Sequence[IntenseEvent]
    warning_messages: Sequence[str]


def _station_text(block: StationBlock) -> str:
    s = block.summary
    lines = [f"{block.name} ({block.source_name}, {block.network})"]
    if s.accumulated_mm is None:
        lines.append(
            "  Sin datos en el período: no se puede informar un acumulado. "
            "Eso no significa que no haya llovido."
        )
    else:
        lines.append(
            f"  Acumulado: {fmt_mm(s.accumulated_mm)} en {s.days_with_data} de "
            f"{s.days_in_period} días (cobertura {s.coverage:.0%})."
        )
    gaps = s.days_sin_fila + s.days_fila_sin_valor
    if gaps:
        lines.append(
            f"  {gaps} {'día' if gaps == 1 else 'días'} sin dato "
            f"({s.days_sin_fila} sin fila, {s.days_fila_sin_valor} con fila sin valor): "
            "no se cuentan como 0 mm."
        )
    if block.events:
        detail = "; ".join(
            f"{e.obs_date:%d/%m} {fmt_mm(e.mm)} (≥{e.level_mm:g} mm)" for e in block.events
        )
        lines.append(f"  Eventos intensos: {detail}.")
    for message in block.warning_messages:
        lines.append(f"  ⚠ {message}")
    return "\n".join(lines)


def compose_text(
    *,
    category: DataCategory,
    date_from: date,
    date_to: date,
    cutoff: date,
    clipped: bool,
    stations: Sequence[StationBlock],
    comparability: Sequence[str],
) -> str:
    head = [
        "PARTE PLUVIAL · Formosa",
        f"Período: {fmt_date(date_from)} al {fmt_date(date_to)}. "
        f"Fecha de corte de los datos: {fmt_date(cutoff)}.",
        f"Categoría: {category.value}.",
    ]
    if clipped:
        head.append(
            f"El período pedido pasaba la fecha de corte y se recortó al {fmt_date(cutoff)}."
        )
    body = [_station_text(block) for block in stations]
    foot: list[str] = []
    if len(stations) > 1:
        foot.append("Los acumulados de estaciones distintas no se suman entre sí.")
    foot.extend(f"⚠ {message}" for message in comparability)
    foot.append(NOTICE)
    return "\n\n".join(["\n".join(head), *body, "\n".join(foot)])
