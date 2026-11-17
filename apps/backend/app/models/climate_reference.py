from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.enums import DataCategory
from app.models._types import text_enum


class ClimateReference(Base):
    """Normal climática mensual. Siempre `referencia`; solo se carga con fuente verificada."""

    __tablename__ = "climate_references"
    __table_args__ = (
        UniqueConstraint("station_id", "month", "period"),
        CheckConstraint("month BETWEEN 1 AND 12", name="month_range"),
        CheckConstraint("normal_mm >= 0", name="normal_non_negative"),
        CheckConstraint("category = 'referencia'", name="always_reference"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"))
    month: Mapped[int]
    normal_mm: Mapped[float] = mapped_column(Numeric(8, 2, asdecimal=False))
    period: Mapped[str] = mapped_column(String(32))
    source_note: Mapped[str] = mapped_column(String(500))
    category: Mapped[DataCategory] = mapped_column(
        text_enum(DataCategory, "climate_category"), default=DataCategory.REFERENCIA
    )
