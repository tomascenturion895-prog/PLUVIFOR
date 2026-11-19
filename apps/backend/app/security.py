"""Protecciones de la API a nivel de pedido: encabezados de seguridad y límite de tamaño.

Son middlewares ASGI puros (no dependen de FastAPI), cada uno con una sola responsabilidad.
"""

from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]

# La API solo devuelve JSON: no necesita cargar nada, ni que la incrusten en otra página.
SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
    "Cross-Origin-Resource-Policy": "same-site",
}
API_CSP = "default-src 'none'; frame-ancestors 'none'"
HSTS = "max-age=31536000; includeSubDomains"
DOCS_PATHS = ("/docs", "/openapi.json")  # la documentación interactiva necesita sus scripts


class SecurityHeadersMiddleware:
    def __init__(self, app: Callable, *, hsts: bool = False):
        self._app = app
        self._hsts = hsts

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        is_docs = scope["path"].startswith(DOCS_PATHS)

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = [(k, v) for k, v in message.get("headers", []) if k.lower() != b"server"]
                present = {k.lower() for k, _ in headers}
                extra = dict(SECURITY_HEADERS)
                if not is_docs:
                    extra["Content-Security-Policy"] = API_CSP
                if self._hsts:
                    extra["Strict-Transport-Security"] = HSTS
                for name, value in extra.items():
                    if name.lower().encode() not in present:
                        headers.append((name.lower().encode(), value.encode()))
                message = {**message, "headers": headers}
            await send(message)

        await self._app(scope, receive, send_with_headers)


class BodySizeLimitMiddleware:
    """Corta los pedidos cuyo cuerpo supera el máximo, sin leerlos enteros.

    `limits` es una lista de (prefijo de ruta, máximo en bytes); gana el prefijo más largo y
    `default` aplica al resto. Así la importación admite archivos y el resto no.
    """

    def __init__(self, app: Callable, *, default: int, limits: tuple[tuple[str, int], ...] = ()):
        self._app = app
        self._default = default
        self._limits = sorted(limits, key=lambda item: len(item[0]), reverse=True)

    def _limit_for(self, path: str) -> int:
        for prefix, limit in self._limits:
            if path.startswith(prefix):
                return limit
        return self._default

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        limit = self._limit_for(scope["path"])
        declared = dict(scope.get("headers", [])).get(b"content-length", b"")
        if declared.isdigit() and int(declared) > limit:
            await self._reject(send, limit)
            return

        received = 0
        exceeded = False
        started = False

        async def counting_receive() -> Message:
            nonlocal received, exceeded
            if exceeded:
                return {"type": "http.disconnect"}
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    # No se lanza una excepción: los frameworks suelen atraparla y convertirla en
                    # otro error. Se corta la lectura y la respuesta la da este middleware.
                    exceeded = True
                    return {"type": "http.disconnect"}
            return message

        async def tracking_send(message: Message) -> None:
            nonlocal started
            if exceeded and not started:
                return  # se descarta lo que conteste la app a un cuerpo cortado
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self._app(scope, counting_receive, tracking_send)
        except Exception:
            if not exceeded:
                raise
        if exceeded and not started:
            await self._reject(send, limit)

    @staticmethod
    async def _reject(send: Send, limit: int) -> None:
        mb = limit / (1024 * 1024)
        size = f"{mb:g} MB" if mb >= 1 else f"{limit // 1024} KB"
        body = (
            '{"error":{"code":"payload_too_large",'
            f'"message":"El pedido supera el máximo de {size}."}}}}'
        ).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})
