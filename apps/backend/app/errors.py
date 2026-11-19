"""Formato único de errores: {"error": {"code", "message", "details"}}.

Nunca se devuelve el detalle interno de una excepción ni el valor que mandó el usuario.
"""

import logging
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.security import API_CSP, SECURITY_HEADERS

logger = logging.getLogger("pluvifor")

_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    413: "payload_too_large",
    429: "too_many_requests",
}


class ApiError(Exception):
    """Error de negocio controlado: se responde con el código y mensaje indicados."""

    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def error_response(
    status_code: int, code: str, message: str, details: list[dict] | None = None
) -> JSONResponse:
    body: dict = {"code": code, "message": message}
    if details:
        body["details"] = details
    return JSONResponse(status_code=status_code, content={"error": body})


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _CODES.get(exc.status_code, "http_error")
        try:
            message = HTTPStatus(exc.status_code).phrase
        except ValueError:
            message = "Error"
        return error_response(exc.status_code, code, message)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Solo se informa dónde y qué falló; nunca el valor recibido.
        details = [
            {"field": ".".join(str(part) for part in err["loc"]), "message": err["msg"]}
            for err in exc.errors()
        ]
        return error_response(
            422, "validation_error", "Los datos enviados no son válidos.", details
        )

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Error no controlado", exc_info=exc)
        response = error_response(500, "internal_error", "Ocurrió un error interno.")
        # Este handler corre fuera de los middlewares: los encabezados se ponen acá.
        response.headers.update({**SECURITY_HEADERS, "Content-Security-Policy": API_CSP})
        return response
