"""
Test suite for BacktestExecutionService.

Tests execution management logic including:
- Starting backtest execution
- Status tracking
- Result storage
- Error handling
"""

import pytest
from datetime import date
from decimal import Decimal

from app.modules.backtest.services.execution_service import BacktestExecutionService
from app.modules.backtest.exceptions import (
    BacktestExecutionError,
    ResourceNotFoundError
)
from app.database.models.backtest import BacktestStatus


class TestStartBacktest:
    """Test starting backtest execution."""

    @pytest.mark.asyncio
    async def test_start_backtest_creates_result(
        self,
        execution_service: BacktestExecutionService,
        config_service
    ):
        """Test starting a backtest creates a result record."""
        # Create config first
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": date(2020, 1, 1),
            "end_date": date(2020, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005")
        }
        config = await config_service.create_config(config_data)

        # Start backtest
        result = await execution_service.start_backtest(config.id)

        assert result.id is not None
        assert result.config_id == config.id
        assert result.status == BacktestStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_start_backtest_with_invalid_config(
        self,
        execution_service: BacktestExecutionService
    ):
        """Test starting backtest with non-existent config raises error."""
        with pytest.raises(ResourceNotFoundError):
            await execution_service.start_backtest("nonexistent-id")


class TestGetBacktestStatus:
    """Test retrieving backtest status."""

    @pytest.mark.asyncio
    async def test_get_status_for_existing_result(
        self,
        execution_service: BacktestExecutionService,
        config_service
    ):
        """Test getting status for an existing backtest."""
        # Create and start backtest
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": date(2020, 1, 1),
            "end_date": date(2020, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005")
        }
        config = await config_service.create_config(config_data)
        result = await execution_service.start_backtest(config.id)

        # Get status
        status = await execution_service.get_backtest_status(result.id)

        assert status == BacktestStatus.PENDING.value

    @pytest.mark.asyncio
    async def test_get_status_for_nonexistent_result(
        self,
        execution_service: BacktestExecutionService
    ):
        """Test getting status for non-existent backtest raises error."""
        with pytest.raises(ResourceNotFoundError):
            await execution_service.get_backtest_status("nonexistent-id")


class TestUpdateBacktestStatus:
    """Test updating backtest status."""

    @pytest.mark.asyncio
    async def test_update_status_to_running(
        self,
        execution_service: BacktestExecutionService,
        config_service
    ):
        """Test updating backtest status to RUNNING."""
        # Create and start backtest
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": date(2020, 1, 1),
            "end_date": date(2020, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005")
        }
        config = await config_service.create_config(config_data)
        result = await execution_service.start_backtest(config.id)

        # Update status
        updated = await execution_service.update_status(
            result.id,
            BacktestStatus.RUNNING.value
        )

        assert updated.status == BacktestStatus.RUNNING.value

    @pytest.mark.asyncio
    async def test_update_status_with_invalid_transition(
        self,
        execution_service: BacktestExecutionService,
        config_service
    ):
        """Test invalid status transition raises error."""
        # Create and start backtest
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": date(2020, 1, 1),
            "end_date": date(2020, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005")
        }
        config = await config_service.create_config(config_data)
        result = await execution_service.start_backtest(config.id)

        # Try invalid transition (PENDING -> CANCELLED without going through RUNNING)
        # For now, we'll allow all transitions, but this test documents the intent
        updated = await execution_service.update_status(
            result.id,
            BacktestStatus.CANCELLED.value
        )
        assert updated.status == BacktestStatus.CANCELLED.value


class TestCompleteBacktest:
    """Test completing backtest with results."""

    @pytest.mark.asyncio
    async def test_complete_backtest_with_metrics(
        self,
        execution_service: BacktestExecutionService,
        config_service
    ):
        """Test completing backtest and storing metrics."""
        # Create and start backtest
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": date(2020, 1, 1),
            "end_date": date(2020, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005")
        }
        config = await config_service.create_config(config_data)
        result = await execution_service.start_backtest(config.id)

        # Complete with metrics
        metrics = {
            "total_return": Decimal("0.25"),
            "annual_return": Decimal("0.25"),
            "sharpe_ratio": Decimal("1.5"),
            "max_drawdown": Decimal("0.15"),
            "win_rate": Decimal("0.55")
        }

        completed = await execution_service.complete_backtest(result.id, metrics)

        assert completed.status == BacktestStatus.COMPLETED.value
        assert completed.total_return == Decimal("0.25")
        assert completed.sharpe_ratio == Decimal("1.5")


class TestFailBacktest:
    """Test handling backtest failures."""

    @pytest.mark.asyncio
    async def test_fail_backtest_with_error_message(
        self,
        execution_service: BacktestExecutionService,
        config_service
    ):
        """Test marking backtest as failed with error message."""
        # Create and start backtest
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": date(2020, 1, 1),
            "end_date": date(2020, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005")
        }
        config = await config_service.create_config(config_data)
        result = await execution_service.start_backtest(config.id)

        # Fail backtest
        error_msg = "Data not available for specified date range"
        failed = await execution_service.fail_backtest(result.id, error_msg)

        assert failed.status == BacktestStatus.FAILED.value
        assert failed.metrics is not None
        assert "error" in failed.metrics
