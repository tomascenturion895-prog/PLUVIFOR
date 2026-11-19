"""Registro de conectores: agregar una fuente es agregar su conector acá."""

from collections.abc import Iterable

from app.ingestion.siga import SigaCsvConnector
from app.ingestion.sources import SourceConnector


def build_registry(connectors: Iterable[SourceConnector]) -> dict[str, SourceConnector]:
    registry: dict[str, SourceConnector] = {}
    for connector in connectors:
        code = connector.definition.code
        if code in registry:
            raise ValueError(f"Fuente repetida: {code}")
        registry[code] = connector
    return registry


DEFAULT_CONNECTORS: dict[str, SourceConnector] = build_registry([SigaCsvConnector()])
