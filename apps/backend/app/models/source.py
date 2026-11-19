from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.enums import DataCategory
from app.models._types import text_enum


class Source(Base):
    """De dónde viene cada dato."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    network: Mapped[str] = mapped_column(String(100))
    category: Mapped[DataCategory] = mapped_column(text_enum(DataCategory, "source_category"))
    # Hora de corte del «día de lluvia» (07:00 o 09:00): alimenta la advertencia de horario.
    day_cutoff_local: Mapped[str | None] = mapped_column(String(5))
    url: Mapped[str | None] = mapped_column(String(500))
    license: Mapped[str | None] = mapped_column(String(200))
