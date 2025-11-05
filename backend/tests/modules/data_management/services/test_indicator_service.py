"""
TDD Tests for Technical Indicator Service

Following TDD methodology:
1. RED: Write failing tests first
2. GREEN: Implement minimal code to pass
3. REFACTOR: Optimize and clean up

Test Coverage:
- MACD calculation (Moving Average Convergence Divergence)
- RSI calculation (Relative Strength Index)
- KDJ calculation (Stochastic Oscillator)
- Moving Averages (MA5, MA10, MA20, MA60, custom)
- Volume calculations
- Edge cases and error handling
"""

import pytest
import pandas as pd
import numpy as np
from typing import Dict, Any

from app.modules.data_management.services.indicator_service import (
    IndicatorService,
    IndicatorCalculationError,
    InsufficientDataError
)


class TestIndicatorServiceInitialization:
    """Test indicator service initialization."""

    def test_indicator_service_can_be_instantiated(self):
        """Test that IndicatorService can be created."""
        service = IndicatorService()
        assert service is not None

    def test_indicator_service_has_required_methods(self):
        """Test that IndicatorService has all required calculation methods."""
        service = IndicatorService()
        assert hasattr(service, "calculate_macd")
        assert hasattr(service, "calculate_rsi")
        assert hasattr(service, "calculate_kdj")
        assert hasattr(service, "calculate_ma")
        assert hasattr(service, "calculate_volume_indicators")
        assert hasattr(service, "calculate_multiple_indicators")


class TestMACDCalculation:
    """Test MACD (Moving Average Convergence Divergence) calculations."""

    def test_calculate_macd_with_default_parameters(self, sample_stock_data):
        """Test MACD calculation with default parameters (12, 26, 9)."""
        service = IndicatorService()

        result = service.calculate_macd(sample_stock_data)

        # Check result structure
        assert "macd" in result
        assert "signal" in result
        assert "histogram" in result

        # Check data types
        assert isinstance(result["macd"], (list, pd.Series, np.ndarray))
        assert isinstance(result["signal"], (list, pd.Series, np.ndarray))
        assert isinstance(result["histogram"], (list, pd.Series, np.ndarray))

        # Check length matches input data
        assert len(result["macd"]) == len(sample_stock_data)

    def test_calculate_macd_with_custom_parameters(self, sample_stock_data):
        """Test MACD calculation with custom parameters."""
        service = IndicatorService()

        result = service.calculate_macd(
            sample_stock_data,
            fast_period=8,
            slow_period=17,
            signal_period=5
        )

        assert "macd" in result
        assert "signal" in result
        assert "histogram" in result

    def test_macd_histogram_is_difference_of_macd_and_signal(self, sample_stock_data):
        """Test that MACD histogram = MACD - Signal."""
        service = IndicatorService()

        result = service.calculate_macd(sample_stock_data)

        # Convert to numpy arrays for comparison
        macd = np.array(result["macd"])
        signal = np.array(result["signal"])
        histogram = np.array(result["histogram"])

        # Filter out NaN values for comparison
        valid_idx = ~np.isnan(macd) & ~np.isnan(signal) & ~np.isnan(histogram)

        np.testing.assert_array_almost_equal(
            histogram[valid_idx],
            macd[valid_idx] - signal[valid_idx],
            decimal=6
        )

    def test_macd_with_insufficient_data_raises_error(self):
        """Test that MACD calculation fails with insufficient data."""
        service = IndicatorService()

        # Create data with only 10 days (less than default slow_period=26)
        insufficient_data = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=10),
            "close": [100 + i for i in range(10)]
        })

        with pytest.raises(InsufficientDataError) as exc_info:
            service.calculate_macd(insufficient_data)

        assert "insufficient data" in str(exc_info.value).lower()

    def test_macd_with_missing_close_column_raises_error(self, sample_stock_data):
        """Test that MACD calculation fails without close price column."""
        service = IndicatorService()

        # Remove close column
        invalid_data = sample_stock_data.drop(columns=["close"])

        with pytest.raises(IndicatorCalculationError) as exc_info:
            service.calculate_macd(invalid_data)

        assert "close" in str(exc_info.value).lower()


