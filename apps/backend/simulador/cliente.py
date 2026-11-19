"""Envío de lecturas a la API de ingesta (solo biblioteca estándar)."""

import json
import urllib.error
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

RUTA = "/api/sensor-readings"
ENCABEZADO_CLAVE = "X-Device-Key"
TIMEOUT_SEGUNDOS = 10

# (url, clave, cuerpo) -> (código HTTP, mensaje de error si falló)
Enviar = Callable[[str, str, dict[str, Any]], tuple[int, str]]


@dataclass
class Resultado:
    creadas: int = 0
    repetidas: int = 0
    rechazadas: int = 0
    errores: list[str] = field(default_factory=list)
    detenido: bool = False


def validar_url(base: str) -> str:
    partes = urlparse(base)
    if partes.scheme not in ("http", "https") or not partes.netloc:
        raise ValueError("La dirección de la API tiene que ser http:// o https://.")
    return base.rstrip("/") + RUTA


def enviar_http(url: str, clave: str, cuerpo: dict[str, Any]) -> tuple[int, str]:
    pedido = urllib.request.Request(  # noqa: S310 - el esquema se validó en validar_url
        url,
        data=json.dumps(cuerpo).encode(),
        headers={"Content-Type": "application/json", ENCABEZADO_CLAVE: clave},
        method="POST",
    )
    try:
        with urllib.request.urlopen(pedido, timeout=TIMEOUT_SEGUNDOS) as r:  # noqa: S310
            return r.status, ""
    except urllib.error.HTTPError as e:
        try:
            mensaje = json.loads(e.read()).get("error", {}).get("message", "")
        except (ValueError, AttributeError):
            mensaje = ""
        return e.code, mensaje or e.reason
    except (urllib.error.URLError, TimeoutError) as e:
        return 0, f"No se pudo conectar con la API: {e}"


def enviar_lecturas(
    lecturas: Iterable[dict[str, Any]], url: str, clave: str, enviar: Enviar = enviar_http
) -> Resultado:
    """Envía una por una. Se detiene si la clave no sirve o la API no responde."""
    resultado = Resultado()
    for lectura in lecturas:
        codigo, mensaje = enviar(url, clave, lectura)
        if codigo == 201:
            resultado.creadas += 1
        elif codigo == 200:
            resultado.repetidas += 1
        elif codigo in (0, 401, 403):
            resultado.errores.append(mensaje or f"La API respondió {codigo}.")
            resultado.detenido = True
            break
        else:
            resultado.rechazadas += 1
            if len(resultado.errores) < 5:
                resultado.errores.append(f"{lectura['device_id']}: {mensaje or codigo}")
    return resultado
