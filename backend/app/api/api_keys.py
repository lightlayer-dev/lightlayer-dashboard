"""API key management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import generate_api_key, hash_api_key, key_prefix
from app.database import get_db
from app.models import ApiKey

router = APIRouter(prefix="/api/keys", tags=["api-keys"])


class CreateKeyRequest(BaseModel):
    name: str


class CreateKeyResponse(BaseModel):
    """Returned only on creation — the raw key is shown once."""
    id: int
    name: str
    key_prefix: str
    key: str  # Full key, shown only once


class KeyInfo(BaseModel):
    id: int
    name: str
    key_prefix: str
    is_active: bool
    created_at: str
    last_used_at: str | None

    model_config = {"from_attributes": True}


@router.post("/", response_model=CreateKeyResponse, status_code=201)
async def create_api_key(body: CreateKeyRequest, db: AsyncSession = Depends(get_db)):
    """Create a new API key. The full key is returned ONCE."""
    raw_key = generate_api_key()

    db_key = ApiKey(
        key_hash=hash_api_key(raw_key),
        key_prefix=key_prefix(raw_key),
        name=body.name,
    )
    db.add(db_key)
    await db.commit()
    await db.refresh(db_key)

    return CreateKeyResponse(
        id=db_key.id,
        name=db_key.name,
        key_prefix=db_key.key_prefix,
        key=raw_key,
    )


@router.get("/", response_model=list[KeyInfo])
async def list_api_keys(db: AsyncSession = Depends(get_db)):
    """List all API keys (without the raw key)."""
    result = await db.execute(select(ApiKey).order_by(ApiKey.created_at.desc()))
    keys = result.scalars().all()
    return [
        KeyInfo(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            is_active=k.is_active,
            created_at=k.created_at.isoformat(),
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
        )
        for k in keys
    ]


@router.delete("/{key_id}", status_code=204)
async def revoke_api_key(key_id: int, db: AsyncSession = Depends(get_db)):
    """Revoke (soft-delete) an API key."""
    result = await db.execute(select(ApiKey).where(ApiKey.id == key_id))
    db_key = result.scalar_one_or_none()
    if not db_key:
        raise HTTPException(status_code=404, detail="API key not found")

    db_key.is_active = False
    await db.commit()
