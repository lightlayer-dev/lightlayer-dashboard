"""AgentEvent model — individual AI agent request tracked by agent-layer middleware."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    site_id: Mapped[int] = mapped_column(ForeignKey("sites.id"), index=True)
    agent_name: Mapped[str] = mapped_column(String(100), index=True)  # e.g. "ChatGPT", "ClaudeBot"
    user_agent: Mapped[str] = mapped_column(String(1024))
    method: Mapped[str] = mapped_column(String(10))  # GET, POST, etc.
    path: Mapped[str] = mapped_column(String(2048))
    status_code: Mapped[int] = mapped_column(Integer)
    duration_ms: Mapped[float] = mapped_column(Float)
    content_type: Mapped[str | None] = mapped_column(String(255))
    response_size: Mapped[int | None] = mapped_column(Integer)
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True
    )  # When the event actually occurred (from client)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )  # When we received it
