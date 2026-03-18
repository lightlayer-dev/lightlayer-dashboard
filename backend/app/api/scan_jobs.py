"""Scan job trigger and status API — run agent-bench from the dashboard."""

from __future__ import annotations

import asyncio
import json
import tempfile
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Site, Scan, CheckResult, ScanJob
from app.api.users import get_current_user
from app.models import User

router = APIRouter(prefix="/api/scan-jobs", tags=["scan-jobs"])


class TriggerScanRequest(BaseModel):
    url: str


class ScanJobOut(BaseModel):
    id: int
    url: str
    status: str
    overall_score: float | None
    scan_id: int | None
    error: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


@router.post("/", response_model=ScanJobOut, status_code=201)
async def trigger_scan(
    body: TriggerScanRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Trigger a new agent-bench scan for a URL."""
    # Check for existing running job for same URL+user
    existing = await db.execute(
        select(ScanJob).where(
            ScanJob.user_id == user.id,
            ScanJob.url == body.url,
            ScanJob.status.in_(["pending", "running"]),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A scan for this URL is already in progress")

    job = ScanJob(user_id=user.id, url=body.url, status="pending")
    db.add(job)
    await db.commit()
    await db.refresh(job)

    background_tasks.add_task(run_scan_job, job.id, body.url, user.id)

    return job


@router.get("/{job_id}", response_model=ScanJobOut)
async def get_scan_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get scan job status."""
    result = await db.execute(
        select(ScanJob).where(ScanJob.id == job_id, ScanJob.user_id == user.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Scan job not found")
    return job


@router.get("/", response_model=list[ScanJobOut])
async def list_scan_jobs(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List recent scan jobs for the current user."""
    result = await db.execute(
        select(ScanJob)
        .where(ScanJob.user_id == user.id)
        .order_by(ScanJob.created_at.desc())
        .limit(20)
    )
    return result.scalars().all()


_session_factory_override = None


def set_session_factory(factory):
    """Allow tests to override the session factory used by background tasks."""
    global _session_factory_override
    _session_factory_override = factory


async def run_scan_job(job_id: int, url: str, user_id: int) -> None:
    """Background task: run agent-bench and ingest results."""
    from app.database import async_session_factory
    factory = _session_factory_override or async_session_factory

    async with factory() as db:
        # Mark as running
        result = await db.execute(select(ScanJob).where(ScanJob.id == job_id))
        job = result.scalar_one()
        job.status = "running"
        await db.commit()

        try:
            # Run agent-bench as subprocess
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
                output_path = f.name

            proc = await asyncio.create_subprocess_exec(
                "agent-bench", "analyze", url, "--format", "json", "--output", output_path, "--quiet",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

            if proc.returncode != 0:
                raise RuntimeError(f"agent-bench failed (exit {proc.returncode}): {stderr.decode()[:500]}")

            # Read results
            import pathlib
            raw = pathlib.Path(output_path).read_text()
            data = json.loads(raw)

            # Ingest scan (same logic as POST /api/scans/)
            result = await db.execute(select(Site).where(Site.url == data["url"]))
            site = result.scalar_one_or_none()
            if not site:
                site = Site(url=data["url"], user_id=user_id)
                db.add(site)
                await db.flush()
            elif site.user_id is None:
                site.user_id = user_id

            scan = Scan(
                site_id=site.id,
                overall_score=data["overall_score"],
                source="dashboard",
                raw_json=raw,
            )
            db.add(scan)
            await db.flush()

            for check in data.get("checks", []):
                cr = CheckResult(
                    scan_id=scan.id,
                    check_name=check["name"],
                    score=check["score"],
                    findings_json=json.dumps(check.get("findings", [])),
                    details_json=json.dumps(check.get("details")) if check.get("details") else None,
                )
                db.add(cr)

            # Update job
            job.status = "completed"
            job.overall_score = data["overall_score"]
            job.scan_id = scan.id
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()

        except Exception as e:
            job.status = "failed"
            job.error = str(e)[:1000]
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()
