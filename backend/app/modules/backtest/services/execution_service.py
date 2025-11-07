"""
Backtest Execution Service.

Manages backtest execution lifecycle including:
- Starting backtest execution
- Status tracking and updates
- Result storage
- Error handling
"""

from typing import Dict, Any
from decimal import Decimal

from app.database.repositories.backtest_repository import BacktestRepository
from app.database.models.backtest import BacktestResult, BacktestStatus
from app.modules.backtest.exceptions import (
    BacktestExecutionError,
    ResourceNotFoundError
)


class BacktestExecutionService:
    """Service for managing backtest execution."""

    def __init__(self, repository: BacktestRepository):
        """
        Initialize service with repository.

        Args:
            repository: BacktestRepository instance
        """
        self.repository = repository

    async def start_backtest(self, config_id: str) -> BacktestResult:
        """
        Start a backtest execution.

        Args:
            config_id: Configuration ID

        Returns:
            Created BacktestResult instance with PENDING status

        Raises:
            ResourceNotFoundError: If configuration not found
        """
        # Verify config exists
        config = await self.repository.get_config_by_id(config_id)
        if not config:
            raise ResourceNotFoundError(f"Configuration {config_id} not found")

        # Create result record with PENDING status
        result_data = {
            "config_id": config_id,
            "status": BacktestStatus.PENDING.value,
            "total_return": Decimal("0.0"),
            "annual_return": Decimal("0.0"),
            "sharpe_ratio": Decimal("0.0"),
            "max_drawdown": Decimal("0.0"),
            "win_rate": Decimal("0.0")
        }

        return await self.repository.create_result(result_data)

    async def get_backtest_status(self, result_id: str) -> str:
        """
        Get the current status of a backtest.

        Args:
            result_id: Result ID

        Returns:
            Current status string

        Raises:
            ResourceNotFoundError: If result not found
        """
        result = await self.repository.get_result_by_id(result_id)
        if not result:
            raise ResourceNotFoundError(f"Backtest result {result_id} not found")

        return result.status

    async def update_status(
        self,
        result_id: str,
        status: str
    ) -> BacktestResult:
        """
        Update the status of a backtest.

        Args:
            result_id: Result ID
            status: New status value

        Returns:
            Updated BacktestResult instance

        Raises:
            ResourceNotFoundError: If result not found
        """
        result = await self.repository.update_result_status(result_id, status)
        if not result:
            raise ResourceNotFoundError(f"Backtest result {result_id} not found")

        return result

    async def complete_backtest(
        self,
        result_id: str,
        metrics: Dict[str, Any]
    ) -> BacktestResult:
        """
        Complete a backtest and store results.

        Args:
            result_id: Result ID
            metrics: Dictionary containing performance metrics

        Returns:
            Updated BacktestResult instance

        Raises:
            ResourceNotFoundError: If result not found
        """
        # Update status and metrics
        update_data = {
            "status": BacktestStatus.COMPLETED.value,
            "total_return": metrics.get("total_return", Decimal("0.0")),
            "annual_return": metrics.get("annual_return", Decimal("0.0")),
            "sharpe_ratio": metrics.get("sharpe_ratio", Decimal("0.0")),
            "max_drawdown": metrics.get("max_drawdown", Decimal("0.0")),
            "win_rate": metrics.get("win_rate", Decimal("0.0")),
            "metrics": metrics.get("metrics"),
            "trades": metrics.get("trades")
        }

        result = await self.repository.update_result(result_id, update_data)
        if not result:
            raise ResourceNotFoundError(f"Backtest result {result_id} not found")

        return result

    async def fail_backtest(
        self,
        result_id: str,
        error_message: str
    ) -> BacktestResult:
        """
        Mark a backtest as failed with error message.

        Args:
            result_id: Result ID
            error_message: Error description

        Returns:
            Updated BacktestResult instance

        Raises:
            ResourceNotFoundError: If result not found
        """
        update_data = {
            "status": BacktestStatus.FAILED.value,
            "metrics": {"error": error_message}
        }

        result = await self.repository.update_result(result_id, update_data)
        if not result:
            raise ResourceNotFoundError(f"Backtest result {result_id} not found")

        return result
