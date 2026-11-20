from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import SensorReading


@dataclass(frozen=True)
class DeviceSummary:
    """Resumen de un dispositivo: cuántas lecturas tiene y cuál fue la última."""

    device_id: str
    readings: int
    first_read_at: datetime
    last_read_at: datetime
    last_mm: float


class SensorReadingRepository(Protocol):
    def add(self, reading: SensorReading) -> SensorReading: ...

    def find(self, device_id: str, read_at: datetime) -> SensorReading | None: ...

    def latest(
        self, limit: int, offset: int, device_id: str | None
    ) -> tuple[list[SensorReading], int]: ...

    def devices(self) -> list[DeviceSummary]: ...


class SqlSensorReadingRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, reading: SensorReading) -> SensorReading:
        self._session.add(reading)
        self._session.commit()
        self._session.refresh(reading)
        return reading

    def find(self, device_id: str, read_at: datetime) -> SensorReading | None:
        return self._session.scalar(
            select(SensorReading).where(
                SensorReading.device_id == device_id, SensorReading.read_at == read_at
            )
        )

    def latest(
        self, limit: int, offset: int, device_id: str | None
    ) -> tuple[list[SensorReading], int]:
        base = select(SensorReading)
        if device_id is not None:
            base = base.where(SensorReading.device_id == device_id)
        total = self._session.scalar(select(func.count()).select_from(base.subquery())) or 0
        rows = self._session.scalars(
            base.order_by(SensorReading.read_at.desc(), SensorReading.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        return list(rows), total

    def devices(self) -> list[DeviceSummary]:
        resumen = (
            select(
                SensorReading.device_id.label("device_id"),
                func.count().label("readings"),
                func.min(SensorReading.read_at).label("first_read_at"),
                func.max(SensorReading.read_at).label("last_read_at"),
            )
            .group_by(SensorReading.device_id)
            .subquery()
        )
        filas = self._session.execute(
            select(
                resumen.c.device_id,
                resumen.c.readings,
                resumen.c.first_read_at,
                resumen.c.last_read_at,
                SensorReading.mm,
            )
            .join(
                SensorReading,
                (SensorReading.device_id == resumen.c.device_id)
                & (SensorReading.read_at == resumen.c.last_read_at),
            )
            .order_by(resumen.c.device_id)
        ).all()
        return [
            DeviceSummary(f.device_id, f.readings, f.first_read_at, f.last_read_at, f.mm)
            for f in filas
        ]
