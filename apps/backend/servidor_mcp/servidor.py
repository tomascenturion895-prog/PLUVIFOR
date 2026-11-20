"""Protocolo MCP (JSON-RPC 2.0 por stdio) con la biblioteca estándar.

Solo implementa lo que usa un servidor de herramientas: initialize, ping, tools/list y tools/call.
"""

import json
from collections.abc import Iterable
from typing import IO, Any

from servidor_mcp import LEYENDA, VERSION
from servidor_mcp.api import ErrorConsulta, LectorApi
from servidor_mcp.herramientas import HERRAMIENTAS, POR_NOMBRE, ArgumentoInvalido, llamar

PROTOCOLOS = ("2025-06-18", "2025-03-26", "2024-11-05")

PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND, INVALID_PARAMS = -32700, -32600, -32601, -32602

INSTRUCCIONES = (
    f"{LEYENDA}. Servidor de SOLO LECTURA sobre la API de lluvia de Formosa: no hay ninguna "
    "herramienta que escriba. Un día o acumulado «sin dato» no es 0 mm. Observado, referencia y "
    "estimado nunca se suman. Los datos llegan hasta el 31/10/2026. Si una comparación trae "
    "advertencias, mencionalas al responder."
)


def _error(id_: Any, codigo: int, mensaje: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "error": {"code": codigo, "message": mensaje}}


def _resultado(id_: Any, resultado: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id_, "result": resultado}


def _contenido(texto: str, *, error: bool = False) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": texto}], "isError": error}


class ServidorMcp:
    def __init__(self, lector: LectorApi):
        self._lector = lector

    def procesar(self, mensaje: Any) -> dict[str, Any] | None:
        """Devuelve la respuesta, o None si el mensaje era una notificación."""
        if not isinstance(mensaje, dict) or mensaje.get("jsonrpc") != "2.0":
            return _error(None, INVALID_REQUEST, "El mensaje no es una petición JSON-RPC 2.0.")
        metodo, id_ = mensaje.get("method"), mensaje.get("id")
        if not isinstance(metodo, str):
            return _error(id_, INVALID_REQUEST, "Falta el método.")
        if "id" not in mensaje:
            return None  # notificación (por ejemplo notifications/initialized): no se responde
        params = mensaje.get("params") or {}
        if not isinstance(params, dict):
            return _error(id_, INVALID_PARAMS, "Los parámetros tienen que ser un objeto.")

        if metodo == "initialize":
            pedido = params.get("protocolVersion")
            return _resultado(
                id_,
                {
                    "protocolVersion": pedido if pedido in PROTOCOLOS else PROTOCOLOS[0],
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {
                        "name": "pluvifor-lluvia",
                        "title": "PLUVIFOR · lluvia (solo lectura)",
                        "version": VERSION,
                    },
                    "instructions": INSTRUCCIONES,
                },
            )
        if metodo == "ping":
            return _resultado(id_, {})
        if metodo == "tools/list":
            return _resultado(id_, {"tools": [h.definicion() for h in HERRAMIENTAS]})
        if metodo == "tools/call":
            return self._llamar(id_, params)
        return _error(id_, METHOD_NOT_FOUND, f"Método no disponible: {metodo}.")

    def _llamar(self, id_: Any, params: dict[str, Any]) -> dict[str, Any]:
        nombre, args = params.get("name"), params.get("arguments") or {}
        if not isinstance(nombre, str) or nombre not in POR_NOMBRE:
            return _error(id_, INVALID_PARAMS, f"Herramienta desconocida: {nombre}.")
        if not isinstance(args, dict):
            return _resultado(
                id_, _contenido("Los argumentos tienen que ser un objeto.", error=True)
            )
        try:
            return _resultado(id_, _contenido(llamar(nombre, args, self._lector)))
        except (ArgumentoInvalido, ErrorConsulta) as e:
            return _resultado(id_, _contenido(str(e), error=True))
        except Exception:  # noqa: BLE001 - nunca se filtran detalles internos al cliente
            return _resultado(id_, _contenido("Ocurrió un error inesperado.", error=True))


def servir(entrada: Iterable[str], salida: IO[str], servidor: ServidorMcp) -> None:
    """Un mensaje JSON por línea. Termina cuando se cierra la entrada."""
    for linea in entrada:
        if not linea.strip():
            continue
        try:
            mensaje = json.loads(linea)
        except ValueError:
            respuesta: dict[str, Any] | None = _error(None, PARSE_ERROR, "JSON inválido.")
        else:
            respuesta = servidor.procesar(mensaje)
        if respuesta is not None:
            salida.write(json.dumps(respuesta) + "\n")  # ASCII puro: sirve con cualquier consola
            salida.flush()
