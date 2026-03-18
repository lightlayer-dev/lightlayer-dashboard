"""API key authentication."""

from __future__ import annotations

import hashlib
import secrets

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func as sql_func

from app.config import settings
from app.database import get_db
from app.models import ApiKey

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def generate_api_key() -> str:
    """Generate a new API key with the configured prefix."""
    return f"{settings.api_key_prefix}{secrets.token_urlsafe(32)}"


def hash_api_key(key: str) -> str:
    """SHA-256 hash of the API key for storage."""
    return hashlib.sha256(key.encode()).hexdigest()


def key_prefix(key: str) -> str:
    """Extract prefix for identification (first 8 chars)."""
    return key[:8]


async def get_api_key(
    api_key: str | None = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    """Validate API key and return the ApiKey record.

    Raises 401 if key is missing/invalid/inactive.
    """
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    key_hash = hash_api_key(api_key)
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active.is_(True))
    )
    db_key = result.scalar_one_or_none()

    if not db_key:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")

    # Update last_used_at
    await db.execute(
        update(ApiKey).where(ApiKey.id == db_key.id).values(last_used_at=sql_func.now())
    )
    await db.commit()

    return db_key
