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
_EMAIL = re.compile(r"^[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,190}\.[A-Za-z]{2,24}$")


class SubscriptionStatus(StrEnum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    BAJA = "baja"


class Channel(StrEnum):
    """Por dónde saldría un mensaje. Hoy todos son simulados: no se envía nada real."""

    WHATSAPP = "whatsapp"
    EMAIL = "email"
    SISTEMA = "sistema"  # notificación dentro de la propia aplicación


class MessageKind(StrEnum):
    CODIGO = "codigo"
    BIENVENIDA = "bienvenida"
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


def normalize_email(raw: str) -> str:
    """Correo en minúsculas y sin espacios. Lanza ValueError si no parece uno."""
    texto = raw.strip().lower()
    if len(texto) > 254 or not _EMAIL.match(texto):
        raise ValueError("El correo no parece válido.")
    return texto


def mask_email(email: str) -> str:
    """«tomas@correo.com» → «t****@correo.com»: se guarda y se muestra solo así."""
    usuario, dominio = email.split("@", 1)
    return f"{usuario[0]}{'*' * min(len(usuario) - 1, 6)}@{dominio}"


def welcome_message() -> str:
    return (
        "PLUVIFOR: listo, quedaste suscripto a los avisos de lluvia. Vas a recibir un mensaje "
        "cuando una estación registre 50 mm o más en un día. Son avisos informativos, no órdenes "
        f"de evacuar. Para no recibir más, respondé BAJA. {LEYENDA}"
    )


def email_registration(station_name: str | None) -> tuple[str, str]:
    """Asunto y cuerpo del correo que recibe quien se registra."""
    zona = f"la estación {station_name}" if station_name else "todas las estaciones"
    return (
        "PLUVIFOR · recibimos tu registro",
        "Hola. Recibimos tu pedido para recibir avisos de lluvia de "
        f"{zona}. Te enviamos un código por WhatsApp: ingresalo en la aplicación para confirmar. "
        "Si no lo pediste, ignorá este correo.\n\n"
        f"{LEYENDA}",
    )


def email_alert(message: str) -> tuple[str, str]:
    return ("PLUVIFOR · aviso de lluvia intensa", message)
