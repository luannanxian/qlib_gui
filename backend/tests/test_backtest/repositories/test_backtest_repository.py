"""
Comprehensive Test Suite for BacktestRepository

This test suite follows TDD principles and covers:
- CRUD operations for BacktestConfig and BacktestResult
- Query operations (by strategy, status, date range)
- Soft delete functionality
- Pagination and filtering
- Edge cases and error handling

Target: 100% test coverage for BacktestRepository
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.backtest import BacktestConfig, BacktestResult, BacktestStatus
from app.database.repositories.backtest_repository import BacktestRepository


class TestBacktestConfigRepository:
    """Test suite for BacktestConfig repository operations"""

    @pytest.mark.asyncio
    async def test_create_backtest_config(self, db_session: AsyncSession):
        """Test creating a backtest configuration"""
        repository = BacktestRepository(db_session)

        config_data = {
            "strategy_id": "strategy_001",
            "dataset_id": "dataset_001",
            "start_date": date(2020, 1, 1),
            "end_date": date(2023, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005"),
            "config_params": {"benchmark": "SH000300", "freq": "day"}
        }

        config = await repository.create_config(config_data)

        assert config.id is not None
        assert config.strategy_id == "strategy_001"
        assert config.dataset_id == "dataset_001"
        assert config.initial_capital == Decimal("1000000.00")
        assert config.config_params["benchmark"] == "SH000300"
        assert config.is_deleted is False

    @pytest.mark.asyncio
    async def test_get_config_by_id(self, db_session: AsyncSession):
        """Test retrieving a backtest configuration by ID"""
        repository = BacktestRepository(db_session)

        # Create a config
        config_data = {
            "strategy_id": "strategy_002",
            "dataset_id": "dataset_002",
            "start_date": date(2021, 1, 1),
            "end_date": date(2023, 12, 31),
            "initial_capital": Decimal("500000.00"),
            "commission_rate": Decimal("0.002"),
            "slippage": Decimal("0.001"),
        }
        created_config = await repository.create_config(config_data)

        # Retrieve it
        retrieved_config = await repository.get_config_by_id(created_config.id)

        assert retrieved_config is not None
        assert retrieved_config.id == created_config.id
        assert retrieved_config.strategy_id == "strategy_002"
        assert retrieved_config.initial_capital == Decimal("500000.00")

    @pytest.mark.asyncio
    async def test_get_config_by_id_not_found(self, db_session: AsyncSession):
        """Test retrieving a non-existent config returns None"""
        repository = BacktestRepository(db_session)

        config = await repository.get_config_by_id("non_existent_id")

        assert config is None

    @pytest.mark.asyncio
    async def test_get_configs_by_strategy(self, db_session: AsyncSession):
        """Test retrieving all configs for a specific strategy"""
        repository = BacktestRepository(db_session)

        # Create multiple configs for the same strategy
        for i in range(3):
            config_data = {
                "strategy_id": "strategy_multi",
                "dataset_id": f"dataset_{i}",
                "start_date": date(2020, 1, 1),
                "end_date": date(2023, 12, 31),
                "initial_capital": Decimal("1000000.00"),
                "commission_rate": Decimal("0.001"),
                "slippage": Decimal("0.0005"),
            }
            await repository.create_config(config_data)

        # Create a config for a different strategy
        other_config_data = {
            "strategy_id": "strategy_other",
            "dataset_id": "dataset_other",
            "start_date": date(2020, 1, 1),
            "end_date": date(2023, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005"),
        }
        await repository.create_config(other_config_data)

        # Retrieve configs for strategy_multi
        configs = await repository.get_configs_by_strategy("strategy_multi")

        assert len(configs) == 3
        assert all(c.strategy_id == "strategy_multi" for c in configs)

    @pytest.mark.asyncio
    async def test_update_config(self, db_session: AsyncSession):
        """Test updating a backtest configuration"""
        repository = BacktestRepository(db_session)

        # Create a config
        config_data = {
            "strategy_id": "strategy_update",
            "dataset_id": "dataset_update",
            "start_date": date(2020, 1, 1),
            "end_date": date(2023, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005"),
        }
        config = await repository.create_config(config_data)

        # Update it
        update_data = {
            "initial_capital": Decimal("2000000.00"),
            "commission_rate": Decimal("0.002"),
            "config_params": {"benchmark": "SH000905"}
        }
        updated_config = await repository.update_config(config.id, update_data)

        assert updated_config.initial_capital == Decimal("2000000.00")
        assert updated_config.commission_rate == Decimal("0.002")
        assert updated_config.config_params["benchmark"] == "SH000905"
        # Original fields should remain unchanged
        assert updated_config.strategy_id == "strategy_update"

    @pytest.mark.asyncio
    async def test_soft_delete_config(self, db_session: AsyncSession):
        """Test soft deleting a backtest configuration"""
        repository = BacktestRepository(db_session)

        # Create a config
        config_data = {
            "strategy_id": "strategy_delete",
            "dataset_id": "dataset_delete",
            "start_date": date(2020, 1, 1),
            "end_date": date(2023, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005"),
        }
        config = await repository.create_config(config_data)

        # Soft delete it
        await repository.delete_config(config.id)

        # Should not be retrievable by normal queries
        retrieved_config = await repository.get_config_by_id(config.id)
        assert retrieved_config is None

        # But should still exist in database with is_deleted=True
        stmt = select(BacktestConfig).where(BacktestConfig.id == config.id)
        result = await db_session.execute(stmt)
        deleted_config = result.scalar_one_or_none()
        assert deleted_config is not None
        assert deleted_config.is_deleted is True


class TestBacktestResultRepository:
    """Test suite for BacktestResult repository operations"""

    @pytest.mark.asyncio
    async def test_create_backtest_result(self, db_session: AsyncSession):
        """Test creating a backtest result"""
        repository = BacktestRepository(db_session)

        # First create a config
        config_data = {
            "strategy_id": "strategy_result",
            "dataset_id": "dataset_result",
            "start_date": date(2020, 1, 1),
            "end_date": date(2023, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005"),
        }
        config = await repository.create_config(config_data)

        # Create a result
        result_data = {
            "config_id": config.id,
            "status": BacktestStatus.COMPLETED.value,
            "total_return": Decimal("0.25"),
            "annual_return": Decimal("0.08"),
            "sharpe_ratio": Decimal("1.5"),
            "max_drawdown": Decimal("0.15"),
            "win_rate": Decimal("0.55"),
            "metrics": {"volatility": 0.12, "sortino": 1.8},
            "trades": {"total_trades": 100, "winning_trades": 55}
        }

        result = await repository.create_result(result_data)

        assert result.id is not None
        assert result.config_id == config.id
        assert result.status == BacktestStatus.COMPLETED.value
        assert result.total_return == Decimal("0.25")
        assert result.sharpe_ratio == Decimal("1.5")
        assert result.metrics["volatility"] == 0.12
        assert result.trades["total_trades"] == 100

    @pytest.mark.asyncio
    async def test_get_result_by_id(self, db_session: AsyncSession):
        """Test retrieving a backtest result by ID"""
        repository = BacktestRepository(db_session)

        # Create config and result
        config_data = {
            "strategy_id": "strategy_get_result",
            "dataset_id": "dataset_get_result",
            "start_date": date(2020, 1, 1),
            "end_date": date(2023, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005"),
        }
        config = await repository.create_config(config_data)

        result_data = {
            "config_id": config.id,
            "status": BacktestStatus.COMPLETED.value,
            "total_return": Decimal("0.30"),
            "annual_return": Decimal("0.10"),
            "sharpe_ratio": Decimal("2.0"),
            "max_drawdown": Decimal("0.10"),
            "win_rate": Decimal("0.60"),
        }
        created_result = await repository.create_result(result_data)

        # Retrieve it
        retrieved_result = await repository.get_result_by_id(created_result.id)

        assert retrieved_result is not None
        assert retrieved_result.id == created_result.id
        assert retrieved_result.total_return == Decimal("0.30")

    @pytest.mark.asyncio
    async def test_get_results_by_config(self, db_session: AsyncSession):
        """Test retrieving all results for a specific config"""
        repository = BacktestRepository(db_session)

        # Create a config
        config_data = {
            "strategy_id": "strategy_multi_results",
            "dataset_id": "dataset_multi_results",
            "start_date": date(2020, 1, 1),
            "end_date": date(2023, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005"),
        }
        config = await repository.create_config(config_data)

        # Create multiple results for the same config
        for i in range(3):
            result_data = {
                "config_id": config.id,
                "status": BacktestStatus.COMPLETED.value,
                "total_return": Decimal(f"0.{20 + i}"),
                "annual_return": Decimal("0.08"),
                "sharpe_ratio": Decimal("1.5"),
                "max_drawdown": Decimal("0.15"),
                "win_rate": Decimal("0.55"),
            }
            await repository.create_result(result_data)

        # Retrieve results
        results = await repository.get_results_by_config(config.id)

        assert len(results) == 3
        assert all(r.config_id == config.id for r in results)

    @pytest.mark.asyncio
    async def test_get_results_by_status(self, db_session: AsyncSession):
        """Test retrieving results by status"""
        repository = BacktestRepository(db_session)

        # Create configs and results with different statuses
        statuses = [BacktestStatus.COMPLETED, BacktestStatus.RUNNING, BacktestStatus.FAILED]

        for status in statuses:
            config_data = {
                "strategy_id": f"strategy_{status.value}",
                "dataset_id": f"dataset_{status.value}",
                "start_date": date(2020, 1, 1),
                "end_date": date(2023, 12, 31),
                "initial_capital": Decimal("1000000.00"),
                "commission_rate": Decimal("0.001"),
                "slippage": Decimal("0.0005"),
            }
            config = await repository.create_config(config_data)

            result_data = {
                "config_id": config.id,
                "status": status.value,
                "total_return": Decimal("0.20"),
                "annual_return": Decimal("0.08"),
                "sharpe_ratio": Decimal("1.5"),
                "max_drawdown": Decimal("0.15"),
                "win_rate": Decimal("0.55"),
            }
            await repository.create_result(result_data)

        # Retrieve only COMPLETED results
        completed_results = await repository.get_results_by_status(BacktestStatus.COMPLETED.value)

        assert len(completed_results) >= 1
        assert all(r.status == BacktestStatus.COMPLETED.value for r in completed_results)

    @pytest.mark.asyncio
    async def test_update_result_status(self, db_session: AsyncSession):
        """Test updating a backtest result status"""
        repository = BacktestRepository(db_session)

        # Create config and result
        config_data = {
            "strategy_id": "strategy_status_update",
            "dataset_id": "dataset_status_update",
            "start_date": date(2020, 1, 1),
            "end_date": date(2023, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005"),
        }
        config = await repository.create_config(config_data)

        result_data = {
            "config_id": config.id,
            "status": BacktestStatus.PENDING.value,
            "total_return": Decimal("0.0"),
            "annual_return": Decimal("0.0"),
            "sharpe_ratio": Decimal("0.0"),
            "max_drawdown": Decimal("0.0"),
            "win_rate": Decimal("0.0"),
        }
        result = await repository.create_result(result_data)

        # Update status to RUNNING
        updated_result = await repository.update_result_status(result.id, BacktestStatus.RUNNING.value)

        assert updated_result.status == BacktestStatus.RUNNING.value

        # Update status to COMPLETED with metrics
        final_update = {
            "status": BacktestStatus.COMPLETED.value,
            "total_return": Decimal("0.25"),
            "sharpe_ratio": Decimal("1.8"),
        }
        final_result = await repository.update_result(result.id, final_update)

        assert final_result.status == BacktestStatus.COMPLETED.value
        assert final_result.total_return == Decimal("0.25")

    @pytest.mark.asyncio
    async def test_soft_delete_result(self, db_session: AsyncSession):
        """Test soft deleting a backtest result"""
        repository = BacktestRepository(db_session)

        # Create config and result
        config_data = {
            "strategy_id": "strategy_delete_result",
            "dataset_id": "dataset_delete_result",
            "start_date": date(2020, 1, 1),
            "end_date": date(2023, 12, 31),
            "initial_capital": Decimal("1000000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005"),
        }
        config = await repository.create_config(config_data)

        result_data = {
            "config_id": config.id,
            "status": BacktestStatus.COMPLETED.value,
            "total_return": Decimal("0.20"),
            "annual_return": Decimal("0.08"),
            "sharpe_ratio": Decimal("1.5"),
            "max_drawdown": Decimal("0.15"),
            "win_rate": Decimal("0.55"),
        }
        result = await repository.create_result(result_data)

        # Soft delete it
        await repository.delete_result(result.id)

        # Should not be retrievable by normal queries
        retrieved_result = await repository.get_result_by_id(result.id)
        assert retrieved_result is None

        # But should still exist in database with is_deleted=True
        stmt = select(BacktestResult).where(BacktestResult.id == result.id)
        db_result = await db_session.execute(stmt)
        deleted_result = db_result.scalar_one_or_none()
        assert deleted_result is not None
        assert deleted_result.is_deleted is True


class TestBacktestRepositoryQueries:
    """Test suite for complex query operations"""

    @pytest.mark.asyncio
    async def test_get_configs_with_pagination(self, db_session: AsyncSession):
        """Test retrieving configs with pagination"""
        repository = BacktestRepository(db_session)

        # Create 10 configs
        for i in range(10):
            config_data = {
                "strategy_id": f"strategy_page_{i}",
                "dataset_id": f"dataset_page_{i}",
                "start_date": date(2020, 1, 1),
                "end_date": date(2023, 12, 31),
                "initial_capital": Decimal("1000000.00"),
                "commission_rate": Decimal("0.001"),
                "slippage": Decimal("0.0005"),
            }
            await repository.create_config(config_data)

        # Get first page (5 items)
        page1 = await repository.get_configs(skip=0, limit=5)
        assert len(page1) == 5

        # Get second page (5 items)
        page2 = await repository.get_configs(skip=5, limit=5)
        assert len(page2) == 5

        # Ensure no overlap
        page1_ids = {c.id for c in page1}
        page2_ids = {c.id for c in page2}
        assert len(page1_ids & page2_ids) == 0

    @pytest.mark.asyncio
    async def test_get_configs_by_date_range(self, db_session: AsyncSession):
        """Test retrieving configs by date range"""
        repository = BacktestRepository(db_session)

        # Create configs with different date ranges
        date_ranges = [
            (date(2020, 1, 1), date(2020, 12, 31)),
            (date(2021, 1, 1), date(2021, 12, 31)),
            (date(2022, 1, 1), date(2022, 12, 31)),
        ]

        for start, end in date_ranges:
            config_data = {
                "strategy_id": f"strategy_{start.year}",
                "dataset_id": f"dataset_{start.year}",
                "start_date": start,
                "end_date": end,
                "initial_capital": Decimal("1000000.00"),
                "commission_rate": Decimal("0.001"),
                "slippage": Decimal("0.0005"),
            }
            await repository.create_config(config_data)

        # Query configs that overlap with 2021
        configs_2021 = await repository.get_configs_by_date_range(
            date(2021, 1, 1),
            date(2021, 12, 31)
        )

        assert len(configs_2021) >= 1
        assert all(
            c.start_date <= date(2021, 12, 31) and c.end_date >= date(2021, 1, 1)
            for c in configs_2021
        )

    @pytest.mark.asyncio
    async def test_get_best_performing_results(self, db_session: AsyncSession):
        """Test retrieving best performing backtest results"""
        repository = BacktestRepository(db_session)

        # Create configs and results with different performance
        returns = [Decimal("0.10"), Decimal("0.25"), Decimal("0.15"), Decimal("0.30"), Decimal("0.20")]

        for i, ret in enumerate(returns):
            config_data = {
                "strategy_id": f"strategy_perf_{i}",
                "dataset_id": f"dataset_perf_{i}",
                "start_date": date(2020, 1, 1),
                "end_date": date(2023, 12, 31),
                "initial_capital": Decimal("1000000.00"),
                "commission_rate": Decimal("0.001"),
                "slippage": Decimal("0.0005"),
            }
            config = await repository.create_config(config_data)

            result_data = {
                "config_id": config.id,
                "status": BacktestStatus.COMPLETED.value,
                "total_return": ret,
                "annual_return": Decimal("0.08"),
                "sharpe_ratio": Decimal("1.5"),
                "max_drawdown": Decimal("0.15"),
                "win_rate": Decimal("0.55"),
            }
            await repository.create_result(result_data)

        # Get top 3 performing results
        top_results = await repository.get_best_performing_results(limit=3)

        assert len(top_results) == 3
        # Should be sorted by total_return descending
        assert top_results[0].total_return == Decimal("0.30")
        assert top_results[1].total_return == Decimal("0.25")
        assert top_results[2].total_return == Decimal("0.20")

    @pytest.mark.asyncio
    async def test_count_results_by_status(self, db_session: AsyncSession):
        """Test counting results by status"""
        repository = BacktestRepository(db_session)

        # Create results with different statuses
        status_counts = {
            BacktestStatus.COMPLETED: 5,
            BacktestStatus.RUNNING: 2,
            BacktestStatus.FAILED: 1,
        }

        for status, count in status_counts.items():
            for i in range(count):
                config_data = {
                    "strategy_id": f"strategy_{status.value}_{i}",
                    "dataset_id": f"dataset_{status.value}_{i}",
                    "start_date": date(2020, 1, 1),
                    "end_date": date(2023, 12, 31),
                    "initial_capital": Decimal("1000000.00"),
                    "commission_rate": Decimal("0.001"),
                    "slippage": Decimal("0.0005"),
                }
                config = await repository.create_config(config_data)

                result_data = {
                    "config_id": config.id,
                    "status": status.value,
                    "total_return": Decimal("0.20"),
                    "annual_return": Decimal("0.08"),
                    "sharpe_ratio": Decimal("1.5"),
                    "max_drawdown": Decimal("0.15"),
                    "win_rate": Decimal("0.55"),
                }
                await repository.create_result(result_data)

        # Count results by status
        completed_count = await repository.count_results_by_status(BacktestStatus.COMPLETED.value)
        running_count = await repository.count_results_by_status(BacktestStatus.RUNNING.value)
        failed_count = await repository.count_results_by_status(BacktestStatus.FAILED.value)

        assert completed_count >= 5
        assert running_count >= 2
        assert failed_count >= 1
