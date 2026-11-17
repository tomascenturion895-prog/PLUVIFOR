"""Composición de dependencias: único lugar que conoce las implementaciones concretas."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.repositories.stations import SqlStationRepository
from app.services.stations import StationService


def get_station_service(session: Session = Depends(get_session)) -> StationService:  # noqa: B008
    return StationService(SqlStationRepository(session))
