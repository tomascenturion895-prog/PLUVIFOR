"""Avisos a la población: reglas puras, sin base ni red.

Un aviso solo nace de un día **observado con dato** que pasa un umbral. Un hueco no es 0 mm y no
avisa nada; una lectura simulada o una estimación nunca llegan acá. El mensaje no ordena evacuar.
"""

import hashlib
import hmac
import re
import secrets
from datetime import date
from enum import StrEnum

UMBRAL_INTENSO_MM = 50.0
UMBRAL_MUY_INTENSO_MM = 100.0
CODE_TTL_MINUTES = 15
MAX_CODE_ATTEMPTS = 5
LEYENDA = "PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial"

_TELEFONO = re.compile(r"^\+?[0-9][0-9 ()-]{6,24}$")


class SubscriptionStatus(StrEnum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    BAJA = "baja"


class MessageKind(StrEnum):
    CODIGO = "codigo"
    AVISO = "aviso"


def normalize_phone(raw: str) -> str:
    """Deja el teléfono como «+dígitos» (8 a 15 dígitos). Lanza ValueError si no parece uno."""
    texto = raw.strip()
    digitos = re.sub(r"\D", "", texto)
    if not _TELEFONO.match(texto) or not 8 <= len(digitos) <= 15:
        raise ValueError("El teléfono debe tener entre 8 y 15 dígitos (puede llevar + y espacios).")
    return f"+{digitos}"


def digest(value: str, key: str) -> str:
    """Resumen irreversible (HMAC-SHA256): guarda un teléfono o un código sin dejarlo en claro."""
    return hmac.new(key.encode(), value.encode(), hashlib.sha256).hexdigest()


def new_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def level_for(mm: float) -> int | None:
    """100 o 50 si el día pasa ese umbral; None si no llega al primero."""
    if mm >= UMBRAL_MUY_INTENSO_MM:
        return 100
    if mm >= UMBRAL_INTENSO_MM:
        return 50
    return None


def code_message(code: str) -> str:
    return (
        f"PLUVIFOR: tu código para confirmar los avisos de lluvia es {code}. "
        f"Vence en {CODE_TTL_MINUTES} minutos. Si no lo pediste, ignorá este mensaje. {LEYENDA}"
    )


def alert_message(
    station_name: str, station_code: str, day: date, mm: float, level: int, validated: bool
) -> str:
    """Texto informativo del aviso: fuente, categoría y fecha. Nunca ordena evacuar."""
    validacion = "validado" if validated else "sin validar"
    return (
        f"PLUVIFOR · aviso informativo: la estación {station_name} ({station_code}) registró "
        f"{mm:g} mm el {day:%d/%m/%Y} (superó {level} mm; dato observado, {validacion}). "
        "No es una orden ni una recomendación de evacuar: ante dudas, consultá a Defensa Civil. "
        f"Para no recibir más avisos respondé BAJA. {LEYENDA}"
    )