class TestRSICalculation:
    """Test RSI (Relative Strength Index) calculations."""

    def test_calculate_rsi_with_default_period(self, sample_stock_data):
        """Test RSI calculation with default 14-period."""
        service = IndicatorService()

        result = service.calculate_rsi(sample_stock_data)

        # Check result structure
        assert "rsi" in result
        assert "overbought_line" in result
        assert "oversold_line" in result

        # RSI should be between 0 and 100
        rsi_values = np.array(result["rsi"])
        valid_rsi = rsi_values[~np.isnan(rsi_values)]

        assert np.all(valid_rsi >= 0)
        assert np.all(valid_rsi <= 100)

    def test_calculate_rsi_with_custom_period(self, sample_stock_data):
        """Test RSI calculation with custom period."""
        service = IndicatorService()

        result = service.calculate_rsi(sample_stock_data, period=20)

        assert "rsi" in result
        assert len(result["rsi"]) == len(sample_stock_data)

    def test_rsi_with_custom_overbought_oversold_levels(self, sample_stock_data):
        """Test RSI with custom overbought/oversold levels."""
        service = IndicatorService()

        result = service.calculate_rsi(
            sample_stock_data,
            overbought=75,
            oversold=25
        )

        assert result["overbought_line"] == 75
        assert result["oversold_line"] == 25

    def test_rsi_with_insufficient_data_raises_error(self):
        """Test that RSI calculation fails with insufficient data."""
        service = IndicatorService()

        # Create data with only 5 days (less than default period=14)
        insufficient_data = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=5),
            "close": [100 + i for i in range(5)]
        })

        with pytest.raises(InsufficientDataError):
            service.calculate_rsi(insufficient_data)

    def test_rsi_identifies_overbought_conditions(self, sample_stock_data_with_trend):
        """Test that RSI correctly identifies overbought conditions in uptrend."""
        service = IndicatorService()

        result = service.calculate_rsi(sample_stock_data_with_trend, period=14)

        # In a strong uptrend, we should see RSI values above 70
        rsi_values = np.array(result["rsi"])
        valid_rsi = rsi_values[~np.isnan(rsi_values)]

        # At least some values should be overbought in strong uptrend
        assert np.any(valid_rsi > 70)


class TestKDJCalculation:
    """Test KDJ (Stochastic Oscillator) calculations."""

    def test_calculate_kdj_with_default_parameters(self, sample_stock_data):
        """Test KDJ calculation with default parameters (9, 3, 3)."""
        service = IndicatorService()

        result = service.calculate_kdj(sample_stock_data)

        # Check result structure
        assert "k" in result
        assert "d" in result
        assert "j" in result

        # Check length
        assert len(result["k"]) == len(sample_stock_data)
        assert len(result["d"]) == len(sample_stock_data)
        assert len(result["j"]) == len(sample_stock_data)

    def test_calculate_kdj_with_custom_parameters(self, sample_stock_data):
        """Test KDJ calculation with custom parameters."""
        service = IndicatorService()

        result = service.calculate_kdj(
            sample_stock_data,
            k_period=14,
            d_period=5,
            j_period=5
        )

        assert "k" in result
        assert "d" in result
        assert "j" in result

    def test_kdj_values_in_valid_range(self, sample_stock_data):
        """Test that K and D values are typically between 0 and 100."""
        service = IndicatorService()

        result = service.calculate_kdj(sample_stock_data)

        # K and D should generally be between 0 and 100 (though can exceed)
        k_values = np.array(result["k"])
        d_values = np.array(result["d"])

        valid_k = k_values[~np.isnan(k_values)]
        valid_d = d_values[~np.isnan(d_values)]

        # Most values should be in range (allowing some outliers)
        assert np.percentile(valid_k, 5) >= -10  # Allow slight overflow
        assert np.percentile(valid_k, 95) <= 110
        assert np.percentile(valid_d, 5) >= -10
        assert np.percentile(valid_d, 95) <= 110

    def test_kdj_j_formula(self, sample_stock_data):
        """Test that J = 3*K - 2*D."""
        service = IndicatorService()

        result = service.calculate_kdj(sample_stock_data)

        k = np.array(result["k"])
        d = np.array(result["d"])
        j = np.array(result["j"])

        # Filter valid values
        valid_idx = ~np.isnan(k) & ~np.isnan(d) & ~np.isnan(j)

        np.testing.assert_array_almost_equal(
            j[valid_idx],
            3 * k[valid_idx] - 2 * d[valid_idx],
            decimal=6
        )

    def test_kdj_with_insufficient_data_raises_error(self):
        """Test that KDJ calculation fails with insufficient data."""
        service = IndicatorService()

        insufficient_data = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=5),
            "high": [100 + i for i in range(5)],
            "low": [90 + i for i in range(5)],
            "close": [95 + i for i in range(5)]
        })

        with pytest.raises(InsufficientDataError):
            service.calculate_kdj(insufficient_data)

    def test_kdj_with_missing_columns_raises_error(self, sample_stock_data):
        """Test that KDJ requires high, low, close columns."""
        service = IndicatorService()

        # Missing high column
        invalid_data = sample_stock_data.drop(columns=["high"])

        with pytest.raises(IndicatorCalculationError):
            service.calculate_kdj(invalid_data)


