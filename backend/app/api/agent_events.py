"""Agent event ingestion and analytics API.

Receives telemetry from agent-layer middleware and provides analytics queries.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import String, func, select, case, cast
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Site, AgentEvent
from app.models import ApiKey as ApiKeyModel
from app.models import User
from app.auth import get_api_key
from app.api.users import get_current_user

router = APIRouter(prefix="/api/agent-events", tags=["agent-events"])


# ── Schemas ──────────────────────────────────────────────────────────────


class AgentEventIn(BaseModel):
    agent: str
    userAgent: str
    method: str
    path: str
    statusCode: int
    durationMs: float
    timestamp: str  # ISO 8601
    contentType: str | None = None
    responseSize: int | None = None


class EventBatchIn(BaseModel):
    """Batch of events sent by agent-layer middleware."""
    url: str | None = None  # Site URL; if absent, derived from API key's sites
    events: list[AgentEventIn] = Field(..., max_length=500)


class EventBatchOut(BaseModel):
    ingested: int


class AgentSummary(BaseModel):
    agent: str
    request_count: int
    avg_duration_ms: float
    error_count: int  # 4xx + 5xx
    last_seen: str


class TrafficPoint(BaseModel):
    date: str  # YYYY-MM-DD
    count: int


class AnalyticsOverview(BaseModel):
    total_requests: int
    unique_agents: int
    avg_duration_ms: float
    error_rate: float
    by_agent: list[AgentSummary]
    daily_traffic: list[TrafficPoint]


# ── Ingestion (API key auth — used by middleware) ────────────────────────


@router.post("/", response_model=EventBatchOut, status_code=201)
async def ingest_events(
    payload: EventBatchIn,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKeyModel = Depends(get_api_key),
):
    """Ingest a batch of agent events from agent-layer middleware."""
    if not payload.events:
        return EventBatchOut(ingested=0)

    # Resolve site
    site = None
    if payload.url:
        result = await db.execute(select(Site).where(Site.url == payload.url))
        site = result.scalar_one_or_none()
        if not site:
            site = Site(url=payload.url, user_id=api_key.user_id)
            db.add(site)
            await db.flush()

    if not site:
        # Try to find a site owned by this user (use first one)
        result = await db.execute(
            select(Site).where(Site.user_id == api_key.user_id).limit(1)
        )
        site = result.scalar_one_or_none()
        if not site:
            raise HTTPException(
                status_code=400,
                detail="No site found. Provide 'url' in the payload or create a site first.",
            )

    count = 0
    for ev in payload.events:
        try:
            ts = datetime.fromisoformat(ev.timestamp.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            ts = datetime.now(timezone.utc)

        event = AgentEvent(
            site_id=site.id,
            agent_name=ev.agent,
            user_agent=ev.userAgent,
            method=ev.method,
            path=ev.path,
            status_code=ev.statusCode,
            duration_ms=ev.durationMs,
            content_type=ev.contentType,
            response_size=ev.responseSize,
            event_timestamp=ts,
        )
        db.add(event)
        count += 1

    await db.commit()
    return EventBatchOut(ingested=count)


# ── Analytics queries (JWT auth — used by dashboard frontend) ────────────


@router.get("/analytics", response_model=AnalyticsOverview)
async def get_analytics(
    site_id: int | None = Query(None),
    days: int = Query(30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get agent traffic analytics for the authenticated user's sites."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Base filter: user's sites, within time range
    base_filter = [
        AgentEvent.event_timestamp >= since,
        Site.user_id == user.id,
    ]
    if site_id:
        base_filter.append(AgentEvent.site_id == site_id)

    # Overall stats
    stats_q = (
        select(
            func.count(AgentEvent.id).label("total"),
            func.count(func.distinct(AgentEvent.agent_name)).label("unique_agents"),
            func.coalesce(func.avg(AgentEvent.duration_ms), 0).label("avg_duration"),
            func.coalesce(
                func.sum(
                    case(
                        (AgentEvent.status_code >= 400, 1),
                        else_=0,
                    )
                ),
                0,
            ).label("errors"),
        )
        .select_from(AgentEvent)
        .join(Site, AgentEvent.site_id == Site.id)
        .where(*base_filter)
    )
    result = await db.execute(stats_q)
    row = result.one()
    total = row.total or 0
    error_rate = (row.errors / total) if total > 0 else 0.0

    # By agent breakdown
    agent_q = (
        select(
            AgentEvent.agent_name,
            func.count(AgentEvent.id).label("cnt"),
            func.avg(AgentEvent.duration_ms).label("avg_dur"),
            func.sum(
                case((AgentEvent.status_code >= 400, 1), else_=0)
            ).label("errs"),
            cast(func.max(AgentEvent.event_timestamp), String).label("last_seen"),
        )
        .select_from(AgentEvent)
        .join(Site, AgentEvent.site_id == Site.id)
        .where(*base_filter)
        .group_by(AgentEvent.agent_name)
        .order_by(func.count(AgentEvent.id).desc())
    )
    agent_rows = (await db.execute(agent_q)).all()

    by_agent = [
        AgentSummary(
            agent=r.agent_name,
            request_count=r.cnt,
            avg_duration_ms=round(r.avg_dur, 1),
            error_count=r.errs,
            last_seen=r.last_seen,
        )
        for r in agent_rows
    ]

    # Daily traffic — use substr for SQLite compat, cast(Date) for Postgres
    day_expr = func.substr(cast(AgentEvent.event_timestamp, String), 1, 10)
    daily_q = (
        select(
            day_expr.label("day"),
            func.count(AgentEvent.id).label("cnt"),
        )
        .select_from(AgentEvent)
        .join(Site, AgentEvent.site_id == Site.id)
        .where(*base_filter)
        .group_by(day_expr)
        .order_by(day_expr)
    )
    daily_rows = (await db.execute(daily_q)).all()
    daily_traffic = [
        TrafficPoint(date=str(r.day), count=r.cnt)
        for r in daily_rows
    ]

    return AnalyticsOverview(
        total_requests=total,
        unique_agents=row.unique_agents or 0,
        avg_duration_ms=round(row.avg_duration, 1),
        error_rate=round(error_rate, 4),
        by_agent=by_agent,
        daily_traffic=daily_traffic,
    )
