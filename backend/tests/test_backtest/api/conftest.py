"""Fixtures for backtest API tests."""

from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.database import get_db

# Import fixtures directly from parent conftest
from tests.test_backtest.repositories.conftest import db_session, test_engine  # noqa: F401


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing."""
    # Override the get_db dependency to use the shared db_session
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
