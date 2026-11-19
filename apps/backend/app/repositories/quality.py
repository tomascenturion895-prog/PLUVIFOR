import json
from typing import Protocol

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain.enums import DataCategory, Severity
from app.domain.quality import DayValue, Streak
from app.models import QualityFlag, RainfallRecord, Station


class QualityRepository(Protocol):
    def station_ids(self) -> list[int]: ...

    def observed_days(self, station_id: int) -> list[DayValue]: ...

    def replace_flags(
        self,
        station_id: int,
        code: str,
        rule_version: str,
        streaks: list[Streak],
        severity: Severity,
        detail: dict,
    ) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class SqlQualityRepository:
    def __init__(self, session: Session):
        self._session = session

    def station_ids(self) -> list[int]:
        return list(self._session.scalars(select(Station.id).order_by(Station.id)))

    def observed_days(self, station_id: int) -> list[DayValue]:
        rows = self._session.execute(
            select(RainfallRecord.obs_date, RainfallRecord.state, RainfallRecord.mm)
            .where(
                RainfallRecord.station_id == station_id,
                RainfallRecord.category == DataCategory.OBSERVADO,
            )
            .order_by(RainfallRecord.obs_date)
        )
        return [DayValue(obs_date, state, mm) for obs_date, state, mm in rows]

    def replace_flags(
        self,
        station_id: int,
        code: str,
        rule_version: str,
        streaks: list[Streak],
        severity: Severity,
        detail: dict,
    ) -> None:
        # Las banderas se recalculan: se reemplazan las de esa regla, no se acumulan.
        self._session.execute(
            delete(QualityFlag).where(
                QualityFlag.station_id == station_id, QualityFlag.code == code
            )
        )
        for streak in streaks:
            self._session.add(
                QualityFlag(
                    station_id=station_id,
                    code=code,
                    start_date=streak.start,
                    end_date=streak.end,
                    severity=severity,
                    detail=json.dumps({**detail, "days": streak.days}, ensure_ascii=False),
                    rule_version=rule_version,
                )
            )
        self._session.flush()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
