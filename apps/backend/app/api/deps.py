"""Composición de dependencias: único lugar que conoce las implementaciones concretas."""

import hmac
from dataclasses import dataclass

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.session import get_session
from app.domain.auth import STAFF_ROLES, Role
from app.errors import ApiError
from app.models import User
from app.repositories.alerts import SqlAlertRepository
from app.repositories.field_reports import SqlFieldReportRepository
from app.repositories.gap_estimates import SqlGapEstimateRepository
from app.repositories.ingestion import SqlIngestionRepository
from app.repositories.network_health import SqlNetworkHealthRepository
from app.repositories.quality import SqlQualityRepository
from app.repositories.references import SqlReferenceRepository
from app.repositories.sensor_readings import SqlSensorReadingRepository
from app.repositories.series import SqlSeriesRepository
from app.repositories.stations import SqlStationRepository
from app.repositories.users import SqlUserRepository
from app.services.alerts import AlertService
from app.services.auth import AuthService
from app.services.field_reports import FieldReportService
from app.services.gap_estimation import GapEstimationService
from app.services.importer import ImportService
from app.services.network_health import NetworkHealthService
from app.services.quality import QualityService
from app.services.references import ReferenceService
from app.services.report import ReportService
from app.services.sensor_readings import SensorReadingService
from app.services.series import SeriesService
from app.services.stations import StationService


def get_station_service(session: Session = Depends(get_session)) -> StationService:  # noqa: B008
    return StationService(SqlStationRepository(session))


def get_series_service(
    session: Session = Depends(get_session),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> SeriesService:
    return SeriesService(SqlSeriesRepository(session), settings.data_cutoff_date)


def get_field_report_service(
    session: Session = Depends(get_session),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> FieldReportService:
    return FieldReportService(SqlFieldReportRepository(session), settings.data_cutoff_date)


def get_gap_estimation_service(
    session: Session = Depends(get_session),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> GapEstimationService:
    return GapEstimationService(SqlGapEstimateRepository(session), settings.data_cutoff_date)


def get_network_health_service(
    session: Session = Depends(get_session),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> NetworkHealthService:
    return NetworkHealthService(SqlNetworkHealthRepository(session), settings.data_cutoff_date)


@dataclass(frozen=True)
class Actor:
    """Quién escribe: una cuenta (`user_id`) o la clave de administración."""

    user_id: int | None
    via: str  # «sesion» o «clave»


def get_auth_service(
    session: Session = Depends(get_session),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> AuthService:
    return AuthService(
        SqlUserRepository(session),
        settings.session_hours,
        settings.registration_open,
    )


def bearer_token(authorization: str | None) -> str | None:
    if authorization is None:
        return None
    esquema, _, token = authorization.partition(" ")
    return token.strip() or None if esquema.lower() == "bearer" else None


def current_user(
    authorization: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),  # noqa: B008
) -> User | None:
    """La cuenta de la sesión (`Authorization: Bearer ...`), o None si no hay una vigente."""
    token = bearer_token(authorization)
    return auth.authenticate(token) if token else None


def require_user(user: User | None = Depends(current_user)) -> User:  # noqa: B008
    if user is None:
        raise ApiError(401, "unauthorized", "Iniciá sesión para hacer esto.")
    return user


def require_role(*roles: Role):
    """Exige una sesión vigente con alguno de esos roles (la clave de administración no alcanza)."""

    def _check(user: User = Depends(require_user)) -> User:  # noqa: B008
        if user.role not in roles:
            raise ApiError(403, "forbidden", "Tu cuenta no tiene permiso para hacer esto.")
        return user

    return _check


def require_admin(
    x_api_key: str | None = Header(default=None),
    user: User | None = Depends(current_user),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> Actor:
    """Protege las operaciones de escritura. La lectura queda pública.

    Pasa quien tenga una sesión de operador o administrador, o la clave de administración. Si no hay
    ninguna de las dos formas disponibles, la escritura queda deshabilitada (cerrado por defecto).
    """
    if user is not None and user.role in STAFF_ROLES:
        return Actor(user.id, "sesion")
    expected = settings.admin_api_key
    key_enabled = expected is not None and expected.get_secret_value() != ""
    if (
        key_enabled
        and x_api_key is not None
        and hmac.compare_digest(x_api_key.encode(), expected.get_secret_value().encode())
    ):
        return Actor(None, "clave")
    if user is not None:
        raise ApiError(403, "forbidden", "Tu cuenta no tiene permiso para hacer esto.")
    if not key_enabled:
        raise ApiError(
            403,
            "forbidden",
            "La escritura está deshabilitada: falta configurar ADMIN_API_KEY o iniciar sesión.",
        )
    raise ApiError(401, "unauthorized", "Falta la clave de administración o es incorrecta.")


def get_sensor_reading_service(
    session: Session = Depends(get_session),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> SensorReadingService:
    return SensorReadingService(SqlSensorReadingRepository(session), settings.data_cutoff_date)


def require_device(
    x_device_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> None:
    """Autentica a los dispositivos que envían lecturas. Cerrado por defecto, como la escritura."""
    expected = settings.device_api_key
    if expected is None or not expected.get_secret_value():
        raise ApiError(
            403, "forbidden", "La ingesta está deshabilitada: falta configurar DEVICE_API_KEY."
        )
    if x_device_key is None or not hmac.compare_digest(
        x_device_key.encode(), expected.get_secret_value().encode()
    ):
        raise ApiError(401, "unauthorized", "Falta la clave del dispositivo o es incorrecta.")


def get_import_service(
    session: Session = Depends(get_session),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> ImportService:
    return ImportService(
        SqlIngestionRepository(session),
        settings.data_cutoff_date,
        max_upload_bytes=settings.max_upload_bytes,
    )


def get_report_service(
    session: Session = Depends(get_session),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> ReportService:
    series = SeriesService(SqlSeriesRepository(session), settings.data_cutoff_date)
    return ReportService(series, settings.data_cutoff_date)


def get_quality_service(
    session: Session = Depends(get_session),  # noqa: B008
) -> QualityService:
    return QualityService(SqlQualityRepository(session))


def get_reference_service(session: Session = Depends(get_session)) -> ReferenceService:  # noqa: B008
    return ReferenceService(SqlReferenceRepository(session))


def get_alert_service(
    session: Session = Depends(get_session),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> AlertService:
    secret = settings.alerts_secret.get_secret_value() if settings.alerts_secret else None
    return AlertService(
        SqlAlertRepository(session),
        SeriesService(SqlSeriesRepository(session), settings.data_cutoff_date),
        secret,
        settings.data_cutoff_date,
        demo=settings.alerts_demo,
    )
