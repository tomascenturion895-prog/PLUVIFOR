from datetime import date

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.enums import CoordsStatus
from app.models._types import text_enum


class Station(Base):
    """Dónde se mide. Las coordenadas admiten vacío: nunca se inventan."""

    __tablename__ = "stations"
    __table_args__ = (
        UniqueConstraint("source_id", "code"),
        CheckConstraint("lat IS NULL OR (lat BETWEEN -90 AND 90)", name="lat_range"),
        CheckConstraint("lon IS NULL OR (lon BETWEEN -180 AND 180)", name="lon_range"),
        # Una estación sin coordenadas no puede figurar como «verificada».
        CheckConstraint(
            "coords_status <> 'verificada' OR (lat IS NOT NULL AND lon IS NOT NULL)",
            name="verified_has_coords",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    code: Mapped[str] = mapped_column(String(64))
    internal_code: Mapped[str | None] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(200))
    kind: Mapped[str | None] = mapped_column(String(100))
    locality: Mapped[str | None] = mapped_column(String(200))
    department: Mapped[str | None] = mapped_column(String(100))
    zone: Mapped[str | None] = mapped_column(String(100))
    lat: Mapped[float | None]
    lon: Mapped[float | None]
    elevation_m: Mapped[float | None]
    coords_status: Mapped[CoordsStatus] = mapped_column(
        text_enum(CoordsStatus, "coords_status"), default=CoordsStatus.PENDIENTE
    )
    active_from: Mapped[date | None]
    active_to: Mapped[date | None]
