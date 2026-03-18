"""Test fixtures — in-memory SQLite via aiosqlite."""

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models import ApiKey, User  # noqa: F401
from app.auth import generate_api_key, hash_api_key, key_prefix
from app.api.users import pwd_context, create_access_token

TEST_DB_URL = "sqlite+aiosqlite://"

engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    from app.api.scan_jobs import set_session_factory
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    set_session_factory(TestSession)
    yield
    set_session_factory(None)
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
async def test_user():
    """Create a test user and return (user_id, auth_headers)."""
    async with TestSession() as session:
        user = User(
            email="test@example.com",
            hashed_password=pwd_context.hash("testpassword123"),
            name="Test User",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        token = create_access_token(user.id)
        return user.id, {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def api_key_raw(test_user):
    """Create a valid API key owned by test_user and return the raw key string."""
    user_id, _ = test_user
    raw = generate_api_key()
    async with TestSession() as session:
        db_key = ApiKey(
            user_id=user_id,
            key_hash=hash_api_key(raw),
            key_prefix=key_prefix(raw),
            name="test-key",
        )
        session.add(db_key)
        await session.commit()
    return raw
