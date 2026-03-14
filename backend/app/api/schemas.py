"""Pydantic schemas for API requests/responses."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


# ── Scan Ingestion ──────────────────────────────────────────────────────


class CheckResultIn(BaseModel):
    name: str
    score: float
    findings: list[str] = Field(default_factory=list)
    details: dict | None = None


class ScanIn(BaseModel):
    """Payload from agent-bench CLI or CI integration."""
    url: str
    overall_score: float
    checks: list[CheckResultIn]
    source: str = "api"  # "api", "ci", "cli"
    commit_sha: str | None = None
    branch: str | None = None


class ScanOut(BaseModel):
    id: int
    site_id: int
    url: str
    overall_score: float
    source: str
    commit_sha: str | None
    branch: str | None
    created_at: datetime
    checks: list[CheckResultOut]

    model_config = {"from_attributes": True}


class CheckResultOut(BaseModel):
    check_name: str
    score: float

    model_config = {"from_attributes": True}


# ── Sites ───────────────────────────────────────────────────────────────


class SiteOut(BaseModel):
    id: int
    url: str
    name: str | None
    created_at: datetime
    latest_score: float | None = None
    scan_count: int = 0

    model_config = {"from_attributes": True}


# ── Score Trend ─────────────────────────────────────────────────────────


class ScoreTrendPoint(BaseModel):
    date: datetime
    score: float
    source: str
