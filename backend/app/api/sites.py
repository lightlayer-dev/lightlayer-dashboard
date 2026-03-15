"""Sites API — list and retrieve tracked sites."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Site, Scan, CheckResult
from app.api.schemas import SiteOut, ScoreTrendPoint, ScanOut, CheckResultOut

router = APIRouter(prefix="/api/sites", tags=["sites"])


@router.get("/", response_model=list[SiteOut])
async def list_sites(db: AsyncSession = Depends(get_db)):
    """List all tracked sites with their latest score."""
    # Subquery for latest score per site
    latest_scan = (
        select(Scan.site_id, Scan.overall_score, func.max(Scan.created_at).label("latest"))
        .group_by(Scan.site_id, Scan.overall_score)
        .subquery()
    )

    result = await db.execute(select(Site).order_by(Site.created_at.desc()))
    sites = result.scalars().all()

    out = []
    for site in sites:
        # Get latest score and count
        score_result = await db.execute(
            select(Scan.overall_score)
            .where(Scan.site_id == site.id)
            .order_by(Scan.created_at.desc())
            .limit(1)
        )
        latest_score = score_result.scalar_one_or_none()

        count_result = await db.execute(
            select(func.count()).where(Scan.site_id == site.id)
        )
        scan_count = count_result.scalar()

        out.append(SiteOut(
            id=site.id,
            url=site.url,
            name=site.name,
            created_at=site.created_at,
            latest_score=latest_score,
            scan_count=scan_count or 0,
        ))

    return out


@router.get("/{site_id}/trend", response_model=list[ScoreTrendPoint])
async def get_score_trend(site_id: int, limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Get score history for a site (most recent first)."""
    result = await db.execute(
        select(Scan.created_at, Scan.overall_score, Scan.source)
        .where(Scan.site_id == site_id)
        .order_by(Scan.created_at.desc())
        .limit(limit)
    )
    rows = result.all()
    return [ScoreTrendPoint(date=r[0], score=r[1], source=r[2]) for r in rows]


@router.get("/{site_id}", response_model=SiteOut)
async def get_site(site_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single site by ID."""
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    score_result = await db.execute(
        select(Scan.overall_score)
        .where(Scan.site_id == site.id)
        .order_by(Scan.created_at.desc())
        .limit(1)
    )
    latest_score = score_result.scalar_one_or_none()

    count_result = await db.execute(
        select(func.count()).where(Scan.site_id == site.id)
    )
    scan_count = count_result.scalar()

    return SiteOut(
        id=site.id,
        url=site.url,
        name=site.name,
        created_at=site.created_at,
        latest_score=latest_score,
        scan_count=scan_count or 0,
    )


@router.get("/{site_id}/scans", response_model=list[ScanOut])
async def list_site_scans(site_id: int, limit: int = 50, db: AsyncSession = Depends(get_db)):
    """List scans for a site with check results."""
    from sqlalchemy.orm import selectinload

    # Verify site exists
    site_result = await db.execute(select(Site).where(Site.id == site_id))
    site = site_result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    result = await db.execute(
        select(Scan)
        .where(Scan.site_id == site_id)
        .options(selectinload(Scan.checks))
        .order_by(Scan.created_at.desc())
        .limit(limit)
    )
    scans = result.scalars().all()

    return [
        ScanOut(
            id=s.id,
            site_id=s.site_id,
            url=site.url,
            overall_score=s.overall_score,
            source=s.source,
            commit_sha=s.commit_sha,
            branch=s.branch,
            created_at=s.created_at,
            checks=[CheckResultOut(check_name=c.check_name, score=c.score) for c in s.checks],
        )
        for s in scans
    ]
