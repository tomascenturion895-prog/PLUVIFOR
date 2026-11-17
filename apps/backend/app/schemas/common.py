"""Esquemas compartidos por toda la API."""

from datetime import date
from typing import Any

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[dict[str, Any]] | None = None


class ErrorResponse(BaseModel):
    """Formato único de error de la API."""

    error: ErrorBody


class HealthResponse(BaseModel):
    status: str
    version: str
    env: str
    data_cutoff_date: date
