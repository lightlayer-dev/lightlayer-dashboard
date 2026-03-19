"""Scan job trigger API tests."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

MOCK_BENCH_RESULT = {
    "url": "https://example.com",
    "overall_score": 0.42,
    "checks": [
        {"name": "api", "score": 0.0, "findings": ["No API found"], "details": {}},
        {"name": "docs", "score": 0.8, "findings": ["README found"], "details": {}},
    ],
}


async def test_trigger_scan_requires_auth(client: AsyncClient):
    r = await client.post("/api/scan-jobs/", json={"url": "https://example.com"})
    assert r.status_code == 401


async def test_trigger_scan(client: AsyncClient, test_user):
    _, headers = test_user
    r = await client.post("/api/scan-jobs/", json={"url": "https://example.com"}, headers=headers)
    assert r.status_code == 201
    data = r.json()
    assert data["url"] == "https://example.com"
    assert data["status"] == "pending"
    assert data["id"] > 0


async def test_list_scan_jobs(client: AsyncClient, test_user):
    _, headers = test_user
    # Create a job
    await client.post("/api/scan-jobs/", json={"url": "https://example.com"}, headers=headers)
    r = await client.get("/api/scan-jobs/", headers=headers)
    assert r.status_code == 200
    jobs = r.json()
    assert len(jobs) >= 1
    assert jobs[0]["url"] == "https://example.com"


async def test_get_scan_job(client: AsyncClient, test_user):
    _, headers = test_user
    create = await client.post("/api/scan-jobs/", json={"url": "https://a.com"}, headers=headers)
    job_id = create.json()["id"]
    r = await client.get(f"/api/scan-jobs/{job_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["id"] == job_id


async def test_get_scan_job_not_found(client: AsyncClient, test_user):
    _, headers = test_user
    r = await client.get("/api/scan-jobs/99999", headers=headers)
    assert r.status_code == 404


async def test_duplicate_running_scan_rejected(client: AsyncClient, test_user):
    """Duplicate scan for same URL is rejected if one is still pending/running."""
    from tests.conftest import TestSession
    from app.models import ScanJob

    user_id, headers = test_user
    # Manually insert a "running" job so the background task can't change it
    async with TestSession() as session:
        job = ScanJob(user_id=user_id, url="https://dup.com", status="running")
        session.add(job)
        await session.commit()

    r = await client.post("/api/scan-jobs/", json={"url": "https://dup.com"}, headers=headers)
    assert r.status_code == 409
