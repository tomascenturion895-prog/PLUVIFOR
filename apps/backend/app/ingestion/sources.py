"""Definición de las fuentes que se saben importar. Agregar una fuente es agregar una entrada."""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

from app.domain.enums import DataCategory
from app.ingestion.types import RawRainRow, Rejection, StationRow


@dataclass(frozen=True)
class SourceDefinition:
    code: str
    name: str
    network: str
    category: DataCategory
    url: str | None = None
    # Pendiente de confirmar (la red mezcla estaciones convencionales y automáticas).
    day_cutoff_local: str | None = None


class SourceConnector(Protocol):
    """Lo que hace falta para sumar una fuente: se declara y sabe leer sus archivos.

    El resto de la importación (validación, auditoría, guardado) no cambia por fuente.
    """

    definition: SourceDefinition

    def read_stations(self, text: str) -> tuple[list[StationRow], list[Rejection]]: ...

    def read_rainfall(self, text: str) -> Iterator[RawRainRow]: ...


SIGA_INTA = SourceDefinition(
    code="siga_inta",
    name="SIGA · Sistema de Información y Gestión Agrometeorológica (INTA)",
    network="INTA",
    category=DataCategory.OBSERVADO,
    url="https://siga.inta.gob.ar",
)
