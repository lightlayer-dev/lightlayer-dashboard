"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agent_events, api_keys, scan_jobs, scans, sites, users
from app.config import settings

from agent_layer.fastapi import configure_agent_layer
from agent_layer.types import (
    AgentLayerConfig,
    LlmsTxtConfig,
    LlmsTxtSection,
)
from agent_layer.a2a import (
    A2AConfig,
    A2AAgentCard,
    A2AProvider,
    A2ASkill,
    A2ACapabilities,
    A2AAuthScheme,
)

app = FastAPI(title=settings.app_name, version="0.1.0")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Agent Layer Integration ─────────────────────────────────────────────
# Dogfooding: LightLayer Dashboard is itself agent-friendly via agent-layer.

configure_agent_layer(
    app,
    AgentLayerConfig(
        errors=True,
        llms_txt=LlmsTxtConfig(
            title="LightLayer Dashboard API",
            description=(
                "Agent-readiness scoring and agent traffic analytics platform. "
                "Evaluate how AI-agent-friendly any website or API is, monitor "
                "agent traffic patterns, and get actionable recommendations."
            ),
            sections=[
                LlmsTxtSection(
                    title="Authentication",
                    content=(
                        "All API endpoints require a Bearer token. "
                        "Create an API key at /settings after signing up. "
                        "Include it as: Authorization: Bearer <api_key>"
                    ),
                ),
                LlmsTxtSection(
                    title="Scanning",
                    content=(
                        "POST /api/scans — Start a new agent-readiness scan. "
                        "Body: {\"url\": \"https://example.com\"}. "
                        "Returns a scan job ID. Poll GET /api/scan-jobs/{id} for results. "
                        "Scans evaluate 8 dimensions: API availability, documentation quality, "
                        "structured data, authentication patterns, error handling, cost transparency, "
                        "accessibility, and performance."
                    ),
                ),
                LlmsTxtSection(
                    title="Results",
                    content=(
                        "GET /api/scans — List all scans with scores. "
                        "GET /api/scans/{id} — Detailed scan results with per-check breakdown. "
                        "Scores range 0-100. Each check provides specific recommendations."
                    ),
                ),
                LlmsTxtSection(
                    title="Sites",
                    content=(
                        "GET /api/sites — List monitored sites. "
                        "POST /api/sites — Add a site for continuous monitoring. "
                        "Sites track agent-readiness score over time."
                    ),
                ),
            ],
        ),
        a2a=A2AConfig(
            card=A2AAgentCard(
                name="LightLayer Dashboard",
                description=(
                    "Agent-readiness scoring and analytics platform. "
                    "Scan any URL to evaluate how AI-agent-friendly it is, "
                    "with actionable recommendations across 8 dimensions."
                ),
                url="https://dashboard.lightlayer.dev",
                version="0.1.0",
                documentation_url="https://company.lightlayer.dev",
                provider=A2AProvider(
                    organization="LightLayer",
                    url="https://company.lightlayer.dev",
                ),
                capabilities=A2ACapabilities(
                    streaming=False,
                    push_notifications=False,
                ),
                authentication=A2AAuthScheme(
                    type="bearer",
                    in_="header",
                    name="Authorization",
                ),
                skills=[
                    A2ASkill(
                        id="scan-url",
                        name="Scan URL for Agent-Readiness",
                        description=(
                            "Evaluate how AI-agent-friendly a website or API is. "
                            "Returns a score (0-100) with per-check breakdown and recommendations."
                        ),
                        tags=["scanning", "evaluation", "agent-readiness"],
                        examples=[
                            "Scan https://stripe.com for agent-readiness",
                            "How agent-friendly is the GitHub API?",
                        ],
                        input_modes=["text/plain", "application/json"],
                        output_modes=["application/json"],
                    ),
                    A2ASkill(
                        id="list-scans",
                        name="List Scan Results",
                        description="Retrieve past scan results and scores.",
                        tags=["results", "history"],
                        input_modes=["text/plain"],
                        output_modes=["application/json"],
                    ),
                    A2ASkill(
                        id="monitor-site",
                        name="Monitor Site Agent-Readiness",
                        description=(
                            "Add a site for continuous agent-readiness monitoring. "
                            "Track score changes over time."
                        ),
                        tags=["monitoring", "continuous"],
                        input_modes=["application/json"],
                        output_modes=["application/json"],
                    ),
                ],
            ),
        ),
    ),
)

# ── Application Routes ──────────────────────────────────────────────────

app.include_router(users.router)
app.include_router(api_keys.router)
app.include_router(agent_events.router)
app.include_router(scans.router)
app.include_router(scan_jobs.router)
app.include_router(sites.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.app_name}
