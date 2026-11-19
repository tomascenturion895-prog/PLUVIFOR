from datetime import date

from pydantic import BaseModel

from app.domain.enums import DataCategory
from app.domain.network_health import NetworkState


class StationHealthOut(BaseModel):
    station_id: int
    code: str
    name: str
    zone: str | None
    department: str | None
    source: str
    network: str
    state: NetworkState
    last_reading_date: date | None
    # Milímetros de esa última lectura (puede ser un 0 real). Nunca se rellena un silencio.
    last_reading_mm: float | None
    days_since_last: int | None


class NetworkHealthOut(BaseModel):
    category: DataCategory
    data_cutoff_date: date
    silent_after_days: int
    active: int
    silent: int
    no_data: int
    stations: list[StationHealthOut]
