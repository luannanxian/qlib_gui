"""
Chart Data Service

This service handles chart data generation, including:
- OHLC data generation from datasets
- Date range filtering
- Technical indicator integration
- Data format conversion
- Chart annotations
- CSV export
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from io import StringIO
from loguru import logger

from app.modules.data_management.services.indicator_service import IndicatorService


class ChartDataError(Exception):
    """Raised when chart data operation fails."""
    pass


class DatasetNotFoundError(Exception):
    """Raised when dataset is not found."""
    pass


class InvalidDateRangeError(Exception):
    """Raised when date range is invalid."""
    pass


class ChartService:
    """
    Service for chart data generation and manipulation.

    Handles OHLC data generation, indicator integration,
    date filtering, annotations, and export functionality.
    """

    def __init__(self):
        """Initialize chart service with indicator service."""
        self.indicator_service = IndicatorService()
        logger.info("ChartService initialized")

    def generate_ohlc_data(
        self,
        data: pd.DataFrame,
        output_format: str = "dict",
        chart_format: str = "ohlc"
    ) -> Dict[str, Any]:
        """
        Generate OHLC data from pandas DataFrame.

        Args:
            data: DataFrame with OHLC columns
            output_format: Output format ('dict' or 'list')
            chart_format: Chart format ('ohlc' or 'candlestick')

        Returns:
            Dictionary with OHLC data in requested format

        Raises:
            ChartDataError: If required columns are missing
        """
        # Validate required columns
        required_cols = ["open", "high", "low", "close"]
        missing_cols = [col for col in required_cols if col not in data.columns]

        if missing_cols:
            raise ChartDataError(
                f"Missing required columns: {missing_cols}. "
                f"Available columns: {list(data.columns)}"
            )

        try:
            # Handle date column (may be 'date', 'datetime', or index)
            if "date" in data.columns:
                dates = data["date"]
            elif "datetime" in data.columns:
                dates = data["datetime"]
            else:
                # Use index as dates
                dates = data.index

            if chart_format == "candlestick":
                # Format: [[timestamp, open, high, low, close], ...]
                candlestick_data = []
                for idx, row in data.iterrows():
                    if "date" in data.columns:
                        timestamp = pd.Timestamp(row["date"]).timestamp() * 1000
                    elif "datetime" in data.columns:
                        timestamp = pd.Timestamp(row["datetime"]).timestamp() * 1000
                    else:
                        timestamp = pd.Timestamp(idx).timestamp() * 1000

                    candlestick_data.append([
                        timestamp,
                        float(row["open"]),
                        float(row["high"]),
                        float(row["low"]),
                        float(row["close"])
                    ])

                return {"data": candlestick_data}

            # Standard OHLC format
            result = {
                "open": data["open"].tolist() if output_format == "list" else data["open"].values,
                "high": data["high"].tolist() if output_format == "list" else data["high"].values,
                "low": data["low"].tolist() if output_format == "list" else data["low"].values,
                "close": data["close"].tolist() if output_format == "list" else data["close"].values,
            }

            # Add volume if present
            if "volume" in data.columns:
                result["volume"] = data["volume"].tolist() if output_format == "list" else data["volume"].values

            # Add dates
            if isinstance(dates, pd.Index):
                result["date"] = dates.tolist() if output_format == "list" else dates.values
            else:
                result["date"] = dates.tolist() if output_format == "list" else dates.values

            logger.debug(f"Generated OHLC data: {len(data)} records, format={chart_format}")

            return result

        except Exception as e:
            logger.error(f"Error generating OHLC data: {str(e)}")
            raise ChartDataError(f"Failed to generate OHLC data: {str(e)}") from e

    def filter_by_date_range(
        self,
        data: pd.DataFrame,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Filter data by date range.

        Args:
            data: DataFrame with date column
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Filtered DataFrame

        Raises:
            InvalidDateRangeError: If date range is invalid
        """
        # Validate date range
        if start_date and end_date and start_date > end_date:
            raise InvalidDateRangeError(
                f"Invalid date range: start_date ({start_date}) is after end_date ({end_date})"
            )

        try:
            filtered_data = data.copy()

            # Determine date column
            date_col = None
            if "date" in data.columns:
                date_col = "date"
            elif "datetime" in data.columns:
                date_col = "datetime"
            else:
                # Use index if it's datetime
                if isinstance(data.index, pd.DatetimeIndex):
                    date_col = None  # Will use index
                else:
                    logger.warning("No date column found, returning original data")
                    return filtered_data

            # Apply filters
            if date_col:
                if start_date:
                    filtered_data = filtered_data[filtered_data[date_col] >= pd.Timestamp(start_date)]
                if end_date:
                    filtered_data = filtered_data[filtered_data[date_col] <= pd.Timestamp(end_date)]
            else:
                # Filter by index
                if start_date:
                    filtered_data = filtered_data[filtered_data.index >= pd.Timestamp(start_date)]
                if end_date:
                    filtered_data = filtered_data[filtered_data.index <= pd.Timestamp(end_date)]

            logger.debug(
                f"Filtered data: {len(data)} -> {len(filtered_data)} records "
                f"(start={start_date}, end={end_date})"
            )

            return filtered_data

        except Exception as e:
            logger.error(f"Error filtering by date range: {str(e)}")
            raise ChartDataError(f"Failed to filter by date range: {str(e)}") from e

    def apply_indicators(
        self,
        data: pd.DataFrame,
        indicators: List[str],
        params: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Apply technical indicators to chart data.

        Args:
            data: DataFrame with OHLC data
            indicators: List of indicators to apply (max 3)
            params: Optional parameters for each indicator

        Returns:
            Dictionary with original data and indicator results

        Raises:
            ValueError: If more than 3 indicators requested
        """
        if len(indicators) > 3:
            raise ValueError("Maximum 3 indicators can be applied at once")

        if params is None:
            params = {}

        try:
            # Calculate indicators using indicator service
            indicator_results = self.indicator_service.calculate_multiple_indicators(
                data,
                indicators=indicators,
                params=params
            )

            # Prepare result
            result = {
                "data": data,
                "indicators": indicator_results
            }

            logger.debug(f"Applied indicators: {indicators}")

            return result

        except Exception as e:
            logger.error(f"Error applying indicators: {str(e)}")
            raise

    def add_annotation(
        self,
        data: Union[pd.DataFrame, Dict[str, Any]],
        annotation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add annotation to chart data.

        Args:
            data: Chart data (DataFrame or dict with data)
            annotation: Annotation configuration

        Returns:
            Dictionary with data and annotations
        """
        try:
            # Handle input format
            if isinstance(data, pd.DataFrame):
                result = {
                    "data": data,
                    "annotations": []
                }
            elif isinstance(data, dict):
                result = data.copy()
                if "annotations" not in result:
                    result["annotations"] = []
            else:
                raise ChartDataError("Invalid data format for annotation")

            # Validate annotation date if present
            if "date" in annotation:
                annotation_date = pd.Timestamp(annotation["date"])
                # Log warning if date is outside data range (but still add annotation)
                if isinstance(result.get("data"), pd.DataFrame):
                    df = result["data"]
                    if "date" in df.columns:
                        min_date = df["date"].min()
                        max_date = df["date"].max()
                        if annotation_date < min_date or annotation_date > max_date:
                            logger.warning(
                                f"Annotation date {annotation_date} is outside data range "
                                f"({min_date} to {max_date})"
                            )

            # Add annotation
            result["annotations"].append(annotation)

            logger.debug(f"Added annotation: type={annotation.get('type')}")

            return result

        except Exception as e:
            logger.error(f"Error adding annotation: {str(e)}")
            raise ChartDataError(f"Failed to add annotation: {str(e)}") from e

    def export_to_csv(
        self,
        data: Union[pd.DataFrame, Dict[str, Any]],
        columns: Optional[List[str]] = None
    ) -> str:
        """
        Export chart data to CSV format.

        Args:
            data: Chart data (DataFrame or dict)
            columns: Optional list of columns to export

        Returns:
            CSV string

        Raises:
            ChartDataError: If data is empty or export fails
        """
        try:
            # Handle input format
            if isinstance(data, dict):
                # Extract DataFrame from dict
                if "data" in data and isinstance(data["data"], pd.DataFrame):
                    df = data["data"]

                    # If indicators are present, try to merge them
                    if "indicators" in data:
                        for indicator_name, indicator_values in data["indicators"].items():
                            if isinstance(indicator_values, dict):
                                for key, values in indicator_values.items():
                                    if isinstance(values, (list, np.ndarray, pd.Series)):
                                        col_name = f"{indicator_name}_{key}" if indicator_name != "MA" else key
                                        df[col_name] = values
                else:
                    raise ChartDataError("Invalid data structure for CSV export")
            elif isinstance(data, pd.DataFrame):
                df = data
            else:
                raise ChartDataError("Data must be DataFrame or dict with 'data' key")

            # Check if data is empty
            if df.empty:
                raise ChartDataError("Cannot export empty data")

            # Select columns if specified
            if columns:
                available_cols = [col for col in columns if col in df.columns]
                if not available_cols:
                    logger.warning(f"None of the requested columns {columns} are available")
                    available_cols = df.columns.tolist()
                df = df[available_cols]

            # Convert to CSV string
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()

            logger.debug(f"Exported {len(df)} records to CSV")

            return csv_data

        except ChartDataError:
            raise
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            raise ChartDataError(f"Failed to export to CSV: {str(e)}") from e
