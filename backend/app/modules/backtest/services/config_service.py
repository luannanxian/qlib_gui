"""
Backtest Configuration Service.

Manages backtest configuration lifecycle including:
- Configuration creation with validation
- Date range validation
- Capital constraints validation
- Configuration updates and deletion
"""

from datetime import date
from decimal import Decimal
from typing import Dict, Any, Optional

from app.database.repositories.backtest_repository import BacktestRepository
from app.database.models.backtest import BacktestConfig
from app.modules.backtest.exceptions import (
    InvalidConfigError,
    InvalidDateRangeError,
    InvalidCapitalError,
    ResourceNotFoundError
)


class BacktestConfigService:
    """Service for managing backtest configurations."""

    # Validation constants
    MIN_CAPITAL = Decimal("1000.00")  # Minimum initial capital
    MIN_DATE_RANGE_DAYS = 1  # Minimum backtest duration

    def __init__(self, repository: BacktestRepository):
        """
        Initialize service with repository.

        Args:
            repository: BacktestRepository instance
        """
        self.repository = repository

    async def create_config(self, config_data: Dict[str, Any]) -> BacktestConfig:
        """
        Create a new backtest configuration with validation.

        Args:
            config_data: Configuration parameters

        Returns:
            Created BacktestConfig instance

        Raises:
            InvalidConfigError: If configuration parameters are invalid
            InvalidDateRangeError: If date range is invalid
            InvalidCapitalError: If capital constraints are violated
        """
        # Validate all parameters
        self._validate_required_fields(config_data)
        self._validate_references(config_data)
        self._validate_date_range(
            config_data.get("start_date"),
            config_data.get("end_date")
        )
        self._validate_capital(config_data.get("initial_capital"))
        self._validate_rates(config_data)

        # Create configuration
        return await self.repository.create_config(config_data)

    async def get_config_by_id(self, config_id: str) -> BacktestConfig:
        """
        Retrieve a configuration by ID.

        Args:
            config_id: Configuration ID

        Returns:
            BacktestConfig instance

        Raises:
            ResourceNotFoundError: If configuration not found
        """
        config = await self.repository.get_config_by_id(config_id)
        if not config:
            raise ResourceNotFoundError(f"Configuration {config_id} not found")
        return config

    async def update_config(
        self,
        config_id: str,
        update_data: Dict[str, Any]
    ) -> BacktestConfig:
        """
        Update a configuration with validation.

        Args:
            config_id: Configuration ID
            update_data: Fields to update

        Returns:
            Updated BacktestConfig instance

        Raises:
            ResourceNotFoundError: If configuration not found
            InvalidConfigError: If update data is invalid
        """
        # Check if config exists
        config = await self.get_config_by_id(config_id)

        # Validate update data
        if "start_date" in update_data or "end_date" in update_data:
            start_date = update_data.get("start_date", config.start_date)
            end_date = update_data.get("end_date", config.end_date)
            self._validate_date_range(start_date, end_date)

        if "initial_capital" in update_data:
            self._validate_capital(update_data["initial_capital"])

        if "commission_rate" in update_data or "slippage" in update_data:
            rates_data = {
                "commission_rate": update_data.get("commission_rate", config.commission_rate),
                "slippage": update_data.get("slippage", config.slippage)
            }
            self._validate_rates(rates_data)

        # Update configuration
        updated_config = await self.repository.update_config(config_id, update_data)
        if not updated_config:
            raise ResourceNotFoundError(f"Configuration {config_id} not found")

        return updated_config

    async def delete_config(self, config_id: str) -> bool:
        """
        Delete a configuration (soft delete).

        Args:
            config_id: Configuration ID

        Returns:
            True if deleted successfully

        Raises:
            ResourceNotFoundError: If configuration not found
        """
        result = await self.repository.delete_config(config_id)
        if not result:
            raise ResourceNotFoundError(f"Configuration {config_id} not found")
        return result

    # ==================== Validation Methods ====================

    def _validate_required_fields(self, config_data: Dict[str, Any]) -> None:
        """Validate that all required fields are present."""
        required_fields = [
            "strategy_id", "dataset_id", "start_date", "end_date",
            "initial_capital", "commission_rate", "slippage"
        ]

        for field in required_fields:
            if field not in config_data:
                raise InvalidConfigError(f"Missing required field: {field}")

    def _validate_references(self, config_data: Dict[str, Any]) -> None:
        """Validate strategy_id and dataset_id are not empty."""
        strategy_id = config_data.get("strategy_id", "")
        dataset_id = config_data.get("dataset_id", "")

        if not strategy_id or not strategy_id.strip():
            raise InvalidConfigError("strategy_id cannot be empty")

        if not dataset_id or not dataset_id.strip():
            raise InvalidConfigError("dataset_id cannot be empty")

    def _validate_date_range(self, start_date: date, end_date: date) -> None:
        """
        Validate date range constraints.

        Args:
            start_date: Backtest start date
            end_date: Backtest end date

        Raises:
            InvalidDateRangeError: If date range is invalid
        """
        # Check start_date is before end_date
        if start_date > end_date:
            raise InvalidDateRangeError(
                f"start_date ({start_date}) must be before end_date ({end_date})"
            )

        # Check minimum duration
        duration = (end_date - start_date).days
        if duration < self.MIN_DATE_RANGE_DAYS:
            raise InvalidDateRangeError(
                f"Date range must be at least {self.MIN_DATE_RANGE_DAYS} day(s)"
            )

        # Check end_date is not in the future
        if end_date > date.today():
            raise InvalidDateRangeError(
                f"end_date ({end_date}) cannot be in the future"
            )

    def _validate_capital(self, initial_capital: Decimal) -> None:
        """
        Validate capital constraints.

        Args:
            initial_capital: Initial capital amount

        Raises:
            InvalidCapitalError: If capital constraints are violated
        """
        if initial_capital <= 0:
            raise InvalidCapitalError("initial_capital must be positive")

        if initial_capital < self.MIN_CAPITAL:
            raise InvalidCapitalError(
                f"initial_capital must be at least {self.MIN_CAPITAL} (minimum requirement)"
            )

    def _validate_rates(self, config_data: Dict[str, Any]) -> None:
        """
        Validate commission_rate and slippage are within valid ranges.

        Args:
            config_data: Configuration data containing rates

        Raises:
            InvalidConfigError: If rates are out of valid range
        """
        commission_rate = config_data.get("commission_rate")
        slippage = config_data.get("slippage")

        if commission_rate is not None:
            if commission_rate < 0 or commission_rate > 1:
                raise InvalidConfigError(
                    f"commission_rate must be between 0 and 1, got {commission_rate}"
                )

        if slippage is not None:
            if slippage < 0 or slippage > 1:
                raise InvalidConfigError(
                    f"slippage must be between 0 and 1, got {slippage}"
                )
