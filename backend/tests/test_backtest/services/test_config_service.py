"""
Test suite for BacktestConfigService.

Tests configuration management logic including:
- Configuration creation and validation
- Date range validation
- Capital constraints validation
- Strategy and dataset validation
- Configuration updates and deletion
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from app.modules.backtest.services.config_service import BacktestConfigService
from app.modules.backtest.exceptions import (
    InvalidConfigError,
    InvalidDateRangeError,
    InvalidCapitalError,
    ResourceNotFoundError
)


class TestCreateBacktestConfig:
    """Test backtest configuration creation."""

    @pytest.mark.asyncio
    async def test_create_valid_config(self, config_service: BacktestConfigService):
        """Test creating a valid backtest configuration."""
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": date(2020, 1, 1),
            "end_date": date(2021, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005"),
            "config_params": {"benchmark": "SH000300"}
        }

        config = await config_service.create_config(config_data)

        assert config.id is not None
        assert config.strategy_id == "strategy-123"
        assert config.dataset_id == "dataset-456"
        assert config.initial_capital == Decimal("1000000.00")

    @pytest.mark.asyncio
    async def test_create_config_with_minimal_params(self, config_service: BacktestConfigService):
        """Test creating config with minimal required parameters."""
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": date(2020, 1, 1),
            "end_date": date(2021, 12, 31),
            "initial_capital": Decimal("100000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005")
        }

        config = await config_service.create_config(config_data)

        assert config.id is not None
        assert config.config_params is None


class TestValidateConfigParams:
    """Test configuration parameter validation."""

    @pytest.mark.asyncio
    async def test_validate_commission_rate_range(self, config_service: BacktestConfigService):
        """Test commission rate must be between 0 and 1."""
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": date(2020, 1, 1),
            "end_date": date(2021, 12, 31),
            "initial_capital": Decimal("100000.00"),
            "commission_rate": Decimal("1.5"),  # Invalid: > 1
            "slippage": Decimal("0.0005")
        }

        with pytest.raises(InvalidConfigError, match="commission_rate"):
            await config_service.create_config(config_data)

    @pytest.mark.asyncio
    async def test_validate_slippage_range(self, config_service: BacktestConfigService):
        """Test slippage must be between 0 and 1."""
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": date(2020, 1, 1),
            "end_date": date(2021, 12, 31),
            "initial_capital": Decimal("100000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("-0.1")  # Invalid: < 0
        }

        with pytest.raises(InvalidConfigError, match="slippage"):
            await config_service.create_config(config_data)


class TestValidateDateRange:
    """Test date range validation."""

    @pytest.mark.asyncio
    async def test_validate_start_before_end(self, config_service: BacktestConfigService):
        """Test start_date must be before end_date."""
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": date(2021, 12, 31),
            "end_date": date(2020, 1, 1),  # Invalid: before start_date
            "initial_capital": Decimal("100000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005")
        }

        with pytest.raises(InvalidDateRangeError):
            await config_service.create_config(config_data)

    @pytest.mark.asyncio
    async def test_validate_date_range_not_too_short(self, config_service: BacktestConfigService):
        """Test date range must be at least 1 day."""
        today = date.today()
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": today,
            "end_date": today,  # Same day
            "initial_capital": Decimal("100000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005")
        }

        with pytest.raises(InvalidDateRangeError, match="at least"):
            await config_service.create_config(config_data)

    @pytest.mark.asyncio
    async def test_validate_date_not_in_future(self, config_service: BacktestConfigService):
        """Test end_date cannot be in the future."""
        future_date = date.today() + timedelta(days=365)
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": date(2020, 1, 1),
            "end_date": future_date,
            "initial_capital": Decimal("100000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005")
        }

        with pytest.raises(InvalidDateRangeError, match="future"):
            await config_service.create_config(config_data)


class TestValidateCapitalConstraints:
    """Test capital constraints validation."""

    @pytest.mark.asyncio
    async def test_validate_positive_capital(self, config_service: BacktestConfigService):
        """Test initial_capital must be positive."""
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": date(2020, 1, 1),
            "end_date": date(2021, 12, 31),
            "initial_capital": Decimal("0.00"),  # Invalid: not positive
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005")
        }

        with pytest.raises(InvalidCapitalError):
            await config_service.create_config(config_data)

    @pytest.mark.asyncio
    async def test_validate_capital_minimum(self, config_service: BacktestConfigService):
        """Test initial_capital must meet minimum requirement."""
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": date(2020, 1, 1),
            "end_date": date(2021, 12, 31),
            "initial_capital": Decimal("100.00"),  # Too small
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005")
        }

        with pytest.raises(InvalidCapitalError, match="minimum"):
            await config_service.create_config(config_data)


class TestGetConfigById:
    """Test retrieving configuration by ID."""

    @pytest.mark.asyncio
    async def test_get_existing_config(self, config_service: BacktestConfigService):
        """Test retrieving an existing configuration."""
        # Create config first
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": date(2020, 1, 1),
            "end_date": date(2021, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005")
        }
        created_config = await config_service.create_config(config_data)

        # Retrieve it
        retrieved_config = await config_service.get_config_by_id(created_config.id)

        assert retrieved_config is not None
        assert retrieved_config.id == created_config.id
        assert retrieved_config.strategy_id == "strategy-123"

    @pytest.mark.asyncio
    async def test_get_nonexistent_config(self, config_service: BacktestConfigService):
        """Test retrieving a non-existent configuration raises error."""
        with pytest.raises(ResourceNotFoundError):
            await config_service.get_config_by_id("nonexistent-id")


class TestUpdateConfig:
    """Test configuration updates."""

    @pytest.mark.asyncio
    async def test_update_config_params(self, config_service: BacktestConfigService):
        """Test updating configuration parameters."""
        # Create config
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": date(2020, 1, 1),
            "end_date": date(2021, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005")
        }
        config = await config_service.create_config(config_data)

        # Update it
        update_data = {
            "initial_capital": Decimal("2000000.00"),
            "config_params": {"benchmark": "SH000905"}
        }
        updated_config = await config_service.update_config(config.id, update_data)

        assert updated_config.initial_capital == Decimal("2000000.00")
        assert updated_config.config_params["benchmark"] == "SH000905"

    @pytest.mark.asyncio
    async def test_update_with_invalid_data(self, config_service: BacktestConfigService):
        """Test updating with invalid data raises error."""
        # Create config
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": date(2020, 1, 1),
            "end_date": date(2021, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005")
        }
        config = await config_service.create_config(config_data)

        # Try to update with invalid commission rate
        update_data = {"commission_rate": Decimal("2.0")}

        with pytest.raises(InvalidConfigError):
            await config_service.update_config(config.id, update_data)


class TestDeleteConfig:
    """Test configuration deletion."""

    @pytest.mark.asyncio
    async def test_delete_existing_config(self, config_service: BacktestConfigService):
        """Test deleting an existing configuration."""
        # Create config
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "dataset-456",
            "start_date": date(2020, 1, 1),
            "end_date": date(2021, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005")
        }
        config = await config_service.create_config(config_data)

        # Delete it
        result = await config_service.delete_config(config.id)

        assert result is True

        # Verify it's deleted (soft delete)
        with pytest.raises(ResourceNotFoundError):
            await config_service.get_config_by_id(config.id)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_config(self, config_service: BacktestConfigService):
        """Test deleting a non-existent configuration."""
        with pytest.raises(ResourceNotFoundError):
            await config_service.delete_config("nonexistent-id")


class TestConfigWithInvalidReferences:
    """Test configuration with invalid strategy or dataset references."""

    @pytest.mark.asyncio
    async def test_config_with_empty_strategy_id(self, config_service: BacktestConfigService):
        """Test creating config with empty strategy_id."""
        config_data = {
            "strategy_id": "",  # Invalid: empty
            "dataset_id": "dataset-456",
            "start_date": date(2020, 1, 1),
            "end_date": date(2021, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005")
        }

        with pytest.raises(InvalidConfigError, match="strategy_id"):
            await config_service.create_config(config_data)

    @pytest.mark.asyncio
    async def test_config_with_empty_dataset_id(self, config_service: BacktestConfigService):
        """Test creating config with empty dataset_id."""
        config_data = {
            "strategy_id": "strategy-123",
            "dataset_id": "",  # Invalid: empty
            "start_date": date(2020, 1, 1),
            "end_date": date(2021, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005")
        }

        with pytest.raises(InvalidConfigError, match="dataset_id"):
            await config_service.create_config(config_data)
