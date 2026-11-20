from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.enums import DataCategory, RainState
from app.models._types import text_enum


class GapEstimate(Base):
    """Estimación de lluvia para un día SIN DATO de una estación (SCRUM-93).

    Es un valor calculado, nunca medido: va en su propia tabla, siempre con categoría `estimado`
    y con el método y los datos que se usaron. Ninguna consulta de lluvia observada la lee, así
    que no puede sumarse a un acumulado observado. El día original sigue siendo un hueco.
    """

    __tablename__ = "gap_estimates"
    __table_args__ = (
        UniqueConstraint("station_id", "obs_date"),
        CheckConstraint("mm >= 0", name="mm_non_negative"),
        CheckConstraint("category = 'estimado'", name="always_estimated"),
        CheckConstraint("gap_state <> 'dato'", name="fills_a_gap"),
        Index("ix_gap_estimates_obs_date", "obs_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    station_id: Mapped[int] = mapped_column(ForeignKey("stations.id"))
    obs_date: Mapped[date]
    mm: Mapped[float] = mapped_column(Numeric(8, 2, asdecimal=False))
    category: Mapped[DataCategory] = mapped_column(
        text_enum(DataCategory, "gap_estimate_category"), default=DataCategory.ESTIMADO
    )
    # Cómo era el día original: sin_fila o fila_sin_valor (nunca `dato`).
    gap_state: Mapped[RainState] = mapped_column(text_enum(RainState, "gap_estimate_state"))
    method: Mapped[str] = mapped_column(String(64))
    detail: Mapped[str] = mapped_column(Text)  # JSON: vecinas usadas, distancias y parámetros
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
