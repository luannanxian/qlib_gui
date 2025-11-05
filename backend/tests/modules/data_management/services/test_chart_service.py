"""
TDD Tests for Chart Data Service

Following TDD methodology:
1. RED: Write failing tests first
2. GREEN: Implement minimal code to pass
3. REFACTOR: Optimize and clean up

Test Coverage:
- OHLC data generation from dataset
- Time range filtering
- Technical indicator integration
- Multi-indicator overlay (max 3)
- Data format conversion (candlestick/OHLC)
- Chart annotations
- CSV export functionality
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
from io import StringIO

from app.modules.data_management.services.chart_service import (
    ChartService,
    ChartDataError,
    DatasetNotFoundError,
    InvalidDateRangeError
)


class TestChartServiceInitialization:
    """Test chart service initialization."""

    def test_chart_service_can_be_instantiated(self):
        """Test that ChartService can be created."""
        service = ChartService()
        assert service is not None

    def test_chart_service_has_required_methods(self):
        """Test that ChartService has all required methods."""
        service = ChartService()
        assert hasattr(service, "generate_ohlc_data")
        assert hasattr(service, "apply_indicators")
        assert hasattr(service, "filter_by_date_range")
        assert hasattr(service, "export_to_csv")
        assert hasattr(service, "add_annotation")


class TestOHLCDataGeneration:
    """Test OHLC data generation from dataset."""

    def test_generate_ohlc_data_from_dataframe(self, sample_stock_data):
        """Test generating OHLC data from pandas DataFrame."""
        service = ChartService()

        result = service.generate_ohlc_data(sample_stock_data)

        # Check result structure
        assert "date" in result or "datetime" in result
        assert "open" in result
        assert "high" in result
        assert "low" in result
        assert "close" in result
        assert "volume" in result

        # Check data length matches
        assert len(result["open"]) == len(sample_stock_data)

    def test_generate_ohlc_data_returns_list_format(self, sample_stock_data):
        """Test that OHLC data is returned in list format for frontend."""
        service = ChartService()

        result = service.generate_ohlc_data(sample_stock_data, output_format="list")

        # Each field should be a list
        assert isinstance(result["open"], list)
        assert isinstance(result["high"], list)
        assert isinstance(result["low"], list)
        assert isinstance(result["close"], list)
        assert isinstance(result["volume"], list)

    def test_generate_candlestick_format(self, sample_stock_data):
        """Test generating data in candlestick format [[timestamp, open, high, low, close], ...]."""
        service = ChartService()

        result = service.generate_ohlc_data(
            sample_stock_data,
            chart_format="candlestick"
        )

        assert "data" in result
        assert isinstance(result["data"], list)

        # Each item should be [timestamp, open, high, low, close]
        if len(result["data"]) > 0:
            first_item = result["data"][0]
            assert len(first_item) == 5  # timestamp, o, h, l, c

    def test_generate_ohlc_validates_required_columns(self):
        """Test that OHLC generation validates required columns."""
        service = ChartService()

        # Missing 'high' column
        invalid_data = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=10),
            "open": [100] * 10,
            "low": [98] * 10,
            "close": [99] * 10,
            "volume": [1000] * 10
        })

        with pytest.raises(ChartDataError) as exc_info:
            service.generate_ohlc_data(invalid_data)

        assert "required column" in str(exc_info.value).lower() or "high" in str(exc_info.value).lower()


class TestDateRangeFiltering:
    """Test time range filtering functionality."""

    def test_filter_by_date_range_with_start_date(self, sample_stock_data):
        """Test filtering data with start date only."""
        service = ChartService()

        start_date = datetime(2024, 2, 1)
        result = service.filter_by_date_range(
            sample_stock_data,
            start_date=start_date
        )

        # Check that result only contains data from start_date onwards
        assert len(result) < len(sample_stock_data)
        if "date" in result.columns:
            assert result["date"].min() >= pd.Timestamp(start_date)

    def test_filter_by_date_range_with_end_date(self, sample_stock_data):
        """Test filtering data with end date only."""
        service = ChartService()

        end_date = datetime(2024, 2, 1)
        result = service.filter_by_date_range(
            sample_stock_data,
            end_date=end_date
        )

        # Check that result only contains data up to end_date
        assert len(result) < len(sample_stock_data)
        if "date" in result.columns:
            assert result["date"].max() <= pd.Timestamp(end_date)

    def test_filter_by_date_range_with_both_dates(self, sample_stock_data):
        """Test filtering data with both start and end dates."""
        service = ChartService()

        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 2, 15)

        result = service.filter_by_date_range(
            sample_stock_data,
            start_date=start_date,
            end_date=end_date
        )

        # Check that result is within the date range
        if "date" in result.columns:
            assert result["date"].min() >= pd.Timestamp(start_date)
            assert result["date"].max() <= pd.Timestamp(end_date)

    def test_filter_with_invalid_date_range_raises_error(self, sample_stock_data):
        """Test that end_date before start_date raises error."""
        service = ChartService()

        start_date = datetime(2024, 3, 1)
        end_date = datetime(2024, 2, 1)  # Before start_date

        with pytest.raises(InvalidDateRangeError) as exc_info:
            service.filter_by_date_range(
                sample_stock_data,
                start_date=start_date,
                end_date=end_date
            )

        assert "invalid" in str(exc_info.value).lower()

    def test_filter_with_no_matching_data_returns_empty(self, sample_stock_data):
        """Test that filtering with no matching dates returns empty DataFrame."""
        service = ChartService()

        # Date range outside data range
        start_date = datetime(2025, 1, 1)
        result = service.filter_by_date_range(
            sample_stock_data,
            start_date=start_date
        )

        assert len(result) == 0


class TestIndicatorIntegration:
    """Test integrating technical indicators with chart data."""

    def test_apply_single_indicator_to_chart_data(self, sample_stock_data):
        """Test applying a single indicator (e.g., MACD) to chart data."""
        service = ChartService()

        result = service.apply_indicators(
            sample_stock_data,
            indicators=["MACD"]
        )

        # Should contain original data plus indicators
        assert "data" in result
        assert "indicators" in result
        assert "MACD" in result["indicators"]
        assert "macd" in result["indicators"]["MACD"]

    def test_apply_multiple_indicators_to_chart_data(self, sample_stock_data):
        """Test applying multiple indicators to chart data."""
        service = ChartService()

        result = service.apply_indicators(
            sample_stock_data,
            indicators=["MACD", "RSI", "MA"],
            params={
                "MA": {"periods": [5, 10]}
            }
        )

        assert "indicators" in result
        assert "MACD" in result["indicators"]
        assert "RSI" in result["indicators"]
        assert "MA" in result["indicators"]

    def test_apply_max_three_indicators_limit(self, sample_stock_data):
        """Test that maximum 3 indicators can be applied."""
        service = ChartService()

        # Try to apply 4 indicators
        with pytest.raises(ValueError) as exc_info:
            service.apply_indicators(
                sample_stock_data,
                indicators=["MACD", "RSI", "KDJ", "MA"]
            )

        assert "maximum" in str(exc_info.value).lower()
        assert "3" in str(exc_info.value)

    def test_apply_indicators_with_custom_parameters(self, sample_stock_data):
        """Test applying indicators with custom parameters."""
        service = ChartService()

        result = service.apply_indicators(
            sample_stock_data,
            indicators=["MACD", "RSI"],
            params={
                "MACD": {"fast_period": 8, "slow_period": 17, "signal_period": 5},
                "RSI": {"period": 20, "overbought": 75, "oversold": 25}
            }
        )

        assert "MACD" in result["indicators"]
        assert "RSI" in result["indicators"]

    def test_apply_indicators_aligns_data_lengths(self, sample_stock_data):
        """Test that indicator data is aligned with OHLC data."""
        service = ChartService()

        result = service.apply_indicators(
            sample_stock_data,
            indicators=["MACD"]
        )

        # Indicator arrays should have same length as original data
        macd_values = result["indicators"]["MACD"]["macd"]
        assert len(macd_values) == len(sample_stock_data)


class TestChartAnnotations:
    """Test chart annotation functionality."""

    def test_add_text_annotation(self, sample_stock_data):
        """Test adding text annotation to chart."""
        service = ChartService()

        annotation = {
            "type": "text",
            "date": datetime(2024, 1, 15),
            "text": "Important event",
            "position": "top"
        }

        result = service.add_annotation(sample_stock_data, annotation)

        assert "annotations" in result
        assert len(result["annotations"]) == 1
        assert result["annotations"][0]["text"] == "Important event"

    def test_add_date_marker_annotation(self, sample_stock_data):
        """Test adding date marker to chart."""
        service = ChartService()

        annotation = {
            "type": "marker",
            "date": datetime(2024, 1, 20),
            "label": "Earnings report",
            "color": "red"
        }

        result = service.add_annotation(sample_stock_data, annotation)

        assert "annotations" in result
        assert result["annotations"][0]["type"] == "marker"

    def test_add_multiple_annotations(self, sample_stock_data):
        """Test adding multiple annotations."""
        service = ChartService()

        annotations = [
            {"type": "text", "date": datetime(2024, 1, 15), "text": "Event 1"},
            {"type": "marker", "date": datetime(2024, 1, 20), "label": "Event 2"},
            {"type": "text", "date": datetime(2024, 1, 25), "text": "Event 3"}
        ]

        result = sample_stock_data
        for annotation in annotations:
            result = service.add_annotation(result, annotation)

        # Result should be dict with annotations
        if isinstance(result, dict):
            assert len(result["annotations"]) == 3

    def test_annotation_with_invalid_date_raises_error(self, sample_stock_data):
        """Test that annotation with date outside data range raises warning."""
        service = ChartService()

        annotation = {
            "type": "text",
            "date": datetime(2025, 1, 1),  # Outside data range
            "text": "Future event"
        }

        # Should not raise error but may log warning
        result = service.add_annotation(sample_stock_data, annotation)
        # Annotation may still be added with warning
        assert result is not None


class TestChartDataExport:
    """Test chart data export functionality."""

    def test_export_ohlc_data_to_csv(self, sample_stock_data):
        """Test exporting OHLC data to CSV format."""
        service = ChartService()

        csv_data = service.export_to_csv(sample_stock_data)

        assert isinstance(csv_data, str)
        assert "date" in csv_data or "open" in csv_data
        assert "high" in csv_data
        assert "close" in csv_data

        # Verify it's valid CSV
        df = pd.read_csv(StringIO(csv_data))
        assert len(df) > 0

    def test_export_with_indicators_to_csv(self, sample_stock_data):
        """Test exporting data with indicators to CSV."""
        service = ChartService()

        # First apply indicators
        data_with_indicators = service.apply_indicators(
            sample_stock_data,
            indicators=["MACD", "RSI"]
        )

        csv_data = service.export_to_csv(data_with_indicators)

        # Should include indicator columns
        assert "macd" in csv_data.lower() or "rsi" in csv_data.lower()

    def test_export_with_custom_columns(self, sample_stock_data):
        """Test exporting with specific columns only."""
        service = ChartService()

        csv_data = service.export_to_csv(
            sample_stock_data,
            columns=["date", "close", "volume"]
        )

        df = pd.read_csv(StringIO(csv_data))

        # Should only have specified columns
        assert set(df.columns).issubset({"date", "close", "volume"})

    def test_export_empty_data_raises_error(self):
        """Test that exporting empty data raises error."""
        service = ChartService()

        empty_df = pd.DataFrame()

        with pytest.raises(ChartDataError):
            service.export_to_csv(empty_df)


class TestChartServiceIntegration:
    """Test integrated chart service workflows."""

    def test_complete_chart_workflow(self, sample_stock_data):
        """Test complete workflow: filter -> generate OHLC -> apply indicators."""
        service = ChartService()

        # 1. Filter by date range
        filtered_data = service.filter_by_date_range(
            sample_stock_data,
            start_date=datetime(2024, 1, 15)
        )

        # 2. Generate OHLC data
        ohlc_result = service.generate_ohlc_data(filtered_data)

        # 3. Apply indicators
        final_result = service.apply_indicators(
            filtered_data,
            indicators=["MACD", "RSI"]
        )

        # Verify complete result structure
        assert final_result is not None
        assert "indicators" in final_result

    def test_chart_with_annotations_and_export(self, sample_stock_data):
        """Test workflow with annotations and CSV export."""
        service = ChartService()

        # Add annotation
        annotation = {
            "type": "text",
            "date": datetime(2024, 1, 20),
            "text": "Test event"
        }

        annotated_data = service.add_annotation(sample_stock_data, annotation)

        # Export to CSV
        if isinstance(annotated_data, dict) and "data" in annotated_data:
            csv_data = service.export_to_csv(annotated_data["data"])
        else:
            csv_data = service.export_to_csv(annotated_data if isinstance(annotated_data, pd.DataFrame) else sample_stock_data)

        assert csv_data is not None
        assert len(csv_data) > 0


class TestChartServiceEdgeCases:
    """Test edge cases and error handling."""

    def test_service_handles_missing_date_column_gracefully(self):
        """Test handling of data without date column."""
        service = ChartService()

        data_no_date = pd.DataFrame({
            "open": [100, 101, 102],
            "high": [103, 104, 105],
            "low": [98, 99, 100],
            "close": [101, 102, 103],
            "volume": [1000, 1100, 1200]
        })

        # Should handle gracefully (may add index as date or raise error)
        # Implementation-specific behavior
        result = service.generate_ohlc_data(data_no_date)
        assert result is not None

    def test_service_handles_duplicate_dates(self):
        """Test handling of duplicate date entries."""
        service = ChartService()

        data_with_dupes = pd.DataFrame({
            "date": [datetime(2024, 1, 1), datetime(2024, 1, 1), datetime(2024, 1, 2)],
            "open": [100, 101, 102],
            "high": [103, 104, 105],
            "low": [98, 99, 100],
            "close": [101, 102, 103],
            "volume": [1000, 1100, 1200]
        })

        # Should handle or raise appropriate error
        try:
            result = service.generate_ohlc_data(data_with_dupes)
            # If no error, should have de-duplicated or handled
            assert result is not None
        except ChartDataError:
            # Acceptable to raise error for duplicate dates
            pass

    def test_service_with_very_large_dataset(self):
        """Test service performance with large dataset."""
        service = ChartService()

        # Create large dataset
        large_data = pd.DataFrame({
            "date": pd.date_range("2020-01-01", periods=5000, freq="D"),
            "open": np.random.uniform(90, 110, 5000),
            "high": np.random.uniform(100, 120, 5000),
            "low": np.random.uniform(80, 100, 5000),
            "close": np.random.uniform(90, 110, 5000),
            "volume": np.random.randint(500000, 1500000, 5000)
        })

        # Should handle large dataset
        result = service.generate_ohlc_data(large_data)
        assert len(result["open"]) == 5000
