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
