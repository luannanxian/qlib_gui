"""
TDD Tests for Diagnostic Service

Test coverage for:
- Risk analysis (volatility, VaR, CVaR)
- Return analysis (return sources, distribution)
- Overfitting detection (in-sample vs out-sample comparison)
- Optimization suggestions
"""

import pytest
from decimal import Decimal

from app.modules.backtest.services.diagnostic_service import DiagnosticService
from app.modules.backtest.exceptions import ResourceNotFoundError


class TestRiskAnalysis:
    """Test risk analysis functionality."""

    @pytest.mark.asyncio
    async def test_calculate_volatility(self, diagnostic_service: DiagnosticService, sample_result_id: str):
        """Test calculating volatility metrics."""
        # ACT
        risk_metrics = await diagnostic_service.calculate_risk_metrics(sample_result_id)

        # ASSERT
        assert "volatility" in risk_metrics
        assert "var_95" in risk_metrics  # Value at Risk at 95% confidence
        assert "cvar_95" in risk_metrics  # Conditional VaR at 95%
        assert isinstance(risk_metrics["volatility"], (Decimal, float))

    @pytest.mark.asyncio
    async def test_risk_analysis_not_found(self, diagnostic_service: DiagnosticService):
        """Test risk analysis for non-existent result."""
        # ACT & ASSERT
        with pytest.raises(ResourceNotFoundError):
            await diagnostic_service.calculate_risk_metrics("nonexistent_id")


class TestReturnAnalysis:
    """Test return analysis functionality."""

    @pytest.mark.asyncio
    async def test_analyze_return_sources(self, diagnostic_service: DiagnosticService, sample_result_id: str):
        """Test analyzing return sources."""
        # ACT
        return_analysis = await diagnostic_service.analyze_return_sources(sample_result_id)

        # ASSERT
        assert "total_return" in return_analysis
        assert "return_distribution" in return_analysis
        assert "positive_days" in return_analysis
        assert "negative_days" in return_analysis

    @pytest.mark.asyncio
    async def test_return_analysis_not_found(self, diagnostic_service: DiagnosticService):
        """Test return analysis for non-existent result."""
        # ACT & ASSERT
        with pytest.raises(ResourceNotFoundError):
            await diagnostic_service.analyze_return_sources("nonexistent_id")


class TestOverfittingDetection:
    """Test overfitting detection functionality."""

    @pytest.mark.asyncio
    async def test_detect_overfitting(self, diagnostic_service: DiagnosticService, sample_result_id: str):
        """Test detecting overfitting indicators."""
        # ACT
        overfitting_analysis = await diagnostic_service.detect_overfitting(sample_result_id)

        # ASSERT
        assert "overfitting_score" in overfitting_analysis
        assert "stability_score" in overfitting_analysis
        assert "recommendation" in overfitting_analysis
        assert isinstance(overfitting_analysis["overfitting_score"], (Decimal, float))

    @pytest.mark.asyncio
    async def test_overfitting_detection_not_found(self, diagnostic_service: DiagnosticService):
        """Test overfitting detection for non-existent result."""
        # ACT & ASSERT
        with pytest.raises(ResourceNotFoundError):
            await diagnostic_service.detect_overfitting("nonexistent_id")


class TestOptimizationSuggestions:
    """Test optimization suggestions functionality."""

    @pytest.mark.asyncio
    async def test_generate_optimization_suggestions(
        self, diagnostic_service: DiagnosticService, sample_result_id: str
    ):
        """Test generating optimization suggestions."""
        # ACT
        suggestions = await diagnostic_service.generate_optimization_suggestions(sample_result_id)

        # ASSERT
        assert "suggestions" in suggestions
        assert isinstance(suggestions["suggestions"], list)
        assert len(suggestions["suggestions"]) > 0
        # Each suggestion should have priority and description
        for suggestion in suggestions["suggestions"]:
            assert "priority" in suggestion
            assert "description" in suggestion
            assert "category" in suggestion


class TestComprehensiveDiagnostic:
    """Test comprehensive diagnostic report."""

    @pytest.mark.asyncio
    async def test_get_comprehensive_diagnostic(
        self, diagnostic_service: DiagnosticService, sample_result_id: str
    ):
        """Test getting comprehensive diagnostic report."""
        # ACT
        diagnostic_report = await diagnostic_service.get_comprehensive_diagnostic(sample_result_id)

        # ASSERT
        assert "risk_metrics" in diagnostic_report
        assert "return_analysis" in diagnostic_report
        assert "overfitting_analysis" in diagnostic_report
        assert "optimization_suggestions" in diagnostic_report
        # Verify all sub-components are present
        assert diagnostic_report["risk_metrics"]["volatility"] is not None
        assert diagnostic_report["return_analysis"]["total_return"] is not None
