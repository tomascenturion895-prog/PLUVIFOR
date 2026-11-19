from app.errors import ApiError
from app.models import Station
from app.repositories.stations import Page, StationFilters, StationRepository


class StationService:
    """Consulta del catálogo. Depende del contrato del repositorio, no de SQLAlchemy."""

    def __init__(self, repository: StationRepository):
        self._repository = repository

    def search(self, filters: StationFilters, page: Page) -> tuple[list[Station], int]:
        return self._repository.search(filters, page)

    def get(self, station_id: int) -> Station:
        station = self._repository.get(station_id)
        if station is None:
            raise ApiError(404, "station_not_found", "No existe la estación pedida.")
        return station
