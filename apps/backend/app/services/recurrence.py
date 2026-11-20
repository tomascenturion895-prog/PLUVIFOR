from datetime import date, timedelta

from app.domain.enums import DataCategory
from app.domain.quality import DayValue
from app.domain.recurrence import MIN_OBSERVED_YEARS, ZERO_RUN_CODE, compute
from app.errors import ApiError
from app.schemas.recurrence import RecurrenceOut, YearCountOut
from app.services.series import MAX_DAYS, SeriesService

# La serie se pide por tramos de MAX_DAYS; este tope evita pedidos desmedidos.
MAX_SPAN_DAYS = MAX_DAYS * 4


class RecurrenceService:
    """Recurrencia histórica de una estación. Solo lee la serie observada, nunca otra categoría."""

    def __init__(self, series: SeriesService, cutoff: date):
        self._series = series
        self._cutoff = cutoff

    def get(self, station_id: int, date_from: date, date_to: date) -> RecurrenceOut:
        if (date_to - date_from).days + 1 > MAX_SPAN_DAYS:
            raise ApiError(
                422,
                "range_too_large",
                f"El período no puede superar {MAX_SPAN_DAYS} días.",
            )
        if date_from > self._cutoff:
            raise ApiError(
                422,
                "after_cutoff",
                f"No hay datos posteriores a la fecha de corte ({self._cutoff:%d/%m/%Y}).",
            )
        clipped = date_to > self._cutoff
        date_to = min(date_to, self._cutoff)  # nada posterior al corte (31/10/2026)
        days: list[DayValue] = []
        zero_runs: list[tuple[date, date]] = []
        first = last = None
        start = date_from
        while start <= date_to:
            end = min(start + timedelta(days=MAX_DAYS - 1), date_to)
            result = self._series.get_series(station_id, start, end, DataCategory.OBSERVADO)
            first = first or result
            days.extend(result.days)
            zero_runs.extend(
                (w.start_date, w.end_date)
                for w in result.warnings
                if w.code == ZERO_RUN_CODE and w.start_date and w.end_date
            )
            last = result
            start = end + timedelta(days=1)
        if first is None or last is None:  # date_from es posterior a date_to (o al corte)
            raise ApiError(
                422, "invalid_range", "La fecha inicial no puede ser posterior a la final."
            )
        r = compute(days, zero_runs)
        return RecurrenceOut(
            station_id=station_id,
            station_name=first.station.name,
            category=DataCategory.OBSERVADO,
            date_from=first.date_from,
            date_to=last.date_to,
            clipped_to_cutoff=clipped,
            valid_days=r.valid_days,
            observed_years=r.observed_years,
            excluded_zero_run_days=r.excluded_zero_run_days,
            gap_days=r.gap_days,
            sufficient_history=r.sufficient,
            min_observed_years=MIN_OBSERVED_YEARS,
            ge50=r.ge50,
            ge100=r.ge100,
            ge50_per_year=r.ge50_per_year,
            ge100_per_year=r.ge100_per_year,
            ge50_every_years=r.ge50_every_years,
            ge100_every_years=r.ge100_every_years,
            by_year=[YearCountOut(**vars(y)) for y in r.by_year],
        )
