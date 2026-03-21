"""Tests for agent-layer integration (dogfooding)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_llms_txt_served():
    """Dashboard serves /llms.txt for LLM agents."""
    r = client.get("/llms.txt")
    assert r.status_code == 200
    assert "text/plain" in r.headers["content-type"]
    assert "LightLayer Dashboard API" in r.text
    assert "Authentication" in r.text
    assert "Scanning" in r.text


def test_llms_txt_content_sections():
    """llms.txt includes all key API sections."""
    r = client.get("/llms.txt")
    text = r.text
    assert "POST /api/scans" in text
    assert "GET /api/scans" in text
    assert "GET /api/sites" in text
    assert "Bearer" in text


def test_a2a_agent_card_served():
    """Dashboard serves /.well-known/agent.json per A2A protocol."""
    r = client.get("/.well-known/agent.json")
    assert r.status_code == 200
    card = r.json()
    assert card["name"] == "LightLayer Dashboard"
    assert card["protocolVersion"] == "1.0.0"
    assert card["url"] == "https://dashboard.lightlayer.dev"


def test_a2a_agent_card_skills():
    """Agent card advertises scanning and monitoring skills."""
    r = client.get("/.well-known/agent.json")
    card = r.json()
    skill_ids = [s["id"] for s in card["skills"]]
    assert "scan-url" in skill_ids
    assert "list-scans" in skill_ids
    assert "monitor-site" in skill_ids


def test_a2a_agent_card_provider():
    """Agent card includes LightLayer provider info."""
    r = client.get("/.well-known/agent.json")
    card = r.json()
    assert card["provider"]["organization"] == "LightLayer"


def test_a2a_agent_card_auth():
    """Agent card declares bearer authentication."""
    r = client.get("/.well-known/agent.json")
    card = r.json()
    assert card["authentication"]["type"] == "bearer"


def test_a2a_cache_control():
    """Agent card includes cache headers."""
    r = client.get("/.well-known/agent.json")
    assert "max-age" in r.headers.get("cache-control", "")


def test_health_still_works():
    """Health endpoint unaffected by agent-layer integration."""
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
