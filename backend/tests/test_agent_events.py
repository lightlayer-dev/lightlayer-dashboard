"""Tests for agent event ingestion and analytics API."""

import pytest


SAMPLE_EVENTS = [
    {
        "agent": "ChatGPT",
        "userAgent": "ChatGPT-User/1.0",
        "method": "GET",
        "path": "/api/docs",
        "statusCode": 200,
        "durationMs": 45.2,
        "timestamp": "2026-03-18T12:00:00Z",
    },
    {
        "agent": "ChatGPT",
        "userAgent": "ChatGPT-User/1.0",
        "method": "GET",
        "path": "/api/users",
        "statusCode": 500,
        "durationMs": 120.0,
        "timestamp": "2026-03-18T12:05:00Z",
    },
    {
        "agent": "ClaudeBot",
        "userAgent": "ClaudeBot/1.0",
        "method": "GET",
        "path": "/",
        "statusCode": 200,
        "durationMs": 32.1,
        "timestamp": "2026-03-18T12:01:00Z",
    },
]


@pytest.mark.anyio
async def test_ingest_events(client, api_key_raw):
    resp = await client.post("/api/agent-events/", json={
        "url": "https://example.com",
        "events": SAMPLE_EVENTS[:2],
    }, headers={"X-API-Key": api_key_raw})

    assert resp.status_code == 201
    assert resp.json()["ingested"] == 2


@pytest.mark.anyio
async def test_ingest_empty_batch(client, api_key_raw):
    resp = await client.post("/api/agent-events/", json={
        "events": [],
    }, headers={"X-API-Key": api_key_raw})

    assert resp.status_code == 201
    assert resp.json()["ingested"] == 0


@pytest.mark.anyio
async def test_ingest_requires_api_key(client):
    resp = await client.post("/api/agent-events/", json={
        "url": "https://example.com",
        "events": SAMPLE_EVENTS[:1],
    })
    assert resp.status_code == 401


@pytest.mark.anyio
async def test_analytics_overview(client, test_user, api_key_raw):
    _, jwt_headers = test_user

    # Ingest events
    await client.post("/api/agent-events/", json={
        "url": "https://example.com",
        "events": SAMPLE_EVENTS,
    }, headers={"X-API-Key": api_key_raw})

    resp = await client.get("/api/agent-events/analytics?days=30", headers=jwt_headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_requests"] == 3
    assert data["unique_agents"] == 2
    assert data["error_rate"] > 0
    assert len(data["by_agent"]) == 2
    assert data["by_agent"][0]["agent"] == "ChatGPT"
    assert data["by_agent"][0]["request_count"] == 2
    assert len(data["daily_traffic"]) >= 1


@pytest.mark.anyio
async def test_analytics_empty(client, test_user):
    _, jwt_headers = test_user

    resp = await client.get("/api/agent-events/analytics?days=30", headers=jwt_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_requests"] == 0
    assert data["by_agent"] == []


@pytest.mark.anyio
async def test_ingest_creates_site(client, api_key_raw):
    """Ingesting events with a URL auto-creates the site."""
    resp = await client.post("/api/agent-events/", json={
        "url": "https://newsite.example.com",
        "events": SAMPLE_EVENTS[:1],
    }, headers={"X-API-Key": api_key_raw})

    assert resp.status_code == 201
    assert resp.json()["ingested"] == 1
