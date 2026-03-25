"""Public scan API — no auth required, rate-limited by IP."""

from __future__ import annotations

import json
import time
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import ScanJob, Scan
from fastapi import Depends

router = APIRouter(prefix="/api/public", tags=["public"])

# ── In-memory rate limiter ──────────────────────────────────────────────

_rate_limit: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 3600  # 1 hour


def _check_rate_limit(ip: str) -> None:
    """Raise 429 if IP has exceeded rate limit."""
    now = time.time()
    # Prune old entries
    _rate_limit[ip] = [t for t in _rate_limit[ip] if now - t < RATE_LIMIT_WINDOW]
    if len(_rate_limit[ip]) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT_MAX} scans per hour.",
            headers={"Retry-After": str(RATE_LIMIT_WINDOW)},
        )
    _rate_limit[ip].append(now)


# ── Request / Response schemas ──────────────────────────────────────────


class PublicScanRequest(BaseModel):
    url: str


class PublicScanResponse(BaseModel):
    job_id: int
    status: str


class PublicCheckResult(BaseModel):
    check_name: str
    score: float
    findings: list[str] = []


class PublicScanResult(BaseModel):
    job_id: int
    url: str
    status: str
    overall_score: float | None = None
    checks: list[PublicCheckResult] = []
    error: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


# ── Endpoints ───────────────────────────────────────────────────────────


@router.post("/scan", response_model=PublicScanResponse, status_code=201)
async def public_scan(
    body: PublicScanRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger a public agent-readiness scan. No auth required, rate-limited by IP."""
    # Validate URL
    url = body.url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(status_code=422, detail="Invalid URL. Must be http:// or https://")
    if len(url) > 2048:
        raise HTTPException(status_code=422, detail="URL too long (max 2048 characters)")

    # Rate limit by client IP
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    # Check for existing running public job for same URL
    existing = await db.execute(
        select(ScanJob).where(
            ScanJob.url == url,
            ScanJob.user_id.is_(None),
            ScanJob.status.in_(["pending", "running"]),
        )
    )
    existing_job = existing.scalar_one_or_none()
    if existing_job:
        return PublicScanResponse(job_id=existing_job.id, status=existing_job.status)

    # Create job (no user_id = public)
    job = ScanJob(user_id=None, url=url, status="pending")
    db.add(job)
    await db.commit()
    await db.refresh(job)

    background_tasks.add_task(_run_public_scan, job.id, url)

    return PublicScanResponse(job_id=job.id, status="pending")


@router.get("/scan/{job_id}", response_model=PublicScanResult)
async def get_public_scan(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Poll for public scan results."""
    result = await db.execute(
        select(ScanJob).where(ScanJob.id == job_id, ScanJob.user_id.is_(None))
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Scan not found")

    checks: list[PublicCheckResult] = []
    if job.scan_id:
        scan_result = await db.execute(
            select(Scan)
            .where(Scan.id == job.scan_id)
            .options(selectinload(Scan.checks))
        )
        scan = scan_result.scalar_one_or_none()
        if scan:
            for c in scan.checks:
                findings = []
                if c.findings_json:
                    try:
                        findings = json.loads(c.findings_json)
                    except (json.JSONDecodeError, TypeError):
                        pass
                checks.append(PublicCheckResult(
                    check_name=c.check_name,
                    score=c.score,
                    findings=findings if isinstance(findings, list) else [],
                ))

    return PublicScanResult(
        job_id=job.id,
        url=job.url,
        status=job.status,
        overall_score=job.overall_score,
        checks=checks,
        error=job.error,
        created_at=job.created_at,
        completed_at=job.completed_at,
    )


# ── Background task ────────────────────────────────────────────────────


async def _run_public_scan(job_id: int, url: str) -> None:
    """Background task: run agent-bench for a public scan."""
    # Reuse the same logic as scan_jobs.run_scan_job but with user_id=None
    from app.api.scan_jobs import run_scan_job
    await run_scan_job(job_id, url, user_id=None)
