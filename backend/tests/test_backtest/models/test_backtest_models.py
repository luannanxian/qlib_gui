"""
Backtest Models Tests

TDD tests for Backtest database models (BacktestConfig, BacktestResult).
Following strict TDD methodology: Write tests first (RED phase).
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.backtest import (
    BacktestConfig,
    BacktestResult,
    BacktestStatus
)


class TestBacktestConfigModel:
    """Test suite for BacktestConfig model"""

    @pytest.mark.asyncio
    async def test_create_backtest_config(self, db_session: AsyncSession):
        """Test creating a backtest configuration"""
        # Arrange
        config_data = BacktestConfig(
            strategy_id="strategy_123",
            dataset_id="dataset_456",
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31),
            initial_capital=Decimal("1000000.00"),
            commission_rate=Decimal("0.001"),
            slippage=Decimal("0.0005"),
            config_params={
                "benchmark": "SH000300",
                "freq": "day",
                "trade_unit": "100"
            }
        )

        # Act
        db_session.add(config_data)
        await db_session.commit()
        await db_session.refresh(config_data)

        # Assert
        assert config_data.id is not None
        assert config_data.strategy_id == "strategy_123"
        assert config_data.dataset_id == "dataset_456"
        assert config_data.start_date == date(2020, 1, 1)
        assert config_data.end_date == date(2023, 12, 31)
        assert config_data.initial_capital == Decimal("1000000.00")
        assert config_data.commission_rate == Decimal("0.001")
        assert config_data.slippage == Decimal("0.0005")
        assert config_data.config_params["benchmark"] == "SH000300"
        assert config_data.created_at is not None
        assert config_data.is_deleted is False

    @pytest.mark.asyncio
    async def test_backtest_config_validation(self, db_session: AsyncSession):
        """Test backtest configuration validation rules"""
        # Test 1: Valid date range
        valid_config = BacktestConfig(
            strategy_id="strategy_123",
            dataset_id="dataset_456",
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31),
            initial_capital=Decimal("1000000.00"),
            commission_rate=Decimal("0.001"),
            slippage=Decimal("0.0005")
        )
        db_session.add(valid_config)
        await db_session.commit()
        assert valid_config.id is not None

        # Test 2: Positive initial capital
        assert valid_config.initial_capital > 0

        # Test 3: Valid commission rate (0-1)
        assert 0 <= valid_config.commission_rate <= 1

        # Test 4: Valid slippage (0-1)
        assert 0 <= valid_config.slippage <= 1

    @pytest.mark.asyncio
    async def test_backtest_config_relationships(self, db_session: AsyncSession):
        """Test backtest configuration relationships with other models"""
        # Arrange - Create config
        config = BacktestConfig(
            strategy_id="strategy_789",
            dataset_id="dataset_101",
            start_date=date(2021, 1, 1),
            end_date=date(2022, 12, 31),
            initial_capital=Decimal("500000.00"),
            commission_rate=Decimal("0.0015"),
            slippage=Decimal("0.001")
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # Act - Create result linked to config
        result = BacktestResult(
            config_id=config.id,
            status=BacktestStatus.COMPLETED.value,
            total_return=Decimal("0.25"),
            annual_return=Decimal("0.12"),
            sharpe_ratio=Decimal("1.5"),
            max_drawdown=Decimal("0.15"),
            win_rate=Decimal("0.55")
        )
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)

        # Assert - Verify relationship
        assert result.config_id == config.id
        assert result.id is not None

    @pytest.mark.asyncio
    async def test_backtest_config_default_values(self, db_session: AsyncSession):
        """Test default values for backtest configuration"""
        # Arrange & Act
        config = BacktestConfig(
            strategy_id="strategy_default",
            dataset_id="dataset_default",
            start_date=date(2020, 1, 1),
            end_date=date(2020, 12, 31),
            initial_capital=Decimal("1000000.00"),
            commission_rate=Decimal("0.001"),
            slippage=Decimal("0.0005")
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # Assert - Check default values from BaseDBModel
        assert config.is_deleted is False
        assert config.deleted_at is None
        assert config.created_at is not None
        assert config.updated_at is not None
        assert isinstance(config.id, str)
        assert len(config.id) > 0


class TestBacktestResultModel:
    """Test suite for BacktestResult model"""

    @pytest.mark.asyncio
    async def test_create_backtest_result(self, db_session: AsyncSession):
        """Test creating a backtest result"""
        # Arrange - First create a config
        config = BacktestConfig(
            strategy_id="strategy_result_test",
            dataset_id="dataset_result_test",
            start_date=date(2020, 1, 1),
            end_date=date(2020, 12, 31),
            initial_capital=Decimal("1000000.00"),
            commission_rate=Decimal("0.001"),
            slippage=Decimal("0.0005")
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # Act - Create result
        result = BacktestResult(
            config_id=config.id,
            status=BacktestStatus.COMPLETED.value,
            total_return=Decimal("0.35"),
            annual_return=Decimal("0.15"),
            sharpe_ratio=Decimal("2.1"),
            max_drawdown=Decimal("0.12"),
            win_rate=Decimal("0.60"),
            metrics={
                "volatility": 0.18,
                "sortino_ratio": 2.5,
                "calmar_ratio": 1.25
            },
            trades={
                "total_trades": 150,
                "winning_trades": 90,
                "losing_trades": 60
            }
        )
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)

        # Assert
        assert result.id is not None
        assert result.config_id == config.id
        assert result.status == BacktestStatus.COMPLETED.value
        assert result.total_return == Decimal("0.35")
        assert result.annual_return == Decimal("0.15")
        assert result.sharpe_ratio == Decimal("2.1")
        assert result.max_drawdown == Decimal("0.12")
        assert result.win_rate == Decimal("0.60")
        assert result.metrics["volatility"] == 0.18
        assert result.trades["total_trades"] == 150
        assert result.created_at is not None

    @pytest.mark.asyncio
    async def test_backtest_result_metrics(self, db_session: AsyncSession):
        """Test backtest result metrics calculation and storage"""
        # Arrange - Create config
        config = BacktestConfig(
            strategy_id="strategy_metrics",
            dataset_id="dataset_metrics",
            start_date=date(2021, 1, 1),
            end_date=date(2021, 12, 31),
            initial_capital=Decimal("1000000.00"),
            commission_rate=Decimal("0.001"),
            slippage=Decimal("0.0005")
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # Act - Create result with comprehensive metrics
        result = BacktestResult(
            config_id=config.id,
            status=BacktestStatus.COMPLETED.value,
            total_return=Decimal("0.45"),
            annual_return=Decimal("0.18"),
            sharpe_ratio=Decimal("1.8"),
            max_drawdown=Decimal("0.20"),
            win_rate=Decimal("0.58"),
            metrics={
                "volatility": 0.22,
                "sortino_ratio": 2.2,
                "calmar_ratio": 0.9,
                "information_ratio": 1.5,
                "alpha": 0.05,
                "beta": 1.1,
                "tracking_error": 0.08
            },
            trades={
                "total_trades": 200,
                "winning_trades": 116,
                "losing_trades": 84,
                "avg_win": 5000,
                "avg_loss": -3000,
                "largest_win": 25000,
                "largest_loss": -15000,
                "avg_holding_period": 5.5
            }
        )
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)

        # Assert - Verify all metrics are stored correctly
        assert result.metrics["volatility"] == 0.22
        assert result.metrics["sortino_ratio"] == 2.2
        assert result.metrics["alpha"] == 0.05
        assert result.trades["total_trades"] == 200
        assert result.trades["avg_win"] == 5000
        assert result.trades["avg_holding_period"] == 5.5

    @pytest.mark.asyncio
    async def test_backtest_status_transitions(self, db_session: AsyncSession):
        """Test backtest status state transitions"""
        # Arrange - Create config
        config = BacktestConfig(
            strategy_id="strategy_status",
            dataset_id="dataset_status",
            start_date=date(2022, 1, 1),
            end_date=date(2022, 12, 31),
            initial_capital=Decimal("1000000.00"),
            commission_rate=Decimal("0.001"),
            slippage=Decimal("0.0005")
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # Test 1: PENDING -> RUNNING
        result = BacktestResult(
            config_id=config.id,
            status=BacktestStatus.PENDING.value,
            total_return=Decimal("0.0"),
            annual_return=Decimal("0.0"),
            sharpe_ratio=Decimal("0.0"),
            max_drawdown=Decimal("0.0"),
            win_rate=Decimal("0.0")
        )
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)
        assert result.status == BacktestStatus.PENDING.value

        # Test 2: Update to RUNNING
        result.status = BacktestStatus.RUNNING.value
        await db_session.commit()
        await db_session.refresh(result)
        assert result.status == BacktestStatus.RUNNING.value

        # Test 3: Update to COMPLETED
        result.status = BacktestStatus.COMPLETED.value
        result.total_return = Decimal("0.25")
        result.annual_return = Decimal("0.12")
        result.sharpe_ratio = Decimal("1.5")
        await db_session.commit()
        await db_session.refresh(result)
        assert result.status == BacktestStatus.COMPLETED.value

        # Test 4: Verify all status values are valid
        valid_statuses = [
            BacktestStatus.PENDING.value,
            BacktestStatus.RUNNING.value,
            BacktestStatus.COMPLETED.value,
            BacktestStatus.FAILED.value,
            BacktestStatus.CANCELLED.value
        ]
        assert result.status in valid_statuses

    @pytest.mark.asyncio
    async def test_backtest_result_failed_status(self, db_session: AsyncSession):
        """Test backtest result with FAILED status"""
        # Arrange - Create config
        config = BacktestConfig(
            strategy_id="strategy_failed",
            dataset_id="dataset_failed",
            start_date=date(2022, 1, 1),
            end_date=date(2022, 12, 31),
            initial_capital=Decimal("1000000.00"),
            commission_rate=Decimal("0.001"),
            slippage=Decimal("0.0005")
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        # Act - Create failed result
        result = BacktestResult(
            config_id=config.id,
            status=BacktestStatus.FAILED.value,
            total_return=Decimal("0.0"),
            annual_return=Decimal("0.0"),
            sharpe_ratio=Decimal("0.0"),
            max_drawdown=Decimal("0.0"),
            win_rate=Decimal("0.0"),
            metrics={"error": "Insufficient data for backtest"}
        )
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)

        # Assert
        assert result.status == BacktestStatus.FAILED.value
        assert result.metrics["error"] == "Insufficient data for backtest"


class TestBacktestSoftDelete:
    """Test suite for soft delete functionality"""

    @pytest.mark.asyncio
    async def test_backtest_config_soft_delete(self, db_session: AsyncSession):
        """Test soft deleting a backtest configuration"""
        # Arrange - Create config
        config = BacktestConfig(
            strategy_id="strategy_delete",
            dataset_id="dataset_delete",
            start_date=date(2020, 1, 1),
            end_date=date(2020, 12, 31),
            initial_capital=Decimal("1000000.00"),
            commission_rate=Decimal("0.001"),
            slippage=Decimal("0.0005")
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)
        config_id = config.id

        # Act - Soft delete
        config.is_deleted = True
        config.deleted_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(config)

        # Assert
        assert config.is_deleted is True
        assert config.deleted_at is not None
        assert config.id == config_id

    @pytest.mark.asyncio
    async def test_backtest_result_soft_delete(self, db_session: AsyncSession):
        """Test soft deleting a backtest result"""
        # Arrange - Create config and result
        config = BacktestConfig(
            strategy_id="strategy_delete_result",
            dataset_id="dataset_delete_result",
            start_date=date(2020, 1, 1),
            end_date=date(2020, 12, 31),
            initial_capital=Decimal("1000000.00"),
            commission_rate=Decimal("0.001"),
            slippage=Decimal("0.0005")
        )
        db_session.add(config)
        await db_session.commit()
        await db_session.refresh(config)

        result = BacktestResult(
            config_id=config.id,
            status=BacktestStatus.COMPLETED.value,
            total_return=Decimal("0.25"),
            annual_return=Decimal("0.12"),
            sharpe_ratio=Decimal("1.5"),
            max_drawdown=Decimal("0.15"),
            win_rate=Decimal("0.55")
        )
        db_session.add(result)
        await db_session.commit()
        await db_session.refresh(result)
        result_id = result.id

        # Act - Soft delete
        result.is_deleted = True
        result.deleted_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(result)

        # Assert
        assert result.is_deleted is True
        assert result.deleted_at is not None
        assert result.id == result_id


class TestBacktestStatusEnum:
    """Test suite for BacktestStatus enum"""

    def test_backtest_status_values(self):
        """Test BacktestStatus enum values"""
        # Assert all status values exist
        assert BacktestStatus.PENDING.value == "PENDING"
        assert BacktestStatus.RUNNING.value == "RUNNING"
        assert BacktestStatus.COMPLETED.value == "COMPLETED"
        assert BacktestStatus.FAILED.value == "FAILED"
        assert BacktestStatus.CANCELLED.value == "CANCELLED"

    def test_backtest_status_enum_members(self):
        """Test BacktestStatus enum has all expected members"""
        # Assert
        status_values = [status.value for status in BacktestStatus]
        assert "PENDING" in status_values
        assert "RUNNING" in status_values
        assert "COMPLETED" in status_values
        assert "FAILED" in status_values
        assert "CANCELLED" in status_values
        assert len(status_values) == 5
