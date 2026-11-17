from datetime import date

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.enums import DataCategory, RainState, Validation
from app.models._types import text_enum

# Milímetros como número (no Decimal) para que SQLite y PostgreSQL se comporten igual.
_MM = Numeric(8, 2, asdecimal=False)


class RainfallRecord(Base):
    """La lluvia: un registro por estación, día y categoría.

    Un hueco nunca es 0 mm: `mm` tiene valor si y solo si el estado es `dato`.
    """

    __tablename__ = "rainfall_records"
    __table_args__ = (
        UniqueConstraint("station_id", "obs_date", "category"),
        CheckConstraint("mm IS NULL OR mm >= 0", name="mm_non_negative"),
        CheckConstraint("mm_chrono IS NULL OR mm_chrono >= 0", name="mm_chrono_non_negative"),
        CheckConstraint("(state = 'dato') = (mm IS NOT NULL)", name="gap_is_not_zero"),
        CheckConstraint("unit = 'mm'", name="unit_is_mm"),
        Index("ix_rainfall_records_obs_date", "obs_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"))
    import_id: Mapped[int | None] = mapped_column(ForeignKey("import_logs.id"))
    obs_date: Mapped[date]
    state: Mapped[RainState] = mapped_column(text_enum(RainState, "rain_state"))
    mm: Mapped[float | None] = mapped_column(_MM)
    # Informativa: nunca rellena un hueco de `mm`.
    mm_chrono: Mapped[float | None] = mapped_column(_MM)
    unit: Mapped[str] = mapped_column(String(8), default="mm")
    category: Mapped[DataCategory] = mapped_column(text_enum(DataCategory, "rain_category"))
    validation: Mapped[Validation] = mapped_column(
        text_enum(Validation, "rain_validation"), default=Validation.SIN_VALIDAR
    )
