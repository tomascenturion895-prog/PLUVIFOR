from datetime import date

from app.domain.enums import DataCategory
from app.domain.network_health import NetworkState, classify
from app.repositories.network_health import NetworkHealthRepository
from app.schemas.network_health import NetworkHealthOut, StationHealthOut


class NetworkHealthService:
    def __init__(self, repository: NetworkHealthRepository, cutoff: date):
        self._repository = repository
        self._cutoff = cutoff

    def report(self, silent_after_days: int) -> NetworkHealthOut:
        items: list[StationHealthOut] = []
        for reading in self._repository.last_readings(self._cutoff):
            health = classify(reading.obs_date, self._cutoff, silent_after_days)
            station = reading.station
            items.append(
                StationHealthOut(
                    station_id=station.id,
                    code=station.code,
                    name=station.name,
                    zone=station.zone,
                    department=station.department,
                    source=station.source.code,
                    network=station.source.network,
                    state=health.state,
                    last_reading_date=reading.obs_date,
                    last_reading_mm=reading.mm,
                    days_since_last=health.days_since_last,
                )
            )
        count = lambda s: sum(1 for i in items if i.state is s)  # noqa: E731
        return NetworkHealthOut(
            category=DataCategory.OBSERVADO,
            data_cutoff_date=self._cutoff,
            silent_after_days=silent_after_days,
            active=count(NetworkState.ACTIVA),
            silent=count(NetworkState.EN_SILENCIO),
            no_data=count(NetworkState.SIN_DATOS),
            stations=items,
        )
