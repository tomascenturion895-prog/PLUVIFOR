"""Modelos SQLAlchemy. Importarlos acá registra las tablas en `Base.metadata`."""

from app.models.alert import (
    AlertDispatch,
    AlertOutbox,
    AlertSubscription,
    AlertSubscriptionStation,
)
from app.models.climate_reference import ClimateReference
from app.models.field_report import FieldReport
from app.models.gap_estimate import GapEstimate
from app.models.import_log import ImportLog
from app.models.quality_flag import QualityFlag
from app.models.rainfall_record import RainfallRecord
from app.models.sensor_reading import SensorReading
from app.models.source import Source
from app.models.station import Station
from app.models.user import AuthSession, User

__all__ = [
    "AlertDispatch",
    "AlertSubscriptionStation",
    "AuthSession",
    "AlertOutbox",
    "AlertSubscription",
    "ClimateReference",
    "FieldReport",
    "GapEstimate",
    "ImportLog",
    "QualityFlag",
    "RainfallRecord",
    "SensorReading",
    "Source",
    "Station",
    "User",
]
