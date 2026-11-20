from datetime import date

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.enums import Severity
from app.models._types import text_enum


class QualityFlag(Base):
    """Advertencia que abarca un tramo de fechas. Se recalcula; no es dato de la fuente."""

    __tablename__ = "quality_flags"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="range_ordered"),
        # Cada serie y cada estimación buscan las advertencias de una estación en un tramo.
        Index("ix_quality_flags_station_id_range", "station_id", "start_date", "end_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"))
    code: Mapped[str] = mapped_column(String(64))
    start_date: Mapped[date]
    end_date: Mapped[date]
    severity: Mapped[Severity] = mapped_column(text_enum(Severity, "flag_severity"))
    detail: Mapped[str | None] = mapped_column(Text)  # JSON que explica la advertencia
    rule_version: Mapped[str] = mapped_column(String(32))
