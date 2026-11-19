"""Definición de las fuentes que se saben importar. Agregar una fuente es agregar una entrada."""

from dataclasses import dataclass

from app.domain.enums import DataCategory


@dataclass(frozen=True)
class SourceDefinition:
    code: str
    name: str
    network: str
    category: DataCategory
    url: str | None = None
    # Pendiente de confirmar (la red mezcla estaciones convencionales y automáticas).
    day_cutoff_local: str | None = None


SIGA_INTA = SourceDefinition(
    code="siga_inta",
    name="SIGA · Sistema de Información y Gestión Agrometeorológica (INTA)",
    network="INTA",
    category=DataCategory.OBSERVADO,
    url="https://siga.inta.gob.ar",
)

KNOWN_SOURCES = {source.code: source for source in (SIGA_INTA,)}
