import asyncio
import tempfile
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.database.models  # noqa: F401
from app.core.config import Settings
from app.database.base import Base
from app.database.session import get_db
from app.datasets.storage import LocalStorageProvider
from app.main import app

# Isolated in-memory async SQLite engine for tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def init_test_db():
    """Create all tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def temp_storage_dir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture(autouse=True)
def override_storage(temp_storage_dir):
    """Ensure tests run against a clean isolated temporary storage directory."""
    import app.datasets.storage as storage_module

    provider = LocalStorageProvider(base_dir=temp_storage_dir)
    storage_module._storage_instance = provider
    yield provider
    storage_module._storage_instance = None


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client() -> TestClient:
    """Provide a FastAPI TestClient configured with test database dependency overrides."""
    return TestClient(app)


@pytest.fixture
def test_settings() -> Settings:
    """Provide isolated test settings."""
    return Settings(
        app_env="testing",
        app_debug=True,
        jwt_secret="testing-insecure-secret-key-for-test-suite",
        database_url=TEST_DB_URL,
    )
