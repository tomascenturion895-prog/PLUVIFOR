from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import FieldReport


class FieldReportRepository(Protocol):
    def add(self, report: FieldReport) -> FieldReport: ...

    def latest(self, limit: int, offset: int) -> tuple[list[FieldReport], int]: ...


class SqlFieldReportRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, report: FieldReport) -> FieldReport:
        self._session.add(report)
        self._session.commit()
        self._session.refresh(report)
        return report

    def latest(self, limit: int, offset: int) -> tuple[list[FieldReport], int]:
        total = self._session.scalar(select(func.count()).select_from(FieldReport)) or 0
        rows = self._session.scalars(
            select(FieldReport)
            .order_by(FieldReport.obs_date.desc(), FieldReport.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        return list(rows), total
