from datetime import date, datetime

from sqlalchemy import CheckConstraint, DateTime, Float, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.enums import DataCategory, LocationSource, ReportLocation, Validation
from app.models._types import text_enum


class FieldReport(Base):
    """Lluvia anotada a mano por la policía donde no hay estación (un reporte por día y lugar).

    No es una lectura de estación: va en su propia tabla y nunca se suma a las series.
    Entra siempre como `observado` y `sin_validar`, con su fuente y su ubicación (o pendiente).
    """

    __tablename__ = "field_reports"
    __table_args__ = (
        CheckConstraint("mm >= 0", name="mm_non_negative"),
        CheckConstraint(
            "(lat IS NULL) = (lon IS NULL)",
            name="location_complete",
        ),
        CheckConstraint("lat IS NULL OR (lat BETWEEN -90 AND 90)", name="lat_range"),
        CheckConstraint("lon IS NULL OR (lon BETWEEN -180 AND 180)", name="lon_range"),
        CheckConstraint(
            "(location_status = 'informada') = (lat IS NOT NULL)", name="location_status_matches"
        ),
        Index("ix_field_reports_obs_date", "obs_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    obs_date: Mapped[date]
    mm: Mapped[float] = mapped_column(Numeric(8, 2, asdecimal=False))
    place: Mapped[str] = mapped_column(String(200))
    reporter: Mapped[str] = mapped_column(String(120))
    lat: Mapped[float | None] = mapped_column(Float)
    lon: Mapped[float | None] = mapped_column(Float)
    location_status: Mapped[ReportLocation] = mapped_column(
        text_enum(ReportLocation, "field_report_location")
    )
    location_source: Mapped[LocationSource | None] = mapped_column(
        text_enum(LocationSource, "field_report_location_source")
    )
    category: Mapped[DataCategory] = mapped_column(
        text_enum(DataCategory, "field_report_category"), default=DataCategory.OBSERVADO
    )
    validation: Mapped[Validation] = mapped_column(
        text_enum(Validation, "field_report_validation"), default=Validation.SIN_VALIDAR
    )
    source: Mapped[str] = mapped_column(String(64), default="reporte_policial")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
