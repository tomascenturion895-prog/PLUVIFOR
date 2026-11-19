from dataclasses import dataclass
from datetime import date

from app.domain.enums import DataCategory, Severity
from app.domain.metrics import LOW_COVERAGE_THRESHOLD, Summary, fill_calendar, summarize
from app.domain.quality import DayValue
from app.errors import ApiError
from app.models import Station
from app.repositories.series import SeriesRepository

MAX_DAYS = 3660  # diez años


@dataclass(frozen=True)
class Warning_:
    code: str
    message: str
    severity: Severity
    start_date: date | None = None
    end_date: date | None = None


@dataclass(frozen=True)
class SeriesResult:
    station: Station
    category: DataCategory
    date_from: date
    date_to: date
    clipped_to_cutoff: bool
    days: list[DayValue]
    summary: Summary
    warnings: list[Warning_]


class SeriesService:
    def __init__(self, repository: SeriesRepository, cutoff: date):
        self._repository = repository
        self._cutoff = cutoff

    def get_series(
        self,
        station_id: int,
        date_from: date,
        date_to: date,
        category: DataCategory = DataCategory.OBSERVADO,
    ) -> SeriesResult:
        if date_from > date_to:
            raise ApiError(
                422, "invalid_range", "La fecha inicial no puede ser posterior a la final."
            )
        if date_from > self._cutoff:
            raise ApiError(
                422,
                "after_cutoff",
                f"No hay datos posteriores a la fecha de corte ({self._cutoff:%d/%m/%Y}).",
            )
        clipped = date_to > self._cutoff
        date_to = min(date_to, self._cutoff)
        if (date_to - date_from).days + 1 > MAX_DAYS:
            raise ApiError(422, "range_too_large", f"El período no puede superar {MAX_DAYS} días.")

        station = self._repository.get_station(station_id)
        if station is None:
            raise ApiError(404, "station_not_found", "No existe la estación pedida.")

        data = self._repository.read(station_id, category, date_from, date_to)
        calendar = fill_calendar(data.days, date_from, date_to)
        summary = summarize(calendar)
        warnings = self._warnings(station, summary, data.unvalidated_days, date_from, date_to)
        return SeriesResult(
            station, category, date_from, date_to, clipped, calendar, summary, warnings
        )

    def _warnings(
        self, station: Station, summary: Summary, unvalidated: int, date_from: date, date_to: date
    ) -> list[Warning_]:
        warnings: list[Warning_] = []
        for flag in self._repository.flags(station.id, date_from, date_to):
            warnings.append(
                Warning_(
                    code=flag.code,
                    message=(
                        "Racha de 60 días o más con 0 mm: puede ser un sensor sin registrar, "
                        "no ausencia de lluvia. No se da por buena."
                        if flag.code == "ceros_prolongados"
                        else "Advertencia de calidad."
                    ),
                    severity=flag.severity,
                    start_date=flag.start_date,
                    end_date=flag.end_date,
                )
            )
        if summary.coverage < LOW_COVERAGE_THRESHOLD:
            warnings.append(
                Warning_(
                    code="cobertura_baja",
                    message=(
                        f"Solo {summary.coverage:.0%} de los días tiene dato: "
                        "el acumulado puede quedar por debajo de lo que llovió."
                    ),
                    severity=Severity.AVISO,
                )
            )
        if unvalidated:
            warnings.append(
                Warning_(
                    code="dato_sin_validar",
                    message="Los datos de este período no pasaron una validación externa.",
                    severity=Severity.AVISO,
                )
            )
        return warnings
