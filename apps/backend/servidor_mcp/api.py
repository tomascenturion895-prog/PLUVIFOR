"""Lector de la API de PLUVIFOR. Solo sabe hacer GET: eso lo vuelve de solo lectura."""

import json
import urllib.error
import urllib.request
from collections.abc import Mapping
from typing import Any, Protocol
from urllib.parse import urlencode, urlparse

TIMEOUT_SEGUNDOS = 15
MAX_RESPUESTA_BYTES = 5 * 1024 * 1024


class ErrorConsulta(Exception):
    """La API no pudo responder la consulta. El mensaje está en español y es apto para mostrar."""


class LectorApi(Protocol):
    def get(self, ruta: str, parametros: Mapping[str, Any]) -> Any: ...


def validar_base(base: str) -> str:
    partes = urlparse(base)
    if partes.scheme not in ("http", "https") or not partes.netloc:
        raise ValueError("La dirección de la API tiene que ser http:// o https://.")
    return base.rstrip("/")


class LectorHttp:
    """Implementación real. No expone ningún método que no sea `get`."""

    def __init__(self, base: str):
        self._base = validar_base(base)

    def get(self, ruta: str, parametros: Mapping[str, Any]) -> Any:
        pares = [(k, v) for k, v in parametros.items() if v is not None]
        url = f"{self._base}{ruta}" + (f"?{urlencode(pares, doseq=True)}" if pares else "")
        pedido = urllib.request.Request(  # noqa: S310 - el esquema se validó en validar_base
            url, headers={"Accept": "application/json"}, method="GET"
        )
        try:
            with urllib.request.urlopen(pedido, timeout=TIMEOUT_SEGUNDOS) as r:  # noqa: S310
                cuerpo = r.read(MAX_RESPUESTA_BYTES + 1)
        except urllib.error.HTTPError as e:
            raise ErrorConsulta(self._mensaje_de_error(e)) from None
        except (urllib.error.URLError, TimeoutError):
            raise ErrorConsulta(
                f"No se pudo conectar con la API en {self._base}. ¿Está levantada?"
            ) from None
        if len(cuerpo) > MAX_RESPUESTA_BYTES:
            raise ErrorConsulta("La respuesta de la API es demasiado grande: acotá el período.")
        try:
            return json.loads(cuerpo)
        except ValueError:
            raise ErrorConsulta("La API respondió algo que no es JSON.") from None

    @staticmethod
    def _mensaje_de_error(error: urllib.error.HTTPError) -> str:
        if error.code >= 500:
            return f"La API tuvo un problema interno (código {error.code}). Probá más tarde."
        try:
            mensaje = json.loads(error.read(65536)).get("error", {}).get("message")
        except (ValueError, AttributeError):
            mensaje = None
        return mensaje or f"La API rechazó la consulta (código {error.code})."
