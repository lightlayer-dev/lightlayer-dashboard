"""Sites API — list and retrieve tracked sites."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Site, Scan
from app.api.schemas import SiteOut, ScoreTrendPoint

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