class TestMovingAverageCalculation:
    """Test Moving Average calculations."""

    def test_calculate_ma_single_period(self, sample_stock_data):
        """Test calculating single moving average."""
        service = IndicatorService()

        result = service.calculate_ma(sample_stock_data, periods=[5])

        assert "ma5" in result
        assert len(result["ma5"]) == len(sample_stock_data)

    def test_calculate_ma_multiple_periods(self, sample_stock_data):
        """Test calculating multiple moving averages."""
        service = IndicatorService()

        result = service.calculate_ma(sample_stock_data, periods=[5, 10, 20, 60])

        assert "ma5" in result
        assert "ma10" in result
        assert "ma20" in result
        assert "ma60" in result

    def test_ma_calculation_accuracy(self, sample_stock_data_minimal):
        """Test MA calculation accuracy with known values."""
        service = IndicatorService()

        result = service.calculate_ma(sample_stock_data_minimal, periods=[5])

        ma5 = np.array(result["ma5"])

        # First 4 values should be NaN
        assert np.isnan(ma5[0])
        assert np.isnan(ma5[1])
        assert np.isnan(ma5[2])
        assert np.isnan(ma5[3])

        # 5th value should be average of first 5 close prices
        expected_ma5_4 = np.mean([100, 102, 101, 103, 105])
        np.testing.assert_almost_equal(ma5[4], expected_ma5_4, decimal=2)

    def test_ma_with_custom_column(self, sample_stock_data):
        """Test MA calculation on custom column (e.g., 'open' instead of 'close')."""
        service = IndicatorService()

        result = service.calculate_ma(
            sample_stock_data,
            periods=[5],
            column="open"
        )

        assert "ma5" in result

    def test_ma_with_insufficient_data_returns_nan(self):
        """Test that MA with insufficient data returns NaN values."""
        service = IndicatorService()

        # Data with only 3 days, requesting MA5
        insufficient_data = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=3),
            "close": [100, 102, 101]
        })

        result = service.calculate_ma(insufficient_data, periods=[5])

        ma5 = np.array(result["ma5"])
        # All values should be NaN
        assert np.all(np.isnan(ma5))

    def test_ma_with_invalid_column_raises_error(self, sample_stock_data):
        """Test that MA calculation fails with invalid column name."""
        service = IndicatorService()

        with pytest.raises(IndicatorCalculationError):
            service.calculate_ma(sample_stock_data, periods=[5], column="invalid_column")


