"""Fixtures for backtest integration tests."""

# Import fixtures directly from API tests
from tests.test_backtest.api.conftest import async_client  # noqa: F401
from tests.test_backtest.repositories.conftest import db_session, test_engine  # noqa: F401
