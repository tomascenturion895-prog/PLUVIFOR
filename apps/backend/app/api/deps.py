"""Composición de dependencias: único lugar que conoce las implementaciones concretas."""

import hmac

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.session import get_session
from app.errors import ApiError
from app.repositories.ingestion import SqlIngestionRepository
from app.repositories.series import SqlSeriesRepository
from app.repositories.stations import SqlStationRepository
from app.services.importer import ImportService
from app.services.series import SeriesService
from app.services.stations import StationService


def get_station_service(session: Session = Depends(get_session)) -> StationService:  # noqa: B008
    return StationService(SqlStationRepository(session))


def get_series_service(
    session: Session = Depends(get_session),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> SeriesService:
    return SeriesService(SqlSeriesRepository(session), settings.data_cutoff_date)


def require_admin(
    x_api_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> None:
    """Protege las operaciones de escritura. La lectura queda pública.

    Si no hay clave configurada, la escritura queda deshabilitada (cerrado por defecto).
    """
    expected = settings.admin_api_key
    if expected is None or not expected.get_secret_value():
        raise ApiError(
            403, "forbidden", "La escritura está deshabilitada: falta configurar ADMIN_API_KEY."
        )
    if x_api_key is None or not hmac.compare_digest(
        x_api_key.encode(), expected.get_secret_value().encode()
    ):
        raise ApiError(401, "unauthorized", "Falta la clave de administración o es incorrecta.")


def get_import_service(
    session: Session = Depends(get_session),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> ImportService:
    return ImportService(
        SqlIngestionRepository(session),
        settings.data_cutoff_date,
        max_upload_bytes=settings.max_upload_bytes,
    )
