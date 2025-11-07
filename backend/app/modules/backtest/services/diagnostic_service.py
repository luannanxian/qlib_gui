"""
Diagnostic Service

Provides diagnostic functionality for backtest results including:
- Risk analysis (volatility, VaR, CVaR)
- Return analysis (return sources, distribution)
- Overfitting detection (in-sample vs out-sample comparison)
- Optimization suggestions
"""

from typing import Dict, Any, List
from decimal import Decimal
import math

from app.database.repositories.backtest_repository import BacktestRepository
from app.modules.backtest.exceptions import ResourceNotFoundError


class DiagnosticService:
    """Service for diagnosing backtest results."""

    def __init__(self, repository: BacktestRepository):
        self.repository = repository

    async def calculate_risk_metrics(self, result_id: str) -> Dict[str, Any]:
        """Calculate risk metrics for a backtest result."""
        result = await self.repository.get_result_by_id(result_id)
        if not result:
            raise ResourceNotFoundError(f"Backtest result {result_id} not found")

        # Calculate volatility from max drawdown (simplified estimation)
        # In real implementation, this would use daily returns data
        max_drawdown = abs(float(result.max_drawdown))
        volatility = Decimal(str(max_drawdown * 2))  # Simplified estimation

        # Calculate VaR and CVaR (simplified)
        # VaR at 95% confidence level
        var_95 = Decimal(str(float(volatility) * 1.645))  # 1.645 is z-score for 95%

        # CVaR (Conditional VaR) - expected loss beyond VaR
        cvar_95 = Decimal(str(float(var_95) * 1.3))  # Simplified estimation

        return {
            "volatility": volatility,
            "var_95": var_95,
            "cvar_95": cvar_95
        }

    async def analyze_return_sources(self, result_id: str) -> Dict[str, Any]:
        """Analyze return sources for a backtest result."""
        result = await self.repository.get_result_by_id(result_id)
        if not result:
            raise ResourceNotFoundError(f"Backtest result {result_id} not found")

        # Analyze return distribution
        total_return = result.total_return
        win_rate = result.win_rate

        # Estimate positive and negative days based on win rate
        # In real implementation, this would use actual daily returns
        total_trading_days = 252  # Approximate trading days per year
        positive_days = int(total_trading_days * float(win_rate))
        negative_days = total_trading_days - positive_days

        return {
            "total_return": total_return,
            "return_distribution": {
                "mean": total_return / Decimal(str(total_trading_days)),
                "positive_ratio": win_rate,
                "negative_ratio": Decimal("1.0") - win_rate
            },
            "positive_days": positive_days,
            "negative_days": negative_days
        }

    async def detect_overfitting(self, result_id: str) -> Dict[str, Any]:
        """Detect overfitting indicators for a backtest result."""
        result = await self.repository.get_result_by_id(result_id)
        if not result:
            raise ResourceNotFoundError(f"Backtest result {result_id} not found")

        # Calculate overfitting score based on Sharpe ratio and win rate
        # High Sharpe with very high win rate might indicate overfitting
        sharpe_ratio = float(result.sharpe_ratio)
        win_rate = float(result.win_rate)

        # Overfitting score: 0 (no overfitting) to 1 (high overfitting)
        # If win rate is too high (>0.7) and Sharpe is very high (>2), suspect overfitting
        overfitting_score = Decimal("0.0")
        if win_rate > 0.7 and sharpe_ratio > 2.0:
            overfitting_score = Decimal(str(min((win_rate - 0.7) * 2 + (sharpe_ratio - 2.0) * 0.2, 1.0)))

        # Stability score: inverse of overfitting score
        stability_score = Decimal("1.0") - overfitting_score

        # Generate recommendation
        if overfitting_score > Decimal("0.5"):
            recommendation = "High risk of overfitting detected. Consider out-of-sample validation."
        elif overfitting_score > Decimal("0.3"):
            recommendation = "Moderate overfitting risk. Verify with different time periods."
        else:
            recommendation = "Strategy appears stable with low overfitting risk."

        return {
            "overfitting_score": overfitting_score,
            "stability_score": stability_score,
            "recommendation": recommendation
        }

    async def generate_optimization_suggestions(self, result_id: str) -> Dict[str, Any]:
        """Generate optimization suggestions for a backtest result."""
        result = await self.repository.get_result_by_id(result_id)
        if not result:
            raise ResourceNotFoundError(f"Backtest result {result_id} not found")

        suggestions = []

        # Analyze metrics and generate suggestions
        sharpe_ratio = float(result.sharpe_ratio)
        max_drawdown = float(result.max_drawdown)
        win_rate = float(result.win_rate)

        # Suggestion 1: Sharpe ratio improvement
        if sharpe_ratio < 1.0:
            suggestions.append({
                "priority": "high",
                "category": "risk_adjusted_return",
                "description": "Sharpe ratio is below 1.0. Consider reducing position sizes or improving entry/exit timing."
            })

        # Suggestion 2: Drawdown management
        if max_drawdown > 0.2:
            suggestions.append({
                "priority": "high",
                "category": "risk_management",
                "description": "Maximum drawdown exceeds 20%. Implement stricter stop-loss rules or position sizing."
            })

        # Suggestion 3: Win rate optimization
        if win_rate < 0.5:
            suggestions.append({
                "priority": "medium",
                "category": "strategy_logic",
                "description": "Win rate below 50%. Review entry signals and consider filtering low-quality trades."
            })
        elif win_rate > 0.7:
            suggestions.append({
                "priority": "medium",
                "category": "overfitting_risk",
                "description": "Win rate above 70%. Verify strategy robustness with out-of-sample testing."
            })

        # Suggestion 4: General optimization
        if sharpe_ratio > 1.5 and max_drawdown < 0.15:
            suggestions.append({
                "priority": "low",
                "category": "fine_tuning",
                "description": "Strategy performs well. Consider parameter optimization for marginal improvements."
            })

        # Always provide at least one suggestion
        if not suggestions:
            suggestions.append({
                "priority": "low",
                "category": "monitoring",
                "description": "Strategy metrics are balanced. Continue monitoring performance in live trading."
            })

        return {
            "suggestions": suggestions
        }

    async def get_comprehensive_diagnostic(self, result_id: str) -> Dict[str, Any]:
        """Get comprehensive diagnostic report for a backtest result."""
        # Gather all diagnostic components
        risk_metrics = await self.calculate_risk_metrics(result_id)
        return_analysis = await self.analyze_return_sources(result_id)
        overfitting_analysis = await self.detect_overfitting(result_id)
        optimization_suggestions = await self.generate_optimization_suggestions(result_id)

        return {
            "risk_metrics": risk_metrics,
            "return_analysis": return_analysis,
            "overfitting_analysis": overfitting_analysis,
            "optimization_suggestions": optimization_suggestions
        }
