from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.enums import SensorCategory
from app.models._types import text_enum


class SensorReading(Base):
    """Lectura enviada por un dispositivo. Hoy solo simulada: no hay sensores reales.

    Va en su propia tabla y nunca se suma a las series de las estaciones. Una lectura que no
    llegó simplemente no existe: no se guarda un 0 ni un vacío en su lugar.
    """

    __tablename__ = "sensor_readings"
    __table_args__ = (
        UniqueConstraint("device_id", "read_at"),
        CheckConstraint("mm >= 0", name="mm_non_negative"),
        CheckConstraint("(lat IS NULL) = (lon IS NULL)", name="location_complete"),
        CheckConstraint("lat IS NULL OR (lat BETWEEN -90 AND 90)", name="lat_range"),
        CheckConstraint("lon IS NULL OR (lon BETWEEN -180 AND 180)", name="lon_range"),
        Index("ix_sensor_readings_read_at", "read_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64))
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    mm: Mapped[float] = mapped_column(Numeric(8, 2, asdecimal=False))
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    category: Mapped[SensorCategory] = mapped_column(
        text_enum(SensorCategory, "sensor_reading_category"), default=SensorCategory.SIMULADO
    )
    source: Mapped[str] = mapped_column(String(64), default="sensor_simulado")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
