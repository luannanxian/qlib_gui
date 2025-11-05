"""Tests for Dataset schemas.

Following TDD approach - these tests are written BEFORE implementation.
"""

import pytest


class TestDatasetCreate:
    """Test DatasetCreate schema."""

    def test_dataset_create_schema(self):
        """Test DatasetCreate schema creation."""
        from app.modules.data_management.schemas.dataset import DatasetCreate
        from app.modules.data_management.models.dataset import DataSource

        schema = DatasetCreate(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv"
        )

        assert schema.name == "Test Dataset"
        assert schema.source == DataSource.LOCAL
        assert schema.file_path == "/data/test.csv"

    def test_dataset_create_name_required(self):
        """Test DatasetCreate name is required."""
        from app.modules.data_management.schemas.dataset import DatasetCreate
        from app.modules.data_management.models.dataset import DataSource
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            DatasetCreate(source=DataSource.LOCAL, file_path="/data/test.csv")

    def test_dataset_create_source_required(self):
        """Test DatasetCreate source is required."""
        from app.modules.data_management.schemas.dataset import DatasetCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            DatasetCreate(name="Test", file_path="/data/test.csv")

    def test_dataset_create_file_path_required(self):
        """Test DatasetCreate file_path is required."""
        from app.modules.data_management.schemas.dataset import DatasetCreate
        from app.modules.data_management.models.dataset import DataSource
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            DatasetCreate(name="Test", source=DataSource.LOCAL)


class TestDatasetUpdate:
    """Test DatasetUpdate schema."""

    def test_dataset_update_schema_all_fields(self):
        """Test DatasetUpdate schema with all fields."""
        from app.modules.data_management.schemas.dataset import DatasetUpdate
        from app.modules.data_management.models.dataset import DatasetStatus

        schema = DatasetUpdate(
            name="Updated Name",
            status=DatasetStatus.VALID,
            row_count=1000,
            columns=["col1", "col2"],
            metadata={"version": "2.0"}
        )

        assert schema.name == "Updated Name"
        assert schema.status == DatasetStatus.VALID
        assert schema.row_count == 1000
        assert schema.columns == ["col1", "col2"]
        assert schema.metadata == {"version": "2.0"}

    def test_dataset_update_schema_partial_fields(self):
        """Test DatasetUpdate schema with partial fields."""
        from app.modules.data_management.schemas.dataset import DatasetUpdate
        from app.modules.data_management.models.dataset import DatasetStatus

        schema = DatasetUpdate(status=DatasetStatus.VALID)

        assert schema.status == DatasetStatus.VALID
        assert schema.name is None
        assert schema.row_count is None
        assert schema.columns is None
        assert schema.metadata is None

    def test_dataset_update_all_fields_optional(self):
        """Test DatasetUpdate all fields are optional."""
        from app.modules.data_management.schemas.dataset import DatasetUpdate

        schema = DatasetUpdate()

        assert schema.name is None
        assert schema.status is None
        assert schema.row_count is None
        assert schema.columns is None
        assert schema.metadata is None


class TestDatasetResponse:
    """Test DatasetResponse schema."""

    def test_dataset_response_schema(self):
        """Test DatasetResponse schema creation."""
        from app.modules.data_management.schemas.dataset import DatasetResponse
        from app.modules.data_management.models.dataset import DataSource, DatasetStatus
        from datetime import datetime

        now = datetime.utcnow()

        schema = DatasetResponse(
            id="dataset-123",
            name="Test Dataset",
            source=DataSource.QLIB,
            file_path="/data/qlib.csv",
            status=DatasetStatus.VALID,
            row_count=500,
            columns=["open", "close"],
            metadata={"info": "test"},
            created_at=now,
            updated_at=now
        )

        assert schema.id == "dataset-123"
        assert schema.name == "Test Dataset"
        assert schema.source == DataSource.QLIB
        assert schema.file_path == "/data/qlib.csv"
        assert schema.status == DatasetStatus.VALID
        assert schema.row_count == 500
        assert schema.columns == ["open", "close"]
        assert schema.metadata == {"info": "test"}
        assert schema.created_at == now
        assert schema.updated_at == now

    def test_dataset_response_from_model(self):
        """Test DatasetResponse creation from Dataset model."""
        from app.modules.data_management.schemas.dataset import DatasetResponse
        from app.modules.data_management.models.dataset import Dataset, DataSource, DatasetStatus

        dataset = Dataset(
            name="Model Dataset",
            source=DataSource.LOCAL,
            file_path="/data/local.csv",
            status=DatasetStatus.PENDING,
            row_count=100
        )

        schema = DatasetResponse(
            id=dataset.id,
            name=dataset.name,
            source=dataset.source,
            file_path=dataset.file_path,
            status=dataset.status,
            row_count=dataset.row_count,
            columns=dataset.columns,
            metadata=dataset.metadata,
            created_at=dataset.created_at,
            updated_at=dataset.updated_at
        )

        assert schema.id == dataset.id
        assert schema.name == dataset.name
        assert schema.source == dataset.source
        assert schema.status == dataset.status


class TestDatasetListResponse:
    """Test DatasetListResponse schema."""

    def test_dataset_list_response_schema(self):
        """Test DatasetListResponse schema creation."""
        from app.modules.data_management.schemas.dataset import DatasetListResponse, DatasetResponse
        from app.modules.data_management.models.dataset import DataSource, DatasetStatus
        from datetime import datetime

        now = datetime.utcnow()

        datasets = [
            DatasetResponse(
                id="1",
                name="Dataset 1",
                source=DataSource.LOCAL,
                file_path="/data/1.csv",
                status=DatasetStatus.VALID,
                row_count=100,
                columns=[],
                metadata={},
                created_at=now,
                updated_at=now
            ),
            DatasetResponse(
                id="2",
                name="Dataset 2",
                source=DataSource.QLIB,
                file_path="/data/2.csv",
                status=DatasetStatus.PENDING,
                row_count=200,
                columns=[],
                metadata={},
                created_at=now,
                updated_at=now
            )
        ]

        schema = DatasetListResponse(
            total=2,
            items=datasets
        )

        assert schema.total == 2
        assert len(schema.items) == 2
        assert schema.items[0].name == "Dataset 1"
        assert schema.items[1].name == "Dataset 2"

    def test_dataset_list_response_empty(self):
        """Test DatasetListResponse with empty list."""
        from app.modules.data_management.schemas.dataset import DatasetListResponse

        schema = DatasetListResponse(total=0, items=[])

        assert schema.total == 0
        assert schema.items == []
