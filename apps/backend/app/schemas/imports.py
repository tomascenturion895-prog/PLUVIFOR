from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from app.ingestion.types import ImportLogEntry, ImportReport, RejectionReason

MAX_REJECTIONS_LISTED = 200

REASON_MESSAGES: dict[RejectionReason, str] = {
    RejectionReason.FECHA_INVALIDA: "La fecha no es válida (se espera AAAA-MM-DD).",
    RejectionReason.FECHA_POSTERIOR_AL_CORTE: "La fecha es posterior a la fecha de corte.",
    RejectionReason.ESTACION_INEXISTENTE: "La estación no existe en el catálogo.",
    RejectionReason.MM_INVALIDO: "Los milímetros no son un número válido.",
    RejectionReason.MM_NEGATIVO: "Los milímetros no pueden ser negativos.",
    RejectionReason.ESTADO_INVALIDO: "El estado del día no es válido.",
    RejectionReason.ESTADO_INCOHERENTE: "El estado no coincide con el valor: un hueco no lleva mm.",
    RejectionReason.CATEGORIA_INVALIDA: "La categoría debe ser observado, referencia o estimado.",
    RejectionReason.UNIDAD_INVALIDA: "La unidad debe ser mm.",
    RejectionReason.DUPLICADO_EN_ARCHIVO: "El día está repetido dentro del archivo.",
    RejectionReason.COORDENADAS_INVALIDAS: "Las coordenadas son inválidas o están incompletas.",
    RejectionReason.CODIGO_VACIO: "Falta el código o el nombre de la estación.",
    RejectionReason.TEXTO_CON_FORMULA: "El texto empieza con un carácter de fórmula (= + - @).",
}


class RejectionOut(BaseModel):
    line: int
    reason: str
    message: str


class ImportReportOut(BaseModel):
    filename: str
    sha256: str
    mode: Literal["audit", "commit"]
    saved: bool
    rows_read: int
    rows_accepted: int
    rows_rejected: int
    rejections_by_reason: dict[str, int]
    rejections: list[RejectionOut]
    rejections_truncated: bool
    inserted: int
    updated: int

    @classmethod
    def from_report(cls, report: ImportReport) -> "ImportReportOut":
        listed = report.rejections[:MAX_REJECTIONS_LISTED]
        return cls(
            filename=report.filename,
            sha256=report.sha256,
            mode=report.mode,  # type: ignore[arg-type]
            saved=report.mode == "commit",
            rows_read=report.rows_read,
            rows_accepted=report.rows_accepted,
            rows_rejected=report.rows_rejected,
            rejections_by_reason=report.rejections_by_reason(),
            rejections=[
                RejectionOut(line=r.line, reason=r.reason.value, message=REASON_MESSAGES[r.reason])
                for r in listed
            ],
            rejections_truncated=len(report.rejections) > len(listed),
            inserted=report.inserted,
            updated=report.updated,
        )


class ImportLogOut(BaseModel):
    id: int
    source: str
    mode: str
    status: str
    filename: str
    sha256: str
    rows_read: int
    rows_accepted: int
    rows_rejected: int
    rejections_by_reason: dict[str, int]
    cutoff_applied: date
    started_at: datetime

    @classmethod
    def from_entry(cls, entry: ImportLogEntry) -> "ImportLogOut":
        return cls(**entry.__dict__)
