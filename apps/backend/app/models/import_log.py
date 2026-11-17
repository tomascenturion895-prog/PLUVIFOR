from datetime import date, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.domain.enums import ImportMode, ImportStatus
from app.models._types import text_enum


class ImportLog(Base):
    """Una fila por importación: base del registro de limpieza y de la auditoría."""

    __tablename__ = "import_logs"
    __table_args__ = (
        CheckConstraint(
            "rows_read >= 0 AND rows_accepted >= 0 AND rows_rejected >= 0", name="counts"
        ),
        CheckConstraint("rows_accepted + rows_rejected <= rows_read", name="counts_consistent"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    mode: Mapped[ImportMode] = mapped_column(text_enum(ImportMode, "import_mode"))
    status: Mapped[ImportStatus] = mapped_column(text_enum(ImportStatus, "import_status"))
    filename: Mapped[str] = mapped_column(String(255))
    sha256: Mapped[str] = mapped_column(String(64))
    rows_read: Mapped[int] = mapped_column(default=0)
    rows_accepted: Mapped[int] = mapped_column(default=0)
    rows_rejected: Mapped[int] = mapped_column(default=0)
    rejections: Mapped[str | None] = mapped_column(Text)  # JSON agrupado por motivo
    cutoff_applied: Mapped[date]
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
