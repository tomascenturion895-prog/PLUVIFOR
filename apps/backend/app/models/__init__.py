"""Modelos SQLAlchemy. Importarlos acá registra las tablas en `Base.metadata`."""

from app.models.climate_reference import ClimateReference
from app.models.import_log import ImportLog
from app.models.quality_flag import QualityFlag
from app.models.rainfall_record import RainfallRecord
from app.models.source import Source
from app.models.station import Station

__all__ = [
    "ClimateReference",
    "ImportLog",
    "QualityFlag",
    "RainfallRecord",
    "Source",
    "Station",
]
