"""
TDD Tests for Results Analysis Service

Test coverage for:
- Metrics calculation (returns, Sharpe ratio, max drawdown)
- Trade analysis (win rate, profit/loss ratio)
- Performance statistics
"""

import pytest
from decimal import Decimal
from datetime import date

from app.modules.backtest.services.analysis_service import ResultsAnalysisService
from app.modules.backtest.exceptions import ResourceNotFoundError


class TestMetricsCalculation:
    """Test metrics calculation functionality."""

    @pytest.mark.asyncio
    async def test_calculate_basic_metrics(self, analysis_service: ResultsAnalysisService, sample_result_id: str):
        """Test calculating basic performance metrics."""
        # ACT
        metrics = await analysis_service.calculate_metrics(sample_result_id)

        # ASSERT
        assert "total_return" in metrics
        assert "annual_return" in metrics
        assert "sharpe_ratio" in metrics
        assert "max_drawdown" in metrics
        assert isinstance(metrics["total_return"], (Decimal, float))

    @pytest.mark.asyncio
    async def test_calculate_metrics_not_found(self, analysis_service: ResultsAnalysisService):
        """Test calculating metrics for non-existent result."""
        # ACT & ASSERT
        with pytest.raises(ResourceNotFoundError):
            await analysis_service.calculate_metrics("nonexistent_id")


class TestTradeAnalysis:
    """Test trade analysis functionality."""

    @pytest.mark.asyncio
    async def test_analyze_trades(self, analysis_service: ResultsAnalysisService, sample_result_id: str):
        """Test analyzing trade statistics."""
        # ACT
        trade_stats = await analysis_service.analyze_trades(sample_result_id)

        # ASSERT
        assert "win_rate" in trade_stats
        assert "profit_loss_ratio" in trade_stats
        assert "total_trades" in trade_stats
        assert isinstance(trade_stats["win_rate"], (Decimal, float))

    @pytest.mark.asyncio
    async def test_analyze_trades_not_found(self, analysis_service: ResultsAnalysisService):
        """Test analyzing trades for non-existent result."""
        # ACT & ASSERT
        with pytest.raises(ResourceNotFoundError):
            await analysis_service.analyze_trades("nonexistent_id")

    @pytest.mark.asyncio
    async def test_analyze_trades_with_zero_win_rate(self, analysis_service: ResultsAnalysisService, db_session):
        """Test analyzing trades when win_rate is 0 (all losses)."""
        # ARRANGE - Create result with 0% win rate
        from app.database.repositories.backtest_repository import BacktestRepository
        from app.database.models import BacktestConfig, BacktestResult

        repository = BacktestRepository(db_session)
        config_data = {
            "strategy_id": "strategy_zero_win",
            "dataset_id": "dataset_zero_win",
            "start_date": date(2023, 1, 1),
            "end_date": date(2023, 12, 31),
            "initial_capital": Decimal("100000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005"),
        }
        config = await repository.create_config(config_data)

        result_data = {
            "config_id": config.id,
            "status": "COMPLETED",
            "total_return": Decimal("-0.20"),
            "annual_return": Decimal("-0.20"),
            "sharpe_ratio": Decimal("-1.0"),
            "max_drawdown": Decimal("0.30"),
            "win_rate": Decimal("0.0"),  # 0% win rate
        }
        result = await repository.create_result(result_data)

        # ACT
        trade_stats = await analysis_service.analyze_trades(result.id)

        # ASSERT
        assert trade_stats["win_rate"] == Decimal("0.0")
        assert trade_stats["profit_loss_ratio"] == Decimal("0.0")  # P/L ratio should be 0

    @pytest.mark.asyncio
    async def test_analyze_trades_with_perfect_win_rate(self, analysis_service: ResultsAnalysisService, db_session):
        """Test analyzing trades when win_rate is 100% (all wins)."""
        # ARRANGE - Create result with 100% win rate
        from app.database.repositories.backtest_repository import BacktestRepository

        repository = BacktestRepository(db_session)
        config_data = {
            "strategy_id": "strategy_perfect_win",
            "dataset_id": "dataset_perfect_win",
            "start_date": date(2023, 1, 1),
            "end_date": date(2023, 12, 31),
            "initial_capital": Decimal("100000.00"),
            "commission_rate": Decimal("0.001"),
            "slippage": Decimal("0.0005"),
        }
        config = await repository.create_config(config_data)

        result_data = {
            "config_id": config.id,
            "status": "COMPLETED",
            "total_return": Decimal("0.50"),
            "annual_return": Decimal("0.50"),
            "sharpe_ratio": Decimal("3.0"),
            "max_drawdown": Decimal("0.05"),
            "win_rate": Decimal("1.0"),  # 100% win rate
        }
        result = await repository.create_result(result_data)

        # ACT
        trade_stats = await analysis_service.analyze_trades(result.id)

        # ASSERT
        assert trade_stats["win_rate"] == Decimal("1.0")
        assert trade_stats["profit_loss_ratio"] is None  # P/L ratio is undefined for 100% win rate


class TestPerformanceStatistics:
    """Test performance statistics functionality."""

    @pytest.mark.asyncio
    async def test_get_performance_summary(self, analysis_service: ResultsAnalysisService, sample_result_id: str):
        """Test getting comprehensive performance summary."""
        # ACT
        summary = await analysis_service.get_performance_summary(sample_result_id)

        # ASSERT
        assert "metrics" in summary
        assert "trades" in summary
        assert summary["metrics"]["total_return"] is not None
        assert summary["trades"]["win_rate"] is not None
