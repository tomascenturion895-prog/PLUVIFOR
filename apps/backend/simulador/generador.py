"""Generación de lecturas simuladas: determinista (misma semilla, mismas lecturas)."""

import random
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta, timezone
from typing import Any

# Argentina no tiene horario de verano.
ARGENTINA = timezone(timedelta(hours=-3))
HORA_LECTURA = 7  # la red provincial corta a las 07:00
PROB_DIA_SECO = 0.6
PROB_DIA_SIN_LECTURA = 0.1  # el dispositivo no reportó: no se envía nada (nunca un 0 ni un vacío)
MAX_DISPOSITIVOS = 50
MAX_DIAS = 366


def nombre_dispositivo(numero: int) -> str:
    return f"SIM-{numero:03d}"


def generar_lecturas(
    *, dispositivos: int, dias: int, hasta: date, semilla: int
) -> Iterator[dict[str, Any]]:
    """Una lectura diaria por dispositivo, a las 07:00 hora de Argentina, hasta `hasta` inclusive.

    No informa ubicación (no se inventan coordenadas). Algunos días el dispositivo no reporta:
    esos días simplemente no hay lectura.
    """
    if not 1 <= dispositivos <= MAX_DISPOSITIVOS:
        raise ValueError(f"La cantidad de dispositivos va de 1 a {MAX_DISPOSITIVOS}.")
    if not 1 <= dias <= MAX_DIAS:
        raise ValueError(f"La cantidad de días va de 1 a {MAX_DIAS}.")
    azar = random.Random(semilla)  # noqa: S311 - datos simulados, no es criptografía
    desde = hasta - timedelta(days=dias - 1)
    for numero in range(1, dispositivos + 1):
        for offset in range(dias):
            dia = desde + timedelta(days=offset)
            if azar.random() < PROB_DIA_SIN_LECTURA:
                continue
            seco = azar.random() < PROB_DIA_SECO
            mm = 0.0 if seco else round(azar.expovariate(1 / 12), 1)
            hora = datetime(dia.year, dia.month, dia.day, HORA_LECTURA, tzinfo=ARGENTINA)
            yield {
                "device_id": nombre_dispositivo(numero),
                "read_at": hora.astimezone(UTC).isoformat().replace("+00:00", "Z"),
                "mm": min(mm, 400.0),
            }
