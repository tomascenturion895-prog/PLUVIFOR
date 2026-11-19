"""Importación con auditoría. El archivo viaja como cuerpo del pedido (text/csv), sin multipart."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Request
from starlette.concurrency import run_in_threadpool

from app.api.deps import get_import_service, require_admin
from app.config import Settings, get_settings
from app.domain.enums import ImportMode
from app.errors import ApiError
from app.ingestion.types import ImportReport, InvalidFileError, UploadTooLargeError
from app.schemas.imports import ImportLogOut, ImportReportOut
from app.services.importer import ImportService

router = APIRouter(
    prefix="/api/import", tags=["importación"], dependencies=[Depends(require_admin)]
)

Source = Annotated[str, Query(min_length=1, max_length=50, pattern=r"^[a-z0-9_]+$")]
Filename = Annotated[str, Query(min_length=1, max_length=255)]
Kind = Literal["stations", "rainfall"]


async def _read_body(request: Request, max_bytes: int) -> bytes:
    """Lee el cuerpo cortando apenas supera el máximo (no se carga un archivo enorme)."""
    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > max_bytes:
        raise _too_large(max_bytes)
    chunks: list[bytes] = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > max_bytes:
            raise _too_large(max_bytes)
        chunks.append(chunk)
    return b"".join(chunks)


def _too_large(max_bytes: int) -> ApiError:
    return ApiError(
        413, "payload_too_large", f"El archivo supera el máximo de {max_bytes // (1024 * 1024)} MB."
    )


async def _run(
    request: Request,
    service: ImportService,
    settings: Settings,
    mode: ImportMode,
    kind: Kind,
    source: str,
    filename: str,
) -> ImportReportOut:
    content = await _read_body(request, settings.max_upload_bytes)

    def work() -> ImportReport:
        if kind == "stations":
            return service.import_stations(source, filename, content, mode)
        return service.import_rainfall(
            source, filename, content, mode, record_audit=mode is ImportMode.COMMIT
        )

    try:
        report = await run_in_threadpool(work)
    except UploadTooLargeError as exc:
        raise ApiError(413, "payload_too_large", str(exc)) from exc
    except InvalidFileError as exc:
        raise ApiError(422, "invalid_file", str(exc)) from exc
    return ImportReportOut.from_report(report)


@router.post(
    "/audit",
    response_model=ImportReportOut,
    summary="Valida un archivo y devuelve el informe sin guardar nada",
)
async def audit(
    request: Request,
    service: Annotated[ImportService, Depends(get_import_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    source: Source = "siga_inta",
    kind: Kind = "rainfall",
    filename: Filename = "archivo.csv",
) -> ImportReportOut:
    return await _run(request, service, settings, ImportMode.AUDIT, kind, source, filename)


@router.post(
    "/commit",
    response_model=ImportReportOut,
    summary="Guarda lo aceptado y registra la carga en import_logs",
)
async def commit(
    request: Request,
    service: Annotated[ImportService, Depends(get_import_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    source: Source = "siga_inta",
    kind: Kind = "rainfall",
    filename: Filename = "archivo.csv",
) -> ImportReportOut:
    return await _run(request, service, settings, ImportMode.COMMIT, kind, source, filename)


@router.get(
    "/logs",
    response_model=list[ImportLogOut],
    summary="Historial de cargas registradas (la más nueva primero)",
)
def logs(
    service: Annotated[ImportService, Depends(get_import_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[ImportLogOut]:
    return [ImportLogOut.from_entry(entry) for entry in service.recent_imports(limit)]
