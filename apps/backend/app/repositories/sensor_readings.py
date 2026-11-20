from datetime import datetime
from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import SensorReading


class SensorReadingRepository(Protocol):
    def add(self, reading: SensorReading) -> SensorReading: ...

    def find(self, device_id: str, read_at: datetime) -> SensorReading | None: ...

    def latest(
        self, limit: int, offset: int, device_id: str | None
    ) -> tuple[list[SensorReading], int]: ...


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
