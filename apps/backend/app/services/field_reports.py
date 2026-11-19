from datetime import date

from app.domain.enums import DataCategory, LocationSource, ReportLocation, Validation
from app.errors import ApiError
from app.models import FieldReport
from app.repositories.field_reports import FieldReportRepository
from app.schemas.field_reports import FieldReportIn

SOURCE = "reporte_policial"


class FieldReportService:
    """Carga de reportes de campo. Un reporte nunca se confunde con una lectura de estación."""

    def __init__(self, repository: FieldReportRepository, cutoff: date):
        self._repository = repository
        self._cutoff = cutoff

    def create(self, data: FieldReportIn) -> FieldReport:
        if data.obs_date > self._cutoff:
            raise ApiError(
                422,
                "date_after_cutoff",
                f"La fecha no puede ser posterior al corte de datos ({self._cutoff:%d/%m/%Y}).",
            )
        informed = data.lat is not None
        return self._repository.add(
            FieldReport(
                obs_date=data.obs_date,
                mm=data.mm,
                place=data.place,
                reporter=data.reporter,
                lat=data.lat,
                lon=data.lon,
                location_status=ReportLocation.INFORMADA if informed else ReportLocation.PENDIENTE,
                # Si hay ubicación y no dicen de dónde salió, se asume la cargada a mano.
                location_source=(data.location_source or LocationSource.MANUAL)
                if informed
                else None,
                category=DataCategory.OBSERVADO,
                validation=Validation.SIN_VALIDAR,
                source=SOURCE,
            )
        )

    def latest(self, limit: int, offset: int) -> tuple[list[FieldReport], int]:
        return self._repository.latest(limit, offset)
