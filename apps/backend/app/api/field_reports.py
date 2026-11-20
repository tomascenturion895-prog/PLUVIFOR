from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import Actor, get_field_report_service, require_admin
from app.schemas.field_reports import FieldReportIn, FieldReportList, FieldReportOut
from app.services.field_reports import FieldReportService

router = APIRouter(
    prefix="/api/field-reports", tags=["reportes de campo"], dependencies=[Depends(require_admin)]
)

Service = Annotated[FieldReportService, Depends(get_field_report_service)]


@router.post(
    "",
    response_model=FieldReportOut,
    status_code=201,
    summary="Cargar un reporte de lluvia de campo (policial)",
)
def create_field_report(
    data: FieldReportIn, service: Service, actor: Annotated[Actor, Depends(require_admin)]
) -> FieldReportOut:
    """Entra como observado y sin validar, con su fuente. Sin ubicación queda pendiente."""
    return FieldReportOut.model_validate(service.create(data, actor.user_id))


@router.get("", response_model=FieldReportList, summary="Últimos reportes de campo")
def list_field_reports(
    service: Service,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> FieldReportList:
    items, total = service.latest(limit, offset)
    return FieldReportList(items=[FieldReportOut.model_validate(i) for i in items], total=total)
