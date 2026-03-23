# Single-service Dockerfile — builds frontend, serves everything from FastAPI
# Ideal for Railway / single-container deploys

# ── Stage 1: Build frontend ────────────────────────────────────────────
FROM node:22-slim AS frontend-build

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# ── Stage 2: Python backend + static frontend ──────────────────────────
FROM python:3.11-slim

WORKDIR /app

# System deps for asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev git && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy backend code
COPY backend/ .

# Copy built frontend into /app/static
COPY --from=frontend-build /app/dist /app/static

EXPOSE 8000

CMD ["sh", "-c", "python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
