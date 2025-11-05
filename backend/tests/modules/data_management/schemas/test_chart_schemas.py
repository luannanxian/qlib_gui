"""Tests for Chart schemas.

Following TDD approach - these tests are written BEFORE implementation.
"""

import pytest


class TestChartConfigCreate:
    """Test ChartConfigCreate schema."""

    def test_chart_config_create_schema(self):
        """Test ChartConfigCreate schema creation."""
        from app.modules.data_management.schemas.chart import ChartConfigCreate
        from app.modules.data_management.models.chart import ChartType

        schema = ChartConfigCreate(
            name="Test Chart",
            chart_type=ChartType.LINE,
            dataset_id="dataset-123",
            config={"x": "date", "y": "value"}
        )

        assert schema.name == "Test Chart"
        assert schema.chart_type == ChartType.LINE
        assert schema.dataset_id == "dataset-123"
        assert schema.config == {"x": "date", "y": "value"}

    def test_chart_config_create_minimal(self):
        """Test ChartConfigCreate with minimal fields."""
        from app.modules.data_management.schemas.chart import ChartConfigCreate
        from app.modules.data_management.models.chart import ChartType

        schema = ChartConfigCreate(
            name="Minimal Chart",
            chart_type=ChartType.BAR,
            dataset_id="dataset-456"
        )

        assert schema.name == "Minimal Chart"
        assert schema.chart_type == ChartType.BAR
        assert schema.dataset_id == "dataset-456"
        assert schema.config == {}


class TestChartConfigUpdate:
    """Test ChartConfigUpdate schema."""

    def test_chart_config_update_all_fields(self):
        """Test ChartConfigUpdate with all fields."""
        from app.modules.data_management.schemas.chart import ChartConfigUpdate
        from app.modules.data_management.models.chart import ChartType

        schema = ChartConfigUpdate(
            name="Updated Chart",
            chart_type=ChartType.SCATTER,
            config={"updated": True}
        )

        assert schema.name == "Updated Chart"
        assert schema.chart_type == ChartType.SCATTER
        assert schema.config == {"updated": True}

    def test_chart_config_update_partial_fields(self):
        """Test ChartConfigUpdate with partial fields."""
        from app.modules.data_management.schemas.chart import ChartConfigUpdate

        schema = ChartConfigUpdate(name="New Name Only")

        assert schema.name == "New Name Only"
        assert schema.chart_type is None
        assert schema.config is None

    def test_chart_config_update_all_optional(self):
        """Test ChartConfigUpdate all fields are optional."""
        from app.modules.data_management.schemas.chart import ChartConfigUpdate

        schema = ChartConfigUpdate()

        assert schema.name is None
        assert schema.chart_type is None
        assert schema.config is None


class TestChartConfigResponse:
    """Test ChartConfigResponse schema."""

    def test_chart_config_response_schema(self):
        """Test ChartConfigResponse schema creation."""
        from app.modules.data_management.schemas.chart import ChartConfigResponse
        from app.modules.data_management.models.chart import ChartType
        from datetime import datetime

        now = datetime.utcnow()

        schema = ChartConfigResponse(
            id="chart-123",
            name="Response Chart",
            chart_type=ChartType.KLINE,
            dataset_id="dataset-789",
            config={"kline": "config"},
            created_at=now,
            updated_at=now
        )

        assert schema.id == "chart-123"
        assert schema.name == "Response Chart"
        assert schema.chart_type == ChartType.KLINE
        assert schema.dataset_id == "dataset-789"
        assert schema.config == {"kline": "config"}
        assert schema.created_at == now
        assert schema.updated_at == now


class TestChartConfigListResponse:
    """Test ChartConfigListResponse schema."""

    def test_chart_config_list_response_schema(self):
        """Test ChartConfigListResponse schema creation."""
        from app.modules.data_management.schemas.chart import ChartConfigListResponse, ChartConfigResponse
        from app.modules.data_management.models.chart import ChartType
        from datetime import datetime

        now = datetime.utcnow()

        charts = [
            ChartConfigResponse(
                id="1",
                name="Chart 1",
                chart_type=ChartType.LINE,
                dataset_id="dataset-1",
                config={},
                created_at=now,
                updated_at=now
            ),
            ChartConfigResponse(
                id="2",
                name="Chart 2",
                chart_type=ChartType.BAR,
                dataset_id="dataset-2",
                config={},
                created_at=now,
                updated_at=now
            )
        ]

        schema = ChartConfigListResponse(total=2, items=charts)

        assert schema.total == 2
        assert len(schema.items) == 2
        assert schema.items[0].name == "Chart 1"
        assert schema.items[1].name == "Chart 2"

    def test_chart_config_list_response_empty(self):
        """Test ChartConfigListResponse with empty list."""
        from app.modules.data_management.schemas.chart import ChartConfigListResponse

        schema = ChartConfigListResponse(total=0, items=[])

        assert schema.total == 0
        assert schema.items == []
