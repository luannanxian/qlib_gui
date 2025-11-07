"""
Pytest configuration for Backtest Service tests.

Provides fixtures for testing backtest services.
Inherits db_session and test_engine fixtures from parent conftest.
"""

import sys
from pathlib import Path

# Add parent directory to path to import fixtures
parent_dir = Path(__file__).parent.parent / "repositories"
sys.path.insert(0, str(parent_dir))

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.backtest_repository import BacktestRepository
from app.modules.backtest.services.config_service import BacktestConfigService
from app.modules.backtest.services.execution_service import BacktestExecutionService
from app.modules.backtest.services.analysis_service import ResultsAnalysisService
from app.database.models.backtest import BacktestConfig, BacktestResult
from datetime import date
from decimal import Decimal

# Import fixtures directly from parent conftest
from tests.test_backtest.repositories.conftest import db_session, test_engine  # noqa: F401


@pytest_asyncio.fixture
async def backtest_repository(db_session: AsyncSession) -> BacktestRepository:
    """Create a BacktestRepository instance for testing."""
    return BacktestRepository(db_session)


@pytest_asyncio.fixture
async def config_service(backtest_repository: BacktestRepository) -> BacktestConfigService:
    """Create a BacktestConfigService instance for testing."""
    return BacktestConfigService(backtest_repository)


@pytest_asyncio.fixture
async def execution_service(backtest_repository: BacktestRepository) -> BacktestExecutionService:
    """Create a BacktestExecutionService instance for testing."""
    return BacktestExecutionService(backtest_repository)


@pytest_asyncio.fixture
async def analysis_service(backtest_repository: BacktestRepository) -> ResultsAnalysisService:
    """Create a ResultsAnalysisService instance for testing."""
    return ResultsAnalysisService(backtest_repository)


@pytest_asyncio.fixture
async def diagnostic_service(backtest_repository: BacktestRepository):
    """Create a DiagnosticService instance for testing."""
    from app.modules.backtest.services.diagnostic_service import DiagnosticService
    return DiagnosticService(backtest_repository)


@pytest_asyncio.fixture
async def export_service(backtest_repository: BacktestRepository):
    """Create an ExportService instance for testing."""
    from app.modules.backtest.services.export_service import ExportService
    return ExportService(backtest_repository)


@pytest_asyncio.fixture
async def sample_result_id(backtest_repository: BacktestRepository) -> str:
    """Create a sample backtest result for testing."""
    # Create config with dictionary
    config_data = {
        "strategy_id": "test_strategy",
        "dataset_id": "test_dataset",
        "start_date": date(2023, 1, 1),
        "end_date": date(2023, 12, 31),
        "initial_capital": Decimal("100000.00"),
        "commission_rate": Decimal("0.001"),
        "slippage": Decimal("0.0005")
    }
    config = await backtest_repository.create_config(config_data)

    # Create result with dictionary
    result_data = {
        "config_id": config.id,
        "status": "COMPLETED",
        "total_return": Decimal("0.15"),
        "annual_return": Decimal("0.15"),
        "sharpe_ratio": Decimal("1.5"),
        "max_drawdown": Decimal("0.10"),
        "win_rate": Decimal("0.60")
    }
    result = await backtest_repository.create_result(result_data)
    return result.id
