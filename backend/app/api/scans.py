"""Scan ingestion and retrieval API."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Site, Scan, CheckResult
from app.api.schemas import ScanIn, ScanOut, CheckResultOut
from app.auth import get_api_key
from app.models import ApiKey as ApiKeyModel

router = APIRouter(prefix="/api/scans", tags=["scans"])


@router.post("/", response_model=ScanOut, status_code=201)
async def ingest_scan(
    payload: ScanIn,
    db: AsyncSession = Depends(get_db),
    _api_key: ApiKeyModel = Depends(get_api_key),
):
    """Ingest an agent-bench analysis result.

    Creates the site if it doesn't exist, then stores the scan with all check results.
    """
    # Find or create site (scoped to the API key's owner)
    owner_id = _api_key.user_id
    result = await db.execute(select(Site).where(Site.url == payload.url))
    site = result.scalar_one_or_none()

    if not site:
        site = Site(url=payload.url, user_id=owner_id)
        db.add(site)
        await db.flush()
    elif site.user_id is None and owner_id is not None:
        # Claim orphaned site
        site.user_id = owner_id

    # Create scan
    scan = Scan(
        site_id=site.id,
        overall_score=payload.overall_score,
        source=payload.source,
        commit_sha=payload.commit_sha,
        branch=payload.branch,
        raw_json=json.dumps(payload.model_dump()),
    )
    db.add(scan)
    await db.flush()

    # Create check results
    for check in payload.checks:
        cr = CheckResult(
            scan_id=scan.id,
            check_name=check.name,
            score=check.score,
            findings_json=json.dumps(check.findings) if check.findings else None,
            details_json=json.dumps(check.details) if check.details else None,
        )
        db.add(cr)

    await db.commit()
    await db.refresh(scan, ["checks"])

    return ScanOut(
        id=scan.id,
        site_id=scan.site_id,
        url=site.url,
        overall_score=scan.overall_score,
        source=scan.source,
        commit_sha=scan.commit_sha,
        branch=scan.branch,
        created_at=scan.created_at,
        checks=[CheckResultOut(check_name=c.check_name, score=c.score) for c in scan.checks],
    )


@router.get("/{scan_id}", response_model=ScanOut)
async def get_scan(scan_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single scan by ID."""
    result = await db.execute(
        select(Scan).where(Scan.id == scan_id).options(selectinload(Scan.checks), selectinload(Scan.site))
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    return ScanOut(
        id=scan.id,
        site_id=scan.site_id,
        url=scan.site.url,
        overall_score=scan.overall_score,
        source=scan.source,
        commit_sha=scan.commit_sha,
        branch=scan.branch,
        created_at=scan.created_at,
        checks=[CheckResultOut(check_name=c.check_name, score=c.score) for c in scan.checks],
    )
