"""Test fixtures for data management services"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


@pytest.fixture
def sample_stock_data() -> pd.DataFrame:
    """
    Create sample OHLCV stock data for testing.

    Returns 100 days of realistic stock price data with volume.
    """
    # Generate 100 days of data
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")

    # Generate realistic price movements
    np.random.seed(42)  # For reproducibility

    # Start with a base price and simulate random walk
    base_price = 100.0
    returns = np.random.normal(0.001, 0.02, size=100)  # 0.1% mean return, 2% volatility
    prices = base_price * np.exp(np.cumsum(returns))

    # Generate OHLC from close prices with realistic spreads
    close_prices = prices
    high_prices = close_prices * (1 + np.abs(np.random.normal(0, 0.01, size=100)))
    low_prices = close_prices * (1 - np.abs(np.random.normal(0, 0.01, size=100)))

    # Open prices are close to previous close with some gap
    open_prices = np.roll(close_prices, 1) * (1 + np.random.normal(0, 0.005, size=100))
    open_prices[0] = base_price

    # Generate volume data (correlated with price movements)
    base_volume = 1000000
    volume = base_volume * (1 + np.abs(returns) * 10) * (1 + np.random.normal(0, 0.3, size=100))
    volume = volume.astype(int)

    df = pd.DataFrame({
        "date": dates,
        "open": open_prices,
        "high": high_prices,
        "low": low_prices,
        "close": close_prices,
        "volume": volume
    })

    return df


@pytest.fixture
def sample_stock_data_with_trend() -> pd.DataFrame:
    """
    Create sample stock data with clear uptrend for testing indicators.

    Returns 50 days of uptrending stock data.
    """
    dates = pd.date_range(start="2024-01-01", periods=50, freq="D")

    # Create uptrend
    base_price = 100.0
    trend = np.linspace(0, 0.3, 50)  # 30% uptrend
    noise = np.random.normal(0, 0.01, size=50)
    close_prices = base_price * (1 + trend + noise)

    # Generate OHLC
    high_prices = close_prices * 1.01
    low_prices = close_prices * 0.99
    open_prices = np.roll(close_prices, 1)
    open_prices[0] = base_price

    volume = np.random.randint(500000, 1500000, size=50)

    df = pd.DataFrame({
        "date": dates,
        "open": open_prices,
        "high": high_prices,
        "low": low_prices,
        "close": close_prices,
        "volume": volume
    })

    return df


@pytest.fixture
def sample_stock_data_minimal() -> pd.DataFrame:
    """
    Create minimal stock data for edge case testing.

    Returns just 10 days of data.
    """
    dates = pd.date_range(start="2024-01-01", periods=10, freq="D")

    close_prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]

    df = pd.DataFrame({
        "date": dates,
        "open": [99, 101, 100, 102, 104, 103, 105, 107, 106, 108],
        "high": [103, 104, 103, 105, 107, 106, 108, 110, 109, 111],
        "low": [98, 100, 99, 101, 103, 102, 104, 106, 105, 107],
        "close": close_prices,
        "volume": [1000000] * 10
    })

    return df


@pytest.fixture
def expected_ma_values() -> dict:
    """Expected moving average values for validation."""
    return {
        "ma5": [None, None, None, None, 101.0],  # First 4 are NaN, 5th is average of first 5
        "ma10": [None] * 9 + [101.5],  # First 9 are NaN
    }


@pytest.fixture
def sample_dataset_data() -> dict:
    """Sample dataset data for creating test datasets."""
    return {
        "name": "Test Stock Dataset",
        "source": "local",
        "file_path": "/tmp/test_stock.csv",
        "status": "valid",
        "row_count": 100,
        "columns": ["date", "open", "high", "low", "close", "volume"],
        "extra_metadata": {
            "symbol": "TEST",
            "market": "US",
            "frequency": "daily"
        }
    }


@pytest.fixture
def sample_chart_config_data() -> dict:
    """Sample chart configuration data for testing."""
    return {
        "name": "Test K-Line Chart",
        "chart_type": "kline",
        "dataset_id": "test-dataset-id",
        "config": {
            "indicators": ["MACD", "RSI"],
            "macd_params": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
            "rsi_params": {"period": 14, "overbought": 70, "oversold": 30}
        },
        "description": "Test chart configuration"
    }
