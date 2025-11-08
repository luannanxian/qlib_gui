"""Tests for data serialization utilities"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, date

from app.modules.data_management.utils.serialization import (
    convert_numpy_to_native,
    convert_datetime_fields,
    prepare_chart_data_for_serialization,
    prepare_annotation_for_storage,
)


class TestConvertNumpyToNative:
    """Test numpy to native type conversion"""

    def test_convert_numpy_array(self):
        """Test converting numpy array to list"""
        arr = np.array([1, 2, 3, 4, 5])
        result = convert_numpy_to_native(arr)
        assert isinstance(result, list)
        assert result == [1, 2, 3, 4, 5]

    def test_convert_numpy_scalars(self):
        """Test converting numpy scalars"""
        assert isinstance(convert_numpy_to_native(np.int64(42)), int)
        assert convert_numpy_to_native(np.int64(42)) == 42

        assert isinstance(convert_numpy_to_native(np.float64(3.14)), float)
        assert abs(convert_numpy_to_native(np.float64(3.14)) - 3.14) < 0.001

        assert isinstance(convert_numpy_to_native(np.bool_(True)), bool)
        assert convert_numpy_to_native(np.bool_(True)) is True

    def test_convert_pandas_timestamp(self):
        """Test converting pandas Timestamp"""
        ts = pd.Timestamp("2024-01-01 12:00:00")
        result = convert_numpy_to_native(ts)
        assert isinstance(result, str)
        assert "2024-01-01" in result

    def test_convert_datetime(self):
        """Test converting datetime objects"""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = convert_numpy_to_native(dt)
        assert isinstance(result, str)
        assert "2024-01-01" in result

    def test_convert_nested_dict(self):
        """Test converting nested dictionary with numpy types"""
        data = {
            "values": np.array([1, 2, 3]),
            "timestamp": datetime(2024, 1, 1),
            "nested": {
                "data": np.array([4, 5, 6]),
                "count": np.int64(10),
            },
        }
        result = convert_numpy_to_native(data)

        assert isinstance(result["values"], list)
        assert result["values"] == [1, 2, 3]
        assert isinstance(result["timestamp"], str)
        assert isinstance(result["nested"]["data"], list)
        assert isinstance(result["nested"]["count"], int)

    def test_convert_list_with_numpy(self):
        """Test converting list containing numpy types"""
        data = [np.int64(1), np.float64(2.5), np.array([3, 4])]
        result = convert_numpy_to_native(data)

        assert isinstance(result[0], int)
        assert isinstance(result[1], float)
        assert isinstance(result[2], list)

    def test_convert_pandas_series(self):
        """Test converting pandas Series"""
        series = pd.Series([1, 2, 3, 4, 5])
        result = convert_numpy_to_native(series)
        assert isinstance(result, list)
        assert result == [1, 2, 3, 4, 5]


class TestConvertDatetimeFields:
    """Test datetime field conversion"""

    def test_convert_all_datetime_fields(self):
        """Test converting all datetime fields in dict"""
        data = {
            "created_at": datetime(2024, 1, 1, 10, 0, 0),
            "updated_at": datetime(2024, 1, 2, 11, 0, 0),
            "name": "test",
            "count": 42,
        }
        result = convert_datetime_fields(data)

        assert isinstance(result["created_at"], str)
        assert isinstance(result["updated_at"], str)
        assert result["name"] == "test"
        assert result["count"] == 42

    def test_convert_specific_fields(self):
        """Test converting only specified fields"""
        data = {
            "date": datetime(2024, 1, 1),
            "created_at": datetime(2024, 1, 2),
            "name": "test",
        }
        result = convert_datetime_fields(data, fields=["date"])

        assert isinstance(result["date"], str)
        assert isinstance(result["created_at"], datetime)

    def test_convert_nested_datetime(self):
        """Test converting nested datetime fields"""
        data = {
            "annotation": {
                "date": datetime(2024, 1, 1),
                "text": "test",
            }
        }
        result = convert_datetime_fields(data)

        assert isinstance(result["annotation"]["date"], str)
        assert result["annotation"]["text"] == "test"


class TestPrepareChartDataForSerialization:
    """Test chart data preparation for serialization"""

    def test_prepare_ohlc_data(self):
        """Test preparing OHLC data with numpy arrays"""
        data = {
            "open": np.array([100.0, 101.0, 102.0]),
            "high": np.array([105.0, 106.0, 107.0]),
            "low": np.array([95.0, 96.0, 97.0]),
            "close": np.array([103.0, 104.0, 105.0]),
            "date": [datetime(2024, 1, 1), datetime(2024, 1, 2), datetime(2024, 1, 3)],
        }
        result = prepare_chart_data_for_serialization(data)

        # All numpy arrays should be converted to lists
        assert isinstance(result["open"], list)
        assert isinstance(result["high"], list)
        assert isinstance(result["low"], list)
        assert isinstance(result["close"], list)

        # All datetimes should be converted to strings
        assert all(isinstance(d, str) for d in result["date"])

    def test_prepare_indicator_data(self):
        """Test preparing indicator data"""
        data = {
            "MACD": {
                "macd": np.array([1.5, 2.0, 2.5]),
                "signal": np.array([1.0, 1.5, 2.0]),
                "histogram": np.array([0.5, 0.5, 0.5]),
            },
            "RSI": {
                "rsi": np.array([65.0, 70.0, 60.0]),
            },
        }
        result = prepare_chart_data_for_serialization(data)

        # All numpy arrays in nested dicts should be converted
        assert isinstance(result["MACD"]["macd"], list)
        assert isinstance(result["MACD"]["signal"], list)
        assert isinstance(result["RSI"]["rsi"], list)


class TestPrepareAnnotationForStorage:
    """Test annotation preparation for storage"""

    def test_prepare_text_annotation(self):
        """Test preparing text annotation"""
        annotation = {
            "type": "text",
            "date": datetime(2024, 1, 1, 12, 0, 0),
            "text": "Important event",
            "position": "top",
        }
        result = prepare_annotation_for_storage(annotation)

        assert isinstance(result["date"], str)
        assert "2024-01-01" in result["date"]
        assert result["type"] == "text"
        assert result["text"] == "Important event"

    def test_prepare_marker_annotation(self):
        """Test preparing marker annotation"""
        annotation = {
            "type": "marker",
            "date": datetime(2024, 1, 1),
            "label": "Buy signal",
            "color": "green",
        }
        result = prepare_annotation_for_storage(annotation)

        assert isinstance(result["date"], str)
        assert result["label"] == "Buy signal"
        assert result["color"] == "green"

    def test_preserve_non_datetime_fields(self):
        """Test that non-datetime fields are preserved"""
        annotation = {
            "type": "text",
            "date": datetime(2024, 1, 1),
            "text": "Test",
            "extra_field": "should be preserved",
        }
        result = prepare_annotation_for_storage(annotation)

        assert result["extra_field"] == "should be preserved"
        assert result["text"] == "Test"
