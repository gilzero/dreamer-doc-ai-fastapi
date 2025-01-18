# tests/conftest.py

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel
from httpx import AsyncClient
import redis.asyncio as aioredis
from unittest.mock import Mock

from app.main import app
from app.core.config import get_settings
from app.db.session import engine
from app.services.cache import CacheService
from app.services.stripe_service import StripeService

settings = get_settings()

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    """Setup test database."""
    # Create tables
    SQLModel.metadata.create_all(engine)
    yield
    # Clean up
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[Session, None]:
    """Get database session for tests."""
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Get async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture(scope="function")
def sync_client() -> Generator[TestClient, None, None]:
    """Get sync test client."""
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="function")
async def redis():
    """Get test Redis connection."""
    redis = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True
    )
    try:
        yield redis
    finally:
        await redis.flushdb()
        await redis.close()

@pytest.fixture(scope="function")
def mock_stripe():
    """Mock Stripe service."""
    mock = Mock(spec=StripeService)
    mock.create_payment_intent.return_value = {
        "id": "pi_test",
        "client_secret": "test_secret",
        "amount": 1000,
        "currency": "cny"
    }
    return mock