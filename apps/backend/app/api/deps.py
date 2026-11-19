"""Composición de dependencias: único lugar que conoce las implementaciones concretas."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.session import get_session
from app.repositories.series import SqlSeriesRepository
from app.repositories.stations import SqlStationRepository
from app.services.series import SeriesService
from app.services.stations import StationService


def get_station_service(session: Session = Depends(get_session)) -> StationService:  # noqa: B008
    return StationService(SqlStationRepository(session))


def get_series_service(
    session: Session = Depends(get_session),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> SeriesService:
    return SeriesService(SqlSeriesRepository(session), settings.data_cutoff_date)