class TestVolumeIndicators:
    """Test volume-based indicator calculations."""

    def test_calculate_volume_ma(self, sample_stock_data):
        """Test volume moving average calculation."""
        service = IndicatorService()

        result = service.calculate_volume_indicators(sample_stock_data, periods=[5, 10])

        assert "volume_ma5" in result
        assert "volume_ma10" in result

    def test_calculate_volume_ratio(self, sample_stock_data):
        """Test volume ratio calculation (current vs. average)."""
        service = IndicatorService()

        result = service.calculate_volume_indicators(
            sample_stock_data,
            include_ratio=True
        )

        assert "volume_ratio" in result

    def test_volume_indicators_with_missing_volume_column_raises_error(self):
        """Test that volume indicators require volume column."""
        service = IndicatorService()

        invalid_data = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=10),
            "close": [100 + i for i in range(10)]
        })

        with pytest.raises(IndicatorCalculationError):
            service.calculate_volume_indicators(invalid_data)


class TestMultipleIndicators:
    """Test calculating multiple indicators at once."""

    def test_calculate_multiple_indicators(self, sample_stock_data):
        """Test calculating multiple indicators in one call."""
        service = IndicatorService()

        indicators = ["MACD", "RSI", "MA"]
        params = {
            "MACD": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
            "RSI": {"period": 14},
            "MA": {"periods": [5, 10, 20]}
        }

        result = service.calculate_multiple_indicators(
            sample_stock_data,
            indicators=indicators,
            params=params
        )

        # Check all indicators are present
        assert "MACD" in result
        assert "RSI" in result
        assert "MA" in result

        # Check MACD sub-results
        assert "macd" in result["MACD"]
        assert "signal" in result["MACD"]

        # Check RSI sub-results
        assert "rsi" in result["RSI"]

        # Check MA sub-results
        assert "ma5" in result["MA"]
        assert "ma10" in result["MA"]
        assert "ma20" in result["MA"]

    def test_calculate_multiple_indicators_with_max_limit(self, sample_stock_data):
        """Test that maximum 3 indicators can be calculated at once."""
        service = IndicatorService()

        indicators = ["MACD", "RSI", "KDJ", "MA"]  # 4 indicators

        with pytest.raises(ValueError) as exc_info:
            service.calculate_multiple_indicators(
                sample_stock_data,
                indicators=indicators
            )

        assert "maximum" in str(exc_info.value).lower()
        assert "3" in str(exc_info.value)

    def test_calculate_multiple_indicators_with_invalid_indicator(self, sample_stock_data):
        """Test that invalid indicator name raises error."""
        service = IndicatorService()

        indicators = ["MACD", "INVALID_INDICATOR"]

        with pytest.raises(ValueError) as exc_info:
            service.calculate_multiple_indicators(
                sample_stock_data,
                indicators=indicators
            )

        assert "invalid" in str(exc_info.value).lower()


class TestIndicatorServiceEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe_raises_error(self):
        """Test that empty dataframe raises error."""
        service = IndicatorService()

        empty_df = pd.DataFrame()

        with pytest.raises(InsufficientDataError):
            service.calculate_macd(empty_df)

    def test_dataframe_with_nan_values_handles_gracefully(self, sample_stock_data):
        """Test that NaN values in data are handled gracefully."""
        service = IndicatorService()

        # Introduce some NaN values
        data_with_nan = sample_stock_data.copy()
        data_with_nan.loc[5:10, "close"] = np.nan

        # Should not raise error, but handle NaN appropriately
        result = service.calculate_ma(data_with_nan, periods=[5])
        assert "ma5" in result

    def test_single_row_dataframe_raises_error(self):
        """Test that single row dataframe raises error."""
        service = IndicatorService()

        single_row = pd.DataFrame({
            "date": [pd.Timestamp("2024-01-01")],
            "close": [100]
        })

        with pytest.raises(InsufficientDataError):
            service.calculate_rsi(single_row)

    def test_negative_price_values_raise_error(self):
        """Test that negative price values raise validation error."""
        service = IndicatorService()

        invalid_data = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=50),
            "close": [-100 + i for i in range(50)]  # Negative prices
        })

        with pytest.raises(IndicatorCalculationError) as exc_info:
            service.calculate_rsi(invalid_data)

        assert "negative" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()
