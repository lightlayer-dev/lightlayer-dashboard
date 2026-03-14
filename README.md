# LightLayer Dashboard

**Agent-readiness scoring + agent traffic analytics.**

Track your website's agent-readiness score over time, gate CI pipelines on score thresholds, and monitor agent traffic hitting your APIs.

## Architecture

```
frontend/    React + TypeScript (Vite)
backend/     FastAPI + SQLAlchemy + Postgres
```

## Quick Start

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Set up Postgres (update DATABASE_URL in .env)
export LIGHTLAYER_DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/lightlayer"
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Ingest a scan

```bash
# Run agent-bench and post results to the dashboard:
agent-bench analyze https://api.example.com --output scan.json
curl -X POST http://localhost:8000/api/scans/ \
  -H "Content-Type: application/json" \
  -d @scan.json
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/scans/` | Ingest an agent-bench result |
| GET | `/api/scans/:id` | Get a single scan |
| GET | `/api/sites/` | List all tracked sites |
| GET | `/api/sites/:id/trend` | Score history for a site |
| GET | `/api/health` | Health check |

## Companion Projects

- **[agent-bench](https://github.com/lightlayer-dev/agent-bench)** — CLI to score agent-readiness
- **[agent-layer-ts](https://github.com/lightlayer-dev/agent-layer-ts)** — TypeScript middleware
- **[agent-layer-python](https://github.com/lightlayer-dev/agent-layer-python)** — Python middleware

## License

MIT
