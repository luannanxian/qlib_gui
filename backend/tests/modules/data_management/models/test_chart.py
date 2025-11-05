"""Tests for Chart models.

Following TDD approach - these tests are written BEFORE implementation.
"""

import pytest
from datetime import datetime


class TestChartType:
    """Test ChartType enum."""

    def test_chart_type_enum_values(self):
        """Test ChartType enum has correct values."""
        from app.modules.data_management.models.chart import ChartType

        assert ChartType.KLINE == "kline"
        assert ChartType.LINE == "line"
        assert ChartType.BAR == "bar"
        assert ChartType.SCATTER == "scatter"
        assert ChartType.HEATMAP == "heatmap"

    def test_chart_type_is_enum(self):
        """Test ChartType is an Enum."""
        from app.modules.data_management.models.chart import ChartType
        from enum import Enum

        assert issubclass(ChartType, Enum)


class TestChartConfig:
    """Test ChartConfig model."""

    def test_chart_config_creation(self):
        """Test ChartConfig model creation with minimal fields."""
        from app.modules.data_management.models.chart import ChartConfig, ChartType

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.LINE,
            dataset_id="dataset-123"
        )

        assert chart.name == "Test Chart"
        assert chart.chart_type == ChartType.LINE
        assert chart.dataset_id == "dataset-123"
        assert chart.config == {}  # Default value

    def test_chart_config_with_all_fields(self):
        """Test ChartConfig model with all fields."""
        from app.modules.data_management.models.chart import ChartConfig, ChartType

        config_data = {
            "x_axis": "date",
            "y_axis": "close",
            "color": "blue",
            "width": 800,
            "height": 600
        }

        chart = ChartConfig(
            name="Full Chart",
            chart_type=ChartType.KLINE,
            dataset_id="dataset-456",
            config=config_data
        )

        assert chart.name == "Full Chart"
        assert chart.chart_type == ChartType.KLINE
        assert chart.dataset_id == "dataset-456"
        assert chart.config == config_data

    def test_chart_config_has_timestamps(self):
        """Test ChartConfig has created_at and updated_at timestamps."""
        from app.modules.data_management.models.chart import ChartConfig, ChartType

        chart = ChartConfig(
            name="Test",
            chart_type=ChartType.BAR,
            dataset_id="dataset-123"
        )

        assert hasattr(chart, "created_at")
        assert hasattr(chart, "updated_at")
        assert isinstance(chart.created_at, datetime)
        assert isinstance(chart.updated_at, datetime)

    def test_chart_config_id_generation(self):
        """Test ChartConfig generates unique ID."""
        from app.modules.data_management.models.chart import ChartConfig, ChartType

        chart1 = ChartConfig(name="Chart 1", chart_type=ChartType.LINE, dataset_id="dataset-1")
        chart2 = ChartConfig(name="Chart 2", chart_type=ChartType.LINE, dataset_id="dataset-2")

        assert hasattr(chart1, "id")
        assert hasattr(chart2, "id")
        assert chart1.id != chart2.id

    def test_chart_config_str_representation(self):
        """Test ChartConfig string representation."""
        from app.modules.data_management.models.chart import ChartConfig, ChartType

        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.SCATTER,
            dataset_id="dataset-123"
        )

        str_repr = str(chart)
        assert "Test Chart" in str_repr
        assert "scatter" in str_repr

    def test_chart_config_chart_type_validation(self):
        """Test ChartConfig chart_type must be valid ChartType."""
        from app.modules.data_management.models.chart import ChartConfig, ChartType
        from pydantic import ValidationError

        # Valid chart_type should work
        chart = ChartConfig(
            name="Test",
            chart_type=ChartType.HEATMAP,
            dataset_id="dataset-123"
        )
        assert chart.chart_type == ChartType.HEATMAP

        # Invalid chart_type should raise ValidationError
        with pytest.raises(ValidationError):
            ChartConfig(
                name="Test",
                chart_type="invalid_type",
                dataset_id="dataset-123"
            )

    def test_chart_config_name_required(self):
        """Test ChartConfig name is required."""
        from app.modules.data_management.models.chart import ChartConfig, ChartType
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ChartConfig(chart_type=ChartType.LINE, dataset_id="dataset-123")

    def test_chart_config_chart_type_required(self):
        """Test ChartConfig chart_type is required."""
        from app.modules.data_management.models.chart import ChartConfig
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ChartConfig(name="Test", dataset_id="dataset-123")

    def test_chart_config_dataset_id_required(self):
        """Test ChartConfig dataset_id is required."""
        from app.modules.data_management.models.chart import ChartConfig, ChartType
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ChartConfig(name="Test", chart_type=ChartType.LINE)

    def test_chart_config_with_kline_specific_config(self):
        """Test ChartConfig with K-line specific configuration."""
        from app.modules.data_management.models.chart import ChartConfig, ChartType

        kline_config = {
            "open_field": "open",
            "high_field": "high",
            "low_field": "low",
            "close_field": "close",
            "volume_field": "volume",
            "show_volume": True,
            "show_ma": True,
            "ma_periods": [5, 10, 20, 30]
        }

        chart = ChartConfig(
            name="K-Line Chart",
            chart_type=ChartType.KLINE,
            dataset_id="dataset-stock",
            config=kline_config
        )

        assert chart.config["open_field"] == "open"
        assert chart.config["show_ma"] is True
        assert chart.config["ma_periods"] == [5, 10, 20, 30]

    def test_chart_config_with_indicator_config(self):
        """Test ChartConfig with technical indicator configuration."""
        from app.modules.data_management.models.chart import ChartConfig, ChartType

        indicator_config = {
            "indicators": [
                {"type": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}},
                {"type": "RSI", "params": {"period": 14}},
                {"type": "BOLL", "params": {"period": 20, "std": 2}}
            ]
        }

        chart = ChartConfig(
            name="Indicator Chart",
            chart_type=ChartType.LINE,
            dataset_id="dataset-stock",
            config=indicator_config
        )

        assert len(chart.config["indicators"]) == 3
        assert chart.config["indicators"][0]["type"] == "MACD"
