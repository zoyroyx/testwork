import asyncio
import os
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.db.base import Base
from app.api.deps import get_db
from app.main import app
from httpx import AsyncClient

TEST_DB_FILE = "./test_db.sqlite"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"

# Create async engine for test SQLite database
engine = create_async_engine(TEST_DATABASE_URL, future=True)
TestingSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    # Setup test DB tables (e.g. Base.metadata.create_all equivalent)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # Remove test SQLite file
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except PermissionError:
            pass

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session
        # Ensure we rollback any changes to keep tests isolated
        await session.rollback()

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    # Override get_db dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Handle different versions of httpx
    try:
        from httpx import ASGITransport
        client_kwargs = {"transport": ASGITransport(app=app)}
    except ImportError:
        client_kwargs = {"app": app}

    async with AsyncClient(base_url="http://test", **client_kwargs) as ac:
        yield ac

    app.dependency_overrides.clear()
