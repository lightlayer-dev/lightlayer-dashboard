"""Test fixtures — in-memory SQLite via aiosqlite."""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models import ApiKey  # noqa: F401
from app.auth import generate_api_key, hash_api_key, key_prefix

TEST_DB_URL = "sqlite+aiosqlite://"

engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with TestSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def api_key_raw():
    """Create a valid API key and return the raw key string."""
    raw = generate_api_key()
    async with TestSession() as session:
        db_key = ApiKey(
            key_hash=hash_api_key(raw),
            key_prefix=key_prefix(raw),
            name="test-key",
        )
        session.add(db_key)
        await session.commit()
    return raw
