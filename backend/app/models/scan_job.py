"""ScanJob model — tracks async scan requests triggered from the dashboard."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Float, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    url: Mapped[str] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, running, completed, failed
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    scan_id: Mapped[int | None] = mapped_column(ForeignKey("scans.id"), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    scan: Mapped["Scan | None"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<ScanJob id={self.id} url={self.url} status={self.status}>"
