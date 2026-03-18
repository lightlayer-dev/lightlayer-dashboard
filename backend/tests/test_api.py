"""API integration tests."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ── Health ──────────────────────────────────────────────────────────────


async def test_health(client: AsyncClient):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── API Keys ────────────────────────────────────────────────────────────


async def test_create_api_key(client: AsyncClient):
    r = await client.post("/api/keys/", json={"name": "my-key"})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "my-key"
    assert data["key"].startswith("ll_")


async def test_list_api_keys(client: AsyncClient):
    await client.post("/api/keys/", json={"name": "key-1"})
    await client.post("/api/keys/", json={"name": "key-2"})
    r = await client.get("/api/keys/")
    assert r.status_code == 200
    assert len(r.json()) == 2


async def test_revoke_api_key(client: AsyncClient):
    create_r = await client.post("/api/keys/", json={"name": "to-revoke"})
    key_id = create_r.json()["id"]
    r = await client.delete(f"/api/keys/{key_id}")
    assert r.status_code == 204


# ── Scan Ingestion ──────────────────────────────────────────────────────


SAMPLE_SCAN = {
    "url": "https://api.example.com",
    "overall_score": 0.72,
    "checks": [
        {"name": "api", "score": 0.9, "findings": ["Has OpenAPI spec"]},
        {"name": "docs", "score": 0.6, "findings": ["Docs found"]},
    ],
    "source": "cli",
}


async def test_ingest_scan_requires_auth(client: AsyncClient):
    r = await client.post("/api/scans/", json=SAMPLE_SCAN)
    assert r.status_code == 401


async def test_ingest_scan_invalid_key(client: AsyncClient):
    r = await client.post(
        "/api/scans/", json=SAMPLE_SCAN, headers={"X-API-Key": "ll_bogus"}
    )
    assert r.status_code == 401


async def test_ingest_scan_success(client: AsyncClient, api_key_raw: str):
    r = await client.post(
        "/api/scans/", json=SAMPLE_SCAN, headers={"X-API-Key": api_key_raw}
    )
    assert r.status_code == 201
    data = r.json()
    assert data["overall_score"] == 0.72
    assert len(data["checks"]) == 2


async def test_get_scan(client: AsyncClient, api_key_raw: str):
    create_r = await client.post(
        "/api/scans/", json=SAMPLE_SCAN, headers={"X-API-Key": api_key_raw}
    )
    scan_id = create_r.json()["id"]
    r = await client.get(f"/api/scans/{scan_id}")
    assert r.status_code == 200
    assert r.json()["id"] == scan_id


# ── Sites ───────────────────────────────────────────────────────────────


async def test_list_sites_empty(client: AsyncClient):
    r = await client.get("/api/sites/")
    assert r.status_code == 200
    assert r.json() == []


async def test_list_sites_after_scan(client: AsyncClient, api_key_raw: str):
    await client.post(
        "/api/scans/", json=SAMPLE_SCAN, headers={"X-API-Key": api_key_raw}
    )
    r = await client.get("/api/sites/")
    assert r.status_code == 200
    sites = r.json()
    assert len(sites) == 1
    assert sites[0]["url"] == "https://api.example.com"
    assert sites[0]["latest_score"] == 0.72
    assert sites[0]["scan_count"] == 1


async def test_site_trend(client: AsyncClient, api_key_raw: str):
    headers = {"X-API-Key": api_key_raw}
    # Ingest two scans
    r1 = await client.post("/api/scans/", json=SAMPLE_SCAN, headers=headers)
    scan2 = {**SAMPLE_SCAN, "overall_score": 0.85}
    await client.post("/api/scans/", json=scan2, headers=headers)

    site_id = r1.json()["site_id"]
    r = await client.get(f"/api/sites/{site_id}/trend")
    assert r.status_code == 200
    assert len(r.json()) == 2


async def test_site_scans(client: AsyncClient, api_key_raw: str):
    headers = {"X-API-Key": api_key_raw}
    r1 = await client.post("/api/scans/", json=SAMPLE_SCAN, headers=headers)
    site_id = r1.json()["site_id"]
    r = await client.get(f"/api/sites/{site_id}/scans")
    assert r.status_code == 200
    assert len(r.json()) == 1


async def test_revoked_key_rejected(client: AsyncClient, api_key_raw: str):
    """After revoking, the key should no longer work."""
    # First create a key via the API so we can revoke it
    create_r = await client.post("/api/keys/", json={"name": "ephemeral"})
    key_data = create_r.json()
    raw = key_data["key"]

    # Verify it works
    r = await client.post("/api/scans/", json=SAMPLE_SCAN, headers={"X-API-Key": raw})
    assert r.status_code == 201

    # Revoke it
    await client.delete(f"/api/keys/{key_data['id']}")

    # Should fail now
    r = await client.post("/api/scans/", json=SAMPLE_SCAN, headers={"X-API-Key": raw})
    assert r.status_code == 401
