"""Salud de la red: qué estaciones siguen reportando y cuáles dejaron de hacerlo.

Un silencio no es 0 mm: una estación que dejó de reportar no tiene lluvia «cero», tiene
«sin dato». El cálculo se hace contra la fecha de corte de los datos (31/10/2026), no contra
el día de hoy, para no usar nada posterior al corte.
"""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

# Umbral por defecto, a confirmar con el equipo: una estación sin ninguna lectura con valor en
# los últimos 30 días antes del corte se marca «en silencio». Se puede pedir otro por consulta.
SILENT_AFTER_DAYS = 30
MAX_SILENT_AFTER_DAYS = 365


class NetworkState(StrEnum):
    ACTIVA = "activa"
    EN_SILENCIO = "en_silencio"
    SIN_DATOS = "sin_datos"


@dataclass(frozen=True)
class Health:
    state: NetworkState
    days_since_last: int | None


def classify(last_reading: date | None, cutoff: date, silent_after_days: int) -> Health:
    """`last_reading` es la última fecha con valor medido (estado `dato`); None si no tiene."""
    if last_reading is None:
        return Health(NetworkState.SIN_DATOS, None)
    days = (cutoff - last_reading).days
    state = NetworkState.EN_SILENCIO if days > silent_after_days else NetworkState.ACTIVA
    return Health(state, days)
