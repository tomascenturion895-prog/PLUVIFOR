from dataclasses import dataclass
from datetime import date

from app.domain.enums import DataCategory
from app.domain.report import IntenseEvent, StationBlock, compose_text, intense_events
from app.domain.warnings import (
    CategoryRule,
    CoverageGapRule,
    CutoffHourRule,
    NeighborConsistencyRule,
    NotApplied,
    SeriesInput,
    evaluate_warnings,
)
from app.errors import ApiError
from app.services.series import SeriesResult, SeriesService, Warning_

MAX_STATIONS = 20

# Reglas que comparan estaciones entre sí. Las de una sola serie (ceros, sin validar, cobertura
# baja) ya vienen en las advertencias de cada estación.
GROUP_RULES = (CutoffHourRule(), CategoryRule(), CoverageGapRule())
NEIGHBOR_RULES = (NeighborConsistencyRule(),)


@dataclass(frozen=True)
class StationReport:
    result: SeriesResult
    events: list[IntenseEvent]
    warnings: list[Warning_]


@dataclass(frozen=True)
class ReportResult:
    category: DataCategory
    date_from: date
    date_to: date
    cutoff: date
    clipped_to_cutoff: bool
    stations: list[StationReport]
    comparability: list[Warning_]
    not_evaluated: list[NotApplied]
    text: str


class ReportService:
    def __init__(self, series: SeriesService, cutoff: date):
        self._series = series
        self._cutoff = cutoff

    def build(
        self,
        station_ids: list[int],
        date_from: date,
        date_to: date,
        category: DataCategory = DataCategory.OBSERVADO,
    ) -> ReportResult:
        unique = list(dict.fromkeys(station_ids))
        if not unique:
            raise ApiError(422, "no_stations", "Elegí al menos una estación.")
        if len(unique) > MAX_STATIONS:
            raise ApiError(
                422, "too_many_stations", f"Se pueden pedir hasta {MAX_STATIONS} estaciones."
            )
        results = [self._series.get_series(sid, date_from, date_to, category) for sid in unique]
        inputs = [self._input(r) for r in results]

        group, not_evaluated = self._group_advisories(inputs)
        stations = [
            StationReport(
                result=r,
                events=intense_events(r.days),
                warnings=[*r.warnings, *self._neighbor_warnings(inputs, i)],
            )
            for i, r in enumerate(results)
        ]
        first = results[0]
        clipped = any(r.clipped_to_cutoff for r in results)
        text = compose_text(
            category=category,
            date_from=first.date_from,
            date_to=first.date_to,
            cutoff=self._cutoff,
            clipped=clipped,
            stations=[
                StationBlock(
                    name=s.result.station.name,
                    source_name=s.result.station.source.name,
                    network=s.result.station.source.network,
                    summary=s.result.summary,
                    events=s.events,
                    warning_messages=[w.message for w in s.warnings],
                )
                for s in stations
            ],
            comparability=[w.message for w in group],
        )
        return ReportResult(
            category, first.date_from, first.date_to, self._cutoff, clipped,
            stations, group, not_evaluated, text,
        )  # fmt: skip

    @staticmethod
    def _input(result: SeriesResult) -> SeriesInput:
        station = result.station
        return SeriesInput(
            station_code=station.code,
            category=result.category,
            days=result.days,
            day_cutoff_local=station.source.day_cutoff_local,
            lat=station.lat,
            lon=station.lon,
        )

    @staticmethod
    def _group_advisories(inputs: list[SeriesInput]) -> tuple[list[Warning_], list[NotApplied]]:
        if len(inputs) < 2:
            return [], []
        evaluation = evaluate_warnings(inputs[0], inputs[1:], GROUP_RULES)
        warnings = [Warning_(a.code, a.message, a.severity) for a in evaluation.advisories]
        return warnings, list(evaluation.not_applied)

    @staticmethod
    def _neighbor_warnings(inputs: list[SeriesInput], index: int) -> list[Warning_]:
        if len(inputs) < 2:
            return []
        others = [x for i, x in enumerate(inputs) if i != index]
        evaluation = evaluate_warnings(inputs[index], others, NEIGHBOR_RULES)
        return [
            Warning_(a.code, a.message, a.severity, a.start_date, a.end_date)
            for a in evaluation.advisories
        ]
