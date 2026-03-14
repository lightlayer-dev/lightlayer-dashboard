"""Scan model — a single agent-bench analysis result."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), index=True)
    overall_score: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(50), default="api")  # "api", "ci", "cli"
    commit_sha: Mapped[str | None] = mapped_column(String(40))
    branch: Mapped[str | None] = mapped_column(String(255))
    raw_json: Mapped[str | None] = mapped_column(Text)  # Full agent-bench JSON
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    site: Mapped["Site"] = relationship(back_populates="scans")
    checks: Mapped[list["CheckResult"]] = relationship(
        back_populates="scan", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Scan site_id={self.site_id} score={self.overall_score:.0%}>"


class CheckResult(Base):
    __tablename__ = "check_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id"), index=True)
    check_name: Mapped[str] = mapped_column(String(50))  # "api", "docs", "structure", etc.
    score: Mapped[float] = mapped_column(Float)
    findings_json: Mapped[str | None] = mapped_column(Text)  # JSON array of finding strings
    details_json: Mapped[str | None] = mapped_column(Text)  # Full check details

    scan: Mapped["Scan"] = relationship(back_populates="checks")

    def __repr__(self) -> str:
        return f"<CheckResult {self.check_name}={self.score:.0%}>"
