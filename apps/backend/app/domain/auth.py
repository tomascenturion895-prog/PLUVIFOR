"""Cuentas de usuario: contraseñas, roles y reglas. Puro: sin base ni red.

Las contraseñas se guardan con scrypt (biblioteca estándar de Python, sin dependencias nuevas),
con una sal distinta por usuario. Nunca se guardan ni se registran en claro. Los tokens de sesión
son aleatorios y en la base solo queda su resumen SHA-256.
"""

import base64
import hashlib
import hmac
import secrets
from enum import StrEnum

MIN_PASSWORD = 10
MAX_PASSWORD = 128
# Parámetros de scrypt (N = 2^14, r = 8, p = 1): ~16 MB y algunas decenas de milisegundos.
_N, _R, _P = 2**14, 8, 1
_MAXMEM = 64 * 1024 * 1024
MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 15


class Role(StrEnum):
    """Quién puede qué. El rol nunca lo elige quien se registra."""

    CIUDADANO = "ciudadano"  # se registra solo; gestiona sus propias suscripciones
    OPERADOR = "operador"  # carga datos, reportes de campo y manda avisos
    ADMINISTRADOR = "administrador"  # además, gestiona las cuentas


STAFF_ROLES = frozenset({Role.OPERADOR, Role.ADMINISTRADOR})


def validate_password(password: str, email: str | None = None) -> None:
    """Lanza ValueError con el motivo en español si la contraseña no sirve."""
    if len(password) < MIN_PASSWORD:
        raise ValueError(f"La contraseña necesita al menos {MIN_PASSWORD} caracteres.")
    if len(password) > MAX_PASSWORD:
        raise ValueError(f"La contraseña no puede pasar de {MAX_PASSWORD} caracteres.")
    if password.strip() != password or password.strip() == "":
        raise ValueError("La contraseña no puede empezar ni terminar con espacios.")
    if email and password.lower() in (email.lower(), email.split("@")[0].lower()):
        raise ValueError("La contraseña no puede ser igual al correo.")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, maxmem=_MAXMEM)
    salt_b64 = base64.b64encode(salt).decode()
    digest_b64 = base64.b64encode(digest).decode()
    return f"scrypt${_N}${_R}${_P}${salt_b64}${digest_b64}"


def verify_password(password: str, stored: str) -> bool:
    """Compara en tiempo constante. Un hash mal formado nunca verifica."""
    try:
        scheme, n, r, p, salt_b64, digest_b64 = stored.split("$")
        if scheme != "scrypt":
            return False
        expected = base64.b64decode(digest_b64)
        actual = hashlib.scrypt(
            password.encode(),
            salt=base64.b64decode(salt_b64),
            n=int(n),
            r=int(r),
            p=int(p),
            maxmem=_MAXMEM,
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


# Hash de una contraseña que nadie conoce: se verifica contra él cuando el correo no existe,
# para que «no existe» y «clave incorrecta» tarden lo mismo.
DUMMY_HASH = hash_password(secrets.token_urlsafe(16))


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def token_digest(token: str) -> str:
    """Resumen del token: en la base nunca queda el token en sí."""
    return hashlib.sha256(token.encode()).hexdigest()
