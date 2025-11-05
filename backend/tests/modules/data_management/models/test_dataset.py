"""Tests for Dataset models.

Following TDD approach - these tests are written BEFORE implementation.
"""

import pytest
from datetime import datetime


class TestDataSource:
    """Test DataSource enum."""

    def test_data_source_enum_values(self):
        """Test DataSource enum has correct values."""
        from app.modules.data_management.models.dataset import DataSource

        assert DataSource.LOCAL == "local"
        assert DataSource.QLIB == "qlib"
        assert DataSource.THIRDPARTY == "thirdparty"

    def test_data_source_is_enum(self):
        """Test DataSource is an Enum."""
        from app.modules.data_management.models.dataset import DataSource
        from enum import Enum

        assert issubclass(DataSource, Enum)


class TestDatasetStatus:
    """Test DatasetStatus enum."""

    def test_dataset_status_enum_values(self):
        """Test DatasetStatus enum has correct values."""
        from app.modules.data_management.models.dataset import DatasetStatus

        assert DatasetStatus.VALID == "valid"
        assert DatasetStatus.INVALID == "invalid"
        assert DatasetStatus.PENDING == "pending"

    def test_dataset_status_is_enum(self):
        """Test DatasetStatus is an Enum."""
        from app.modules.data_management.models.dataset import DatasetStatus
        from enum import Enum

        assert issubclass(DatasetStatus, Enum)


class TestDataset:
    """Test Dataset model."""

    def test_dataset_creation(self):
        """Test Dataset model creation with minimal fields."""
        from app.modules.data_management.models.dataset import Dataset, DataSource, DatasetStatus

        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv"
        )

        assert dataset.name == "Test Dataset"
        assert dataset.source == DataSource.LOCAL
        assert dataset.file_path == "/data/test.csv"
        assert dataset.status == DatasetStatus.PENDING  # Default value
        assert dataset.row_count == 0  # Default value
        assert dataset.columns == []  # Default value
        assert dataset.metadata == {}  # Default value

    def test_dataset_with_all_fields(self):
        """Test Dataset model with all fields."""
        from app.modules.data_management.models.dataset import Dataset, DataSource, DatasetStatus

        metadata = {"description": "Test data", "version": "1.0"}
        columns = ["open", "high", "low", "close", "volume"]

        dataset = Dataset(
            name="Full Dataset",
            source=DataSource.QLIB,
            file_path="/data/qlib.csv",
            status=DatasetStatus.VALID,
            row_count=1000,
            columns=columns,
            metadata=metadata
        )

        assert dataset.name == "Full Dataset"
        assert dataset.source == DataSource.QLIB
        assert dataset.file_path == "/data/qlib.csv"
        assert dataset.status == DatasetStatus.VALID
        assert dataset.row_count == 1000
        assert dataset.columns == columns
        assert dataset.metadata == metadata

    def test_dataset_has_timestamps(self):
        """Test Dataset has created_at and updated_at timestamps."""
        from app.modules.data_management.models.dataset import Dataset, DataSource

        dataset = Dataset(
            name="Test",
            source=DataSource.LOCAL,
            file_path="/data/test.csv"
        )

        assert hasattr(dataset, "created_at")
        assert hasattr(dataset, "updated_at")
        assert isinstance(dataset.created_at, datetime)
        assert isinstance(dataset.updated_at, datetime)

    def test_dataset_id_generation(self):
        """Test Dataset generates unique ID."""
        from app.modules.data_management.models.dataset import Dataset, DataSource

        dataset1 = Dataset(name="Dataset 1", source=DataSource.LOCAL, file_path="/data/1.csv")
        dataset2 = Dataset(name="Dataset 2", source=DataSource.LOCAL, file_path="/data/2.csv")

        assert hasattr(dataset1, "id")
        assert hasattr(dataset2, "id")
        assert dataset1.id != dataset2.id

    def test_dataset_str_representation(self):
        """Test Dataset string representation."""
        from app.modules.data_management.models.dataset import Dataset, DataSource

        dataset = Dataset(
            name="Test Dataset",
            source=DataSource.LOCAL,
            file_path="/data/test.csv"
        )

        str_repr = str(dataset)
        assert "Test Dataset" in str_repr
        assert "local" in str_repr

    def test_dataset_source_validation(self):
        """Test Dataset source must be valid DataSource."""
        from app.modules.data_management.models.dataset import Dataset, DataSource
        from pydantic import ValidationError

        # Valid source should work
        dataset = Dataset(name="Test", source=DataSource.LOCAL, file_path="/data/test.csv")
        assert dataset.source == DataSource.LOCAL

        # Invalid source should raise ValidationError
        with pytest.raises(ValidationError):
            Dataset(name="Test", source="invalid_source", file_path="/data/test.csv")

    def test_dataset_status_validation(self):
        """Test Dataset status must be valid DatasetStatus."""
        from app.modules.data_management.models.dataset import Dataset, DataSource, DatasetStatus
        from pydantic import ValidationError

        # Valid status should work
        dataset = Dataset(
            name="Test",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            status=DatasetStatus.VALID
        )
        assert dataset.status == DatasetStatus.VALID

        # Invalid status should raise ValidationError
        with pytest.raises(ValidationError):
            Dataset(
                name="Test",
                source=DataSource.LOCAL,
                file_path="/data/test.csv",
                status="invalid_status"
            )

    def test_dataset_row_count_non_negative(self):
        """Test Dataset row_count must be non-negative."""
        from app.modules.data_management.models.dataset import Dataset, DataSource
        from pydantic import ValidationError

        # Positive row_count should work
        dataset = Dataset(
            name="Test",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            row_count=100
        )
        assert dataset.row_count == 100

        # Zero row_count should work
        dataset_zero = Dataset(
            name="Test",
            source=DataSource.LOCAL,
            file_path="/data/test.csv",
            row_count=0
        )
        assert dataset_zero.row_count == 0

        # Negative row_count should raise ValidationError
        with pytest.raises(ValidationError):
            Dataset(
                name="Test",
                source=DataSource.LOCAL,
                file_path="/data/test.csv",
                row_count=-1
            )

    def test_dataset_name_required(self):
        """Test Dataset name is required."""
        from app.modules.data_management.models.dataset import Dataset, DataSource
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Dataset(source=DataSource.LOCAL, file_path="/data/test.csv")

    def test_dataset_file_path_required(self):
        """Test Dataset file_path is required."""
        from app.modules.data_management.models.dataset import Dataset, DataSource
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Dataset(name="Test", source=DataSource.LOCAL)
