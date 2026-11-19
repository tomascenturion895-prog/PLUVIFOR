from app.domain.enums import Severity
from app.domain.quality import (
    ZERO_STREAK_CODE,
    ZERO_STREAK_MIN_DAYS,
    ZERO_STREAK_RULE_VERSION,
    find_zero_streaks,
)
from app.repositories.quality import QualityRepository


class QualityService:
    """Recalcula las banderas de calidad a partir de los registros observados."""

    def __init__(self, repository: QualityRepository):
        self._repository = repository

    def recompute_zero_streaks(self) -> dict[int, int]:
        """Devuelve cuántos tramos quedaron marcados por estación."""
        result: dict[int, int] = {}
        try:
            for station_id in self._repository.station_ids():
                streaks = find_zero_streaks(self._repository.observed_days(station_id))
                self._repository.replace_flags(
                    station_id,
                    ZERO_STREAK_CODE,
                    ZERO_STREAK_RULE_VERSION,
                    streaks,
                    Severity.AVISO,
                    {"min_days": ZERO_STREAK_MIN_DAYS},
                )
                result[station_id] = len(streaks)
            self._repository.commit()
        except Exception:
            self._repository.rollback()
            raise
        return result
