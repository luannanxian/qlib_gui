"""
Technical Indicator Service

This service provides calculations for various technical indicators
used in financial chart analysis.

Supported Indicators:
- MACD (Moving Average Convergence Divergence)
- RSI (Relative Strength Index)
- KDJ (Stochastic Oscillator)
- Moving Averages (MA)
- Volume Indicators

Implementation uses pandas and numpy for efficient calculations.
Falls back to pandas if TA-Lib is not available.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Union
from loguru import logger


class IndicatorCalculationError(Exception):
    """Raised when indicator calculation fails."""
    pass


class InsufficientDataError(Exception):
    """Raised when there is insufficient data for indicator calculation."""
    pass


class IndicatorService:
    """
    Service for calculating technical indicators on stock data.

    This service provides methods to calculate various technical indicators
    commonly used in financial analysis and chart visualization.
    """

    def __init__(self):
        """Initialize the indicator service."""
        self.supported_indicators = ["MACD", "RSI", "KDJ", "MA", "VOLUME"]
        logger.info("IndicatorService initialized")

    def calculate_macd(
        self,
        data: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        column: str = "close"
    ) -> Dict[str, Union[List, pd.Series, np.ndarray]]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        MACD = EMA(fast) - EMA(slow)
        Signal = EMA(MACD, signal_period)
        Histogram = MACD - Signal

        Args:
            data: DataFrame with price data
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line EMA period (default: 9)
            column: Price column to use (default: "close")

        Returns:
            Dictionary with 'macd', 'signal', and 'histogram' arrays

        Raises:
            InsufficientDataError: If data has fewer rows than required
            IndicatorCalculationError: If required column is missing
        """
        self._validate_dataframe(data, min_rows=slow_period + signal_period)
        self._validate_column_exists(data, column)

        try:
            prices = data[column].copy()

            # Calculate EMAs
            ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
            ema_slow = prices.ewm(span=slow_period, adjust=False).mean()

            # Calculate MACD line
            macd_line = ema_fast - ema_slow

            # Calculate signal line
            signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

            # Calculate histogram
            histogram = macd_line - signal_line

            logger.debug(
                f"MACD calculated: fast={fast_period}, slow={slow_period}, "
                f"signal={signal_period}"
            )

            return {
                "macd": macd_line.values,
                "signal": signal_line.values,
                "histogram": histogram.values
            }

        except KeyError as e:
            raise IndicatorCalculationError(f"Missing required column: {column}") from e
        except Exception as e:
            logger.error(f"Error calculating MACD: {str(e)}")
            raise IndicatorCalculationError(f"Failed to calculate MACD: {str(e)}") from e

    def calculate_rsi(
        self,
        data: pd.DataFrame,
        period: int = 14,
        overbought: float = 70,
        oversold: float = 30,
        column: str = "close"
    ) -> Dict[str, Union[List, pd.Series, np.ndarray, float]]:
        """
        Calculate RSI (Relative Strength Index).

        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss

        Args:
            data: DataFrame with price data
            period: RSI period (default: 14)
            overbought: Overbought threshold (default: 70)
            oversold: Oversold threshold (default: 30)
            column: Price column to use (default: "close")

        Returns:
            Dictionary with 'rsi', 'overbought_line', and 'oversold_line'

        Raises:
            InsufficientDataError: If data has fewer rows than required
            IndicatorCalculationError: If required column is missing or has invalid values
        """
        self._validate_dataframe(data, min_rows=period + 1)
        self._validate_column_exists(data, column)

        try:
            prices = data[column].copy()

            # Validate no negative prices
            if (prices < 0).any():
                raise IndicatorCalculationError("Price data contains negative values")

            # Calculate price changes
            delta = prices.diff()

            # Separate gains and losses
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)

            # Calculate average gain and loss using exponential moving average
            avg_gain = gain.ewm(span=period, adjust=False).mean()
            avg_loss = loss.ewm(span=period, adjust=False).mean()

            # Calculate RS and RSI
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            logger.debug(f"RSI calculated: period={period}")

            return {
                "rsi": rsi.values,
                "overbought_line": overbought,
                "oversold_line": oversold
            }

        except KeyError as e:
            raise IndicatorCalculationError(f"Missing required column: {column}") from e
        except Exception as e:
            logger.error(f"Error calculating RSI: {str(e)}")
            raise IndicatorCalculationError(f"Failed to calculate RSI: {str(e)}") from e

    def calculate_kdj(
        self,
        data: pd.DataFrame,
        k_period: int = 9,
        d_period: int = 3,
        j_period: int = 3
    ) -> Dict[str, Union[List, pd.Series, np.ndarray]]:
        """
        Calculate KDJ (Stochastic Oscillator).

        RSV = (Close - Lowest Low) / (Highest High - Lowest Low) * 100
        K = SMA(RSV, k_period)
        D = SMA(K, d_period)
        J = 3 * K - 2 * D

        Args:
            data: DataFrame with OHLC data
            k_period: K period (default: 9)
            d_period: D period (default: 3)
            j_period: J period (default: 3)

        Returns:
            Dictionary with 'k', 'd', and 'j' arrays

        Raises:
            InsufficientDataError: If data has fewer rows than required
            IndicatorCalculationError: If required columns are missing
        """
        self._validate_dataframe(data, min_rows=k_period)
        required_columns = ["high", "low", "close"]
        for col in required_columns:
            self._validate_column_exists(data, col)

        try:
            high = data["high"]
            low = data["low"]
            close = data["close"]

            # Calculate RSV (Raw Stochastic Value)
            lowest_low = low.rolling(window=k_period).min()
            highest_high = high.rolling(window=k_period).max()

            rsv = ((close - lowest_low) / (highest_high - lowest_low)) * 100

            # Calculate K line (smoothed RSV)
            k = rsv.ewm(span=d_period, adjust=False).mean()

            # Calculate D line (smoothed K)
            d = k.ewm(span=j_period, adjust=False).mean()

            # Calculate J line
            j = 3 * k - 2 * d

            logger.debug(f"KDJ calculated: k_period={k_period}, d_period={d_period}, j_period={j_period}")

            return {
                "k": k.values,
                "d": d.values,
                "j": j.values
            }

        except KeyError as e:
            raise IndicatorCalculationError(
                f"Missing required columns for KDJ: {required_columns}"
            ) from e
        except Exception as e:
            logger.error(f"Error calculating KDJ: {str(e)}")
            raise IndicatorCalculationError(f"Failed to calculate KDJ: {str(e)}") from e

    def calculate_ma(
        self,
        data: pd.DataFrame,
        periods: List[int] = None,
        column: str = "close"
    ) -> Dict[str, Union[List, pd.Series, np.ndarray]]:
        """
        Calculate Moving Averages for multiple periods.

        Args:
            data: DataFrame with price data
            periods: List of periods to calculate (default: [5, 10, 20, 60])
            column: Price column to use (default: "close")

        Returns:
            Dictionary with MA values for each period (e.g., 'ma5', 'ma10')

        Raises:
            IndicatorCalculationError: If required column is missing
        """
        if periods is None:
            periods = [5, 10, 20, 60]

        self._validate_column_exists(data, column)

        try:
            prices = data[column]
            result = {}

            for period in periods:
                ma = prices.rolling(window=period).mean()
                result[f"ma{period}"] = ma.values

            logger.debug(f"MA calculated for periods: {periods}")

            return result

        except KeyError as e:
            raise IndicatorCalculationError(f"Missing required column: {column}") from e
        except Exception as e:
            logger.error(f"Error calculating MA: {str(e)}")
            raise IndicatorCalculationError(f"Failed to calculate MA: {str(e)}") from e

    def calculate_volume_indicators(
        self,
        data: pd.DataFrame,
        periods: List[int] = None,
        include_ratio: bool = False
    ) -> Dict[str, Union[List, pd.Series, np.ndarray]]:
        """
        Calculate volume-based indicators.

        Args:
            data: DataFrame with volume data
            periods: List of periods for volume MA (default: [5, 10])
            include_ratio: Whether to include volume ratio (default: False)

        Returns:
            Dictionary with volume indicators

        Raises:
            IndicatorCalculationError: If volume column is missing
        """
        if periods is None:
            periods = [5, 10]

        self._validate_column_exists(data, "volume")

        try:
            volume = data["volume"]
            result = {}

            # Calculate volume moving averages
            for period in periods:
                volume_ma = volume.rolling(window=period).mean()
                result[f"volume_ma{period}"] = volume_ma.values

            # Calculate volume ratio if requested
            if include_ratio:
                volume_ma5 = volume.rolling(window=5).mean()
                volume_ratio = (volume / volume_ma5) * 100
                result["volume_ratio"] = volume_ratio.values

            logger.debug(f"Volume indicators calculated for periods: {periods}")

            return result

        except KeyError as e:
            raise IndicatorCalculationError("Missing required column: volume") from e
        except Exception as e:
            logger.error(f"Error calculating volume indicators: {str(e)}")
            raise IndicatorCalculationError(
                f"Failed to calculate volume indicators: {str(e)}"
            ) from e

    def calculate_multiple_indicators(
        self,
        data: pd.DataFrame,
        indicators: List[str],
        params: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calculate multiple indicators at once.

        Args:
            data: DataFrame with OHLCV data
            indicators: List of indicator names to calculate (max 3)
            params: Optional parameters for each indicator

        Returns:
            Dictionary with results for each indicator

        Raises:
            ValueError: If more than 3 indicators requested or invalid indicator name
            InsufficientDataError: If data is insufficient
            IndicatorCalculationError: If calculation fails
        """
        # Validate max 3 indicators
        if len(indicators) > 3:
            raise ValueError("Maximum 3 indicators can be calculated at once")

        # Validate indicator names
        for indicator in indicators:
            if indicator not in self.supported_indicators:
                raise ValueError(
                    f"Invalid indicator: {indicator}. "
                    f"Supported: {self.supported_indicators}"
                )

        if params is None:
            params = {}

        result = {}

        try:
            for indicator in indicators:
                indicator_params = params.get(indicator, {})

                if indicator == "MACD":
                    result["MACD"] = self.calculate_macd(data, **indicator_params)
                elif indicator == "RSI":
                    result["RSI"] = self.calculate_rsi(data, **indicator_params)
                elif indicator == "KDJ":
                    result["KDJ"] = self.calculate_kdj(data, **indicator_params)
                elif indicator == "MA":
                    result["MA"] = self.calculate_ma(data, **indicator_params)
                elif indicator == "VOLUME":
                    result["VOLUME"] = self.calculate_volume_indicators(
                        data, **indicator_params
                    )

            logger.info(f"Calculated multiple indicators: {indicators}")

            return result

        except Exception as e:
            logger.error(f"Error calculating multiple indicators: {str(e)}")
            raise

    def _validate_dataframe(self, data: pd.DataFrame, min_rows: int = 1):
        """
        Validate that dataframe has sufficient data.

        Args:
            data: DataFrame to validate
            min_rows: Minimum required rows

        Raises:
            InsufficientDataError: If data is insufficient
        """
        if data is None or data.empty:
            raise InsufficientDataError("Data is empty")

        if len(data) < min_rows:
            raise InsufficientDataError(
                f"Insufficient data: {len(data)} rows, minimum {min_rows} required"
            )

    def _validate_column_exists(self, data: pd.DataFrame, column: str):
        """
        Validate that required column exists in dataframe.

        Args:
            data: DataFrame to validate
            column: Column name to check

        Raises:
            IndicatorCalculationError: If column is missing
        """
        if column not in data.columns:
            raise IndicatorCalculationError(
                f"Missing required column: {column}. "
                f"Available columns: {list(data.columns)}"
            )
