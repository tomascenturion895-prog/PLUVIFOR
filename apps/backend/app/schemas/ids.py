"""Identificadores de estación acotados.

Sin tope, un id como 99999999999999999999 rompe el driver de la base (OverflowError en SQLite,
«integer out of range» en PostgreSQL) y termina en un 500 en lugar de un 404 o un 422.
"""

from typing import Annotated

from fastapi import Path, Query
from pydantic import Field

MAX_ID = 2_147_483_647  # mayor entero de 32 bits: cabe en cualquier columna INTEGER

StationIdQuery = Annotated[int, Query(ge=1, le=MAX_ID)]
StationIdPath = Annotated[int, Path(ge=1, le=MAX_ID)]
StationIdItem = Annotated[int, Field(ge=1, le=MAX_ID)]
