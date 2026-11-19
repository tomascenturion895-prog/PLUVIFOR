"""Modelos SQLAlchemy. Importarlos acá registra las tablas en `Base.metadata`."""

from app.models.climate_reference import ClimateReference
from app.models.field_report import FieldReport
from app.models.import_log import ImportLog
from app.models.quality_flag import QualityFlag
from app.models.rainfall_record import RainfallRecord
from app.models.sensor_reading import SensorReading
from app.models.source import Source
from app.models.station import Station

__all__ = [
    "ClimateReference",
    "FieldReport",
    "ImportLog",
    "QualityFlag",
    "RainfallRecord",
    "SensorReading",
    "Source",
    "Station",
]
