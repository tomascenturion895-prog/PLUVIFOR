from datetime import UTC, date, timedelta, timezone

from app.domain.enums import SensorCategory
from app.errors import ApiError
from app.models import SensorReading
from app.repositories.sensor_readings import SensorReadingRepository
from app.schemas.sensor_readings import SensorReadingIn

SOURCE = "sensor_simulado"
# Argentina no tiene horario de verano: un desfase fijo evita depender de la base de zonas horarias.
_ARGENTINA = timezone(timedelta(hours=-3))


class SensorReadingService:
    """Ingesta de lecturas de dispositivos. Todo entra como `simulado`, sin excepción."""

    def __init__(self, repository: SensorReadingRepository, cutoff: date):
        self._repository = repository
        self._cutoff = cutoff

    def ingest(self, data: SensorReadingIn) -> tuple[SensorReading, bool]:
        """Guarda la lectura. Devuelve (lectura, creada). Reenviar la misma no la duplica."""
        read_at = data.read_at.astimezone(UTC)
        if read_at.astimezone(_ARGENTINA).date() > self._cutoff:
            raise ApiError(
                422,
                "date_after_cutoff",
                f"La lectura no puede ser posterior al corte de datos ({self._cutoff:%d/%m/%Y}).",
            )
        existing = self._repository.find(data.device_id, read_at)
        if existing is not None:
            if existing.mm != data.mm:
                raise ApiError(
                    409,
                    "reading_conflict",
                    "Ya hay una lectura de ese dispositivo a esa hora con otro valor.",
                )
            return existing, False
        created = self._repository.add(
            SensorReading(
                device_id=data.device_id,
                read_at=read_at,
                mm=data.mm,
                lat=data.lat,
                lon=data.lon,
                category=SensorCategory.SIMULADO,
                source=SOURCE,
            )
        )
        return created, True

    def latest(
        self, limit: int, offset: int, device_id: str | None
    ) -> tuple[list[SensorReading], int]:
        return self._repository.latest(limit, offset, device_id)
