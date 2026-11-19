from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_report_service
from app.schemas.report import (
    IntenseEventOut,
    NotEvaluatedOut,
    ReportOut,
    ReportRequest,
    StationReportOut,
)
from app.schemas.series import SummaryOut, WarningOut
from app.services.report import ReportService

router = APIRouter(prefix="/api/reports", tags=["parte pluvial"])


@router.post(
    "/summary",
    response_model=ReportOut,
    summary="Parte pluvial de una o más estaciones en un período, con texto listo para copiar",
)
def summary(
    body: ReportRequest, service: Annotated[ReportService, Depends(get_report_service)]
) -> ReportOut:
    report = service.build(body.station_ids, body.date_from, body.date_to, body.category)
    return ReportOut(
        category=report.category,
        date_from=report.date_from,
        date_to=report.date_to,
        data_cutoff_date=report.cutoff,
        clipped_to_cutoff=report.clipped_to_cutoff,
        stations=[
            StationReportOut(
                station_id=s.result.station.id,
                station_name=s.result.station.name,
                source=s.result.station.source,
                category=report.category,
                summary=SummaryOut.model_validate(s.result.summary),
                intense_events=[
                    IntenseEventOut(obs_date=e.obs_date, mm=e.mm, level_mm=e.level_mm)
                    for e in s.events
                ],
                warnings=[WarningOut.model_validate(w) for w in s.warnings],
            )
            for s in report.stations
        ],
        comparability_warnings=[WarningOut.model_validate(w) for w in report.comparability],
        not_evaluated=[NotEvaluatedOut(code=n.code, reason=n.reason) for n in report.not_evaluated],
        text=report.text,
    )
