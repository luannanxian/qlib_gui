"""
Results Analysis Service

Provides analysis functionality for backtest results including:
- Metrics calculation (returns, Sharpe ratio, max drawdown)
- Trade analysis (win rate, profit/loss ratio)
- Performance statistics
"""

from typing import Dict, Any
from decimal import Decimal

from app.database.repositories.backtest_repository import BacktestRepository
from app.modules.backtest.exceptions import ResourceNotFoundError


class ResultsAnalysisService:
    """Service for analyzing backtest results."""

    def __init__(self, repository: BacktestRepository):
        self.repository = repository

    async def calculate_metrics(self, result_id: str) -> Dict[str, Any]:
        """Calculate performance metrics for a backtest result."""
        result = await self.repository.get_result_by_id(result_id)
        if not result:
            raise ResourceNotFoundError(f"Backtest result {result_id} not found")

        return {
            "total_return": result.total_return,
            "annual_return": result.annual_return,
            "sharpe_ratio": result.sharpe_ratio,
            "max_drawdown": result.max_drawdown
        }

    async def analyze_trades(self, result_id: str) -> Dict[str, Any]:
        """Analyze trade statistics for a backtest result."""
        result = await self.repository.get_result_by_id(result_id)
        if not result:
            raise ResourceNotFoundError(f"Backtest result {result_id} not found")

        # Calculate profit/loss ratio from win rate
        # Simplified calculation: assuming equal position sizes
        win_rate = result.win_rate

        # Handle edge cases for profit/loss ratio calculation
        if win_rate <= Decimal("0.0"):
            # No wins, P/L ratio is 0
            profit_loss_ratio = Decimal("0.0")
        elif win_rate >= Decimal("1.0"):
            # All wins, P/L ratio is undefined (represented as None)
            profit_loss_ratio = None
        else:
            # Normal case: calculate ratio
            loss_rate = Decimal("1.0") - win_rate
            profit_loss_ratio = win_rate / loss_rate

        return {
            "win_rate": result.win_rate,
            "profit_loss_ratio": profit_loss_ratio,
            "total_trades": 0  # Placeholder - would be calculated from trade data
        }

    async def get_performance_summary(self, result_id: str) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        metrics = await self.calculate_metrics(result_id)
        trades = await self.analyze_trades(result_id)

        return {
            "metrics": metrics,
            "trades": trades
        }
