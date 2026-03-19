"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agent_events, api_keys, scan_jobs, scans, sites, users
from app.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(api_keys.router)
app.include_router(agent_events.router)
app.include_router(scans.router)
app.include_router(scan_jobs.router)
app.include_router(sites.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.app_name}
