"""
Tests for Database Models

This module contains unit tests for SQLAlchemy models.
"""

import pytest
from datetime import datetime, timezone

from app.database.models import (
    Dataset,
    DataSource,
    DatasetStatus,
    ChartConfig,
    ChartType,
    UserPreferences,
    UserMode,
)


class TestDatasetModel:
    """Tests for Dataset model"""

    def test_dataset_creation(self):
        """Test creating a Dataset instance"""
        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL.value,
            file_path="/path/to/data.csv",
            status=DatasetStatus.VALID.value,
            row_count=1000,
            columns=["col1", "col2", "col3"],
            metadata={"description": "Test data"}
        )

        assert dataset.name == "Test Dataset"
        assert dataset.source == "local"
        assert dataset.status == "valid"
        assert dataset.row_count == 1000
        assert dataset.columns == ["col1", "col2", "col3"]
        assert dataset.metadata["description"] == "Test data"

    def test_dataset_repr(self):
        """Test Dataset string representation"""
        dataset = Dataset(
            id="test-id",
            name="Test Dataset",
            source=DataSource.LOCAL.value,
            file_path="/path/to/data.csv"
        )

        repr_str = repr(dataset)
        assert "Dataset" in repr_str
        assert "test-id" in repr_str
        assert "Test Dataset" in repr_str


class TestChartConfigModel:
    """Tests for ChartConfig model"""

    def test_chart_creation(self):
        """Test creating a ChartConfig instance"""
        chart = ChartConfig(
            name="Test Chart",
            chart_type=ChartType.KLINE.value,
            dataset_id="dataset-123",
            config={"x_axis": "date", "y_axis": "price"},
            description="Test chart description"
        )

        assert chart.name == "Test Chart"
        assert chart.chart_type == "kline"
        assert chart.dataset_id == "dataset-123"
        assert chart.config["x_axis"] == "date"
        assert chart.description == "Test chart description"

    def test_chart_repr(self):
        """Test ChartConfig string representation"""
        chart = ChartConfig(
            id="test-id",
            name="Test Chart",
            chart_type=ChartType.LINE.value,
            dataset_id="dataset-123",
            config={}
        )

        repr_str = repr(chart)
        assert "ChartConfig" in repr_str
        assert "test-id" in repr_str
        assert "Test Chart" in repr_str
        assert "line" in repr_str


class TestUserPreferencesModel:
    """Tests for UserPreferences model"""

    def test_user_preferences_creation(self):
        """Test creating a UserPreferences instance"""
        prefs = UserPreferences(
            user_id="user-123",
            mode=UserMode.EXPERT.value,
            language="zh",
            theme="dark",
            show_tooltips=False,
            completed_guides=["intro", "advanced"],
            settings={"auto_save": True}
        )

        assert prefs.user_id == "user-123"
        assert prefs.mode == "expert"
        assert prefs.language == "zh"
        assert prefs.theme == "dark"
        assert prefs.show_tooltips is False
        assert "intro" in prefs.completed_guides
        assert prefs.settings["auto_save"] is True

    def test_user_preferences_defaults(self):
        """Test UserPreferences default values"""
        prefs = UserPreferences(user_id="user-123")

        # Note: defaults are set at DB level, not in model
        assert prefs.user_id == "user-123"

    def test_user_preferences_repr(self):
        """Test UserPreferences string representation"""
        prefs = UserPreferences(
            id="test-id",
            user_id="user-123",
            mode=UserMode.BEGINNER.value
        )

        repr_str = repr(prefs)
        assert "UserPreferences" in repr_str
        assert "test-id" in repr_str
        assert "user-123" in repr_str
        assert "beginner" in repr_str


class TestEnums:
    """Tests for enum types"""

    def test_data_source_enum(self):
        """Test DataSource enum values"""
        assert DataSource.LOCAL.value == "local"
        assert DataSource.QLIB.value == "qlib"
        assert DataSource.THIRDPARTY.value == "thirdparty"

    def test_dataset_status_enum(self):
        """Test DatasetStatus enum values"""
        assert DatasetStatus.VALID.value == "valid"
        assert DatasetStatus.INVALID.value == "invalid"
        assert DatasetStatus.PENDING.value == "pending"

    def test_chart_type_enum(self):
        """Test ChartType enum values"""
        assert ChartType.KLINE.value == "kline"
        assert ChartType.LINE.value == "line"
        assert ChartType.BAR.value == "bar"
        assert ChartType.SCATTER.value == "scatter"
        assert ChartType.HEATMAP.value == "heatmap"

    def test_user_mode_enum(self):
        """Test UserMode enum values"""
        assert UserMode.BEGINNER.value == "beginner"
        assert UserMode.EXPERT.value == "expert"
