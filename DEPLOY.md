# Deploying LightLayer Dashboard on Railway

The dashboard runs 3 services on Railway: **Postgres** (managed), **Backend** (FastAPI), and **Frontend** (static via nginx).

## Prerequisites

- Railway account connected to `lightlayer-dev` GitHub org
- Domain `app.lightlayer.dev` (DNS already points to Railway)

## Setup Steps

### 1. Create Railway Project

```bash
railway login
railway init  # or link existing project
```

### 2. Add PostgreSQL

In Railway dashboard → New → Database → PostgreSQL.

Railway auto-provides `DATABASE_URL`. Note: it uses `postgresql://` scheme; our app needs `postgresql+asyncpg://`.

### 3. Deploy Backend

Create a new service from the `lightlayer-dashboard` repo.

**Root directory:** `backend`  
**Builder:** Dockerfile  

**Environment variables:**
```
LIGHTLAYER_DATABASE_URL=${{Postgres.DATABASE_URL}}  # Railway template variable
LIGHTLAYER_SECRET_KEY=<generate with: openssl rand -hex 32>
LIGHTLAYER_CORS_ORIGINS=https://app.lightlayer.dev
PORT=8000
```

> **Important:** Railway's Postgres `DATABASE_URL` uses `postgresql://`. Add a custom variable that replaces the scheme:
> `LIGHTLAYER_DATABASE_URL=postgresql+asyncpg://<rest-from-railway-postgres>`

**Start command:**
```
cd /app && python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2
```

**Health check:** `/api/health`

### 4. Deploy Frontend

Create another service from the same repo.

**Root directory:** `frontend`  
**Builder:** Dockerfile  

**Build args:**
```
VITE_API_URL=/api
```

**Custom domain:** `app.lightlayer.dev`

### 5. Configure Routing

In Railway's service settings for the frontend, set up:
- Custom domain: `app.lightlayer.dev`
- Path routing: `/api/*` → backend service

Or use Railway's internal networking:
- Frontend gets the public domain
- Frontend's nginx proxies `/api` to backend's private URL

### Alternative: Single-Service Deploy

For simplicity, you can combine frontend + backend into one service:

1. Build frontend → copy dist into backend's static files
2. Serve both from FastAPI using `StaticFiles` mount
3. Single Railway service, simpler routing

This is recommended for MVP/demo stage.

## Docker Compose (VPS/Self-hosted)

If deploying to a VPS with Docker:

```bash
# First run — generates .env.prod
DOMAIN=app.lightlayer.dev ./deploy.sh

# Edit .env.prod with secure passwords, then:
DOMAIN=app.lightlayer.dev ./deploy.sh
```

The `docker-compose.prod.yml` includes Caddy for automatic HTTPS.
