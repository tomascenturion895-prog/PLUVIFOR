"""Estimación de un día sin dato (SCRUM-93). Funciones puras: sin base de datos ni red.

Método propuesto, NO validado como pronóstico ni como reemplazo de una medición:
- «vecinas_idw_v1»: promedio ponderado por el inverso del cuadrado de la distancia de las
  estaciones vecinas (a MAX_KM o menos) que SÍ midieron ese día.
- «chirps_v3_punto»: el valor CHIRPS ya cargado para esa estación y día (si existe).
Ver docs/datos/estimacion-huecos.md para sus límites.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from math import asin, cos, radians, sin, sqrt
from typing import Any

METODO_VECINAS = "vecinas_idw_v1"
METODO_CHIRPS = "chirps_v3_punto"

# Parámetros del método de vecinas. Son una propuesta de trabajo, no un valor calibrado.
MAX_KM = 25.0
POTENCIA = 2
MIN_VECINAS = 1
DISTANCIA_MINIMA_KM = 0.5  # evita pesos enormes si dos estaciones casi coinciden
RADIO_TIERRA_KM = 6371.0088


@dataclass(frozen=True)
class Vecina:
    station_id: int
    name: str
    distance_km: float
    mm: float


@dataclass(frozen=True)
class Estimacion:
    mm: float
    method: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Contexto:
    """Lo que se sabe de un día sin dato al momento de estimarlo."""

    vecinas: Sequence[Vecina]  # vecinas que midieron ese día, dentro del radio
    chirps_mm: float | None  # valor CHIRPS cargado para la estación ese día, si hay


def mismo_horario(
    kind_a: str | None, corte_a: str | None, kind_b: str | None, corte_b: str | None
) -> bool:
    """Solo se comparan estaciones que cuentan el «día» igual: mismo tipo e igual hora de corte.

    Una convencional (lectura a las 09:00) y una automática pueden etiquetar la lluvia con un día
    de diferencia: en El Colorado, la 51 y la 424 (a 4,5 km) tienen correlación 0,10 el mismo día
    y 0,80 con un día de desfase. Si no se sabe el tipo de alguna, no se asume que son iguales.
    """
    if not kind_a or not kind_b:
        return False
    return kind_a.strip().casefold() == kind_b.strip().casefold() and corte_a == corte_b


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia sobre la esfera (haversine). Alcanza para decidir vecindad a decenas de km."""
    d_lat, d_lon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return 2 * RADIO_TIERRA_KM * asin(sqrt(a))


def promedio_idw(vecinas: Sequence[Vecina]) -> float | None:
    """Promedio ponderado por 1/d². Sin vecinas, no hay estimación (None, nunca 0)."""
    if not vecinas:
        return None
    pesos = [1.0 / max(v.distance_km, DISTANCIA_MINIMA_KM) ** POTENCIA for v in vecinas]
    total = sum(p * v.mm for p, v in zip(pesos, vecinas, strict=True)) / sum(pesos)
    return round(total, 2)


class EstimadorVecinas:
    """Estima con estaciones cercanas que midieron ese día."""

    def __init__(self, max_km: float = MAX_KM, min_vecinas: int = MIN_VECINAS):
        self._max_km = max_km
        self._min_vecinas = min_vecinas

    def estimar(self, contexto: Contexto) -> Estimacion | None:
        usables = [v for v in contexto.vecinas if v.distance_km <= self._max_km]
        if len(usables) < self._min_vecinas:
            return None
        mm = promedio_idw(usables)
        if mm is None:
            return None
        return Estimacion(
            mm=mm,
            method=METODO_VECINAS,
            detail={
                "vecinas": [
                    {
                        "station_id": v.station_id,
                        "name": v.name,
                        "distance_km": round(v.distance_km, 1),
                        "mm": v.mm,
                    }
                    for v in sorted(usables, key=lambda v: v.distance_km)
                ],
                "parametros": {
                    "max_km": self._max_km,
                    "potencia": POTENCIA,
                    "min_vecinas": self._min_vecinas,
                },
            },
        )


class EstimadorChirps:
    """Usa el valor CHIRPS ya cargado para esa estación y día. Sin CHIRPS cargado, no estima."""

    def estimar(self, contexto: Contexto) -> Estimacion | None:
        if contexto.chirps_mm is None:
            return None
        return Estimacion(
            mm=contexto.chirps_mm, method=METODO_CHIRPS, detail={"fuente": "chirps_v3"}
        )
