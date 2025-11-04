"""Tests for base models.

Following TDD approach - these tests are written BEFORE implementation.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError


class TestTimestampMixin:
    """Test TimestampMixin model."""

    def test_timestamp_mixin_auto_creates_timestamps(self):
        """Test that TimestampMixin automatically creates timestamps."""
        from app.modules.common.models.base import TimestampMixin

        model = TimestampMixin()
        assert isinstance(model.created_at, datetime)
        assert isinstance(model.updated_at, datetime)

    def test_timestamp_mixin_accepts_custom_timestamps(self):
        """Test that TimestampMixin accepts custom timestamps."""
        from app.modules.common.models.base import TimestampMixin

        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        model = TimestampMixin(created_at=custom_time, updated_at=custom_time)
        assert model.created_at == custom_time
        assert model.updated_at == custom_time

    def test_timestamp_mixin_serialization(self):
        """Test that TimestampMixin can be serialized to dict."""
        from app.modules.common.models.base import TimestampMixin

        model = TimestampMixin()
        data = model.model_dump()
        assert "created_at" in data
        assert "updated_at" in data


class TestBaseDBModel:
    """Test BaseDBModel."""

    def test_base_db_model_requires_id(self):
        """Test that BaseDBModel requires an id field."""
        from app.modules.common.models.base import BaseDBModel

        # Should raise ValidationError when id is missing
        with pytest.raises(ValidationError) as exc_info:
            BaseDBModel()

        assert "id" in str(exc_info.value)

    def test_base_db_model_with_id(self):
        """Test BaseDBModel creation with id."""
        from app.modules.common.models.base import BaseDBModel

        model = BaseDBModel(id="test-id-123")
        assert model.id == "test-id-123"
        assert model.is_deleted is False
        assert isinstance(model.created_at, datetime)
        assert isinstance(model.updated_at, datetime)

    def test_base_db_model_is_deleted_default(self):
        """Test that is_deleted defaults to False."""
        from app.modules.common.models.base import BaseDBModel

        model = BaseDBModel(id="test-id")
        assert model.is_deleted is False

    def test_base_db_model_can_be_marked_deleted(self):
        """Test that is_deleted can be set to True."""
        from app.modules.common.models.base import BaseDBModel

        model = BaseDBModel(id="test-id", is_deleted=True)
        assert model.is_deleted is True

    def test_base_db_model_inherits_timestamps(self):
        """Test that BaseDBModel inherits timestamp functionality."""
        from app.modules.common.models.base import BaseDBModel

        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        model = BaseDBModel(id="test-id", created_at=custom_time, updated_at=custom_time)
        assert model.created_at == custom_time
        assert model.updated_at == custom_time


class TestPaginationParams:
    """Test PaginationParams model."""

    def test_pagination_params_defaults(self):
        """Test PaginationParams default values."""
        from app.modules.common.models.base import PaginationParams

        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20

    def test_pagination_params_custom_values(self):
        """Test PaginationParams with custom values."""
        from app.modules.common.models.base import PaginationParams

        params = PaginationParams(page=3, page_size=50)
        assert params.page == 3
        assert params.page_size == 50

    def test_pagination_params_page_must_be_positive(self):
        """Test that page must be >= 1."""
        from app.modules.common.models.base import PaginationParams

        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(page=0)

        assert "page" in str(exc_info.value).lower()

        with pytest.raises(ValidationError):
            PaginationParams(page=-1)

    def test_pagination_params_page_size_constraints(self):
        """Test page_size constraints (1-100)."""
        from app.modules.common.models.base import PaginationParams

        # Test minimum
        with pytest.raises(ValidationError):
            PaginationParams(page_size=0)

        # Test maximum
        with pytest.raises(ValidationError):
            PaginationParams(page_size=101)

        # Test valid boundaries
        params_min = PaginationParams(page_size=1)
        assert params_min.page_size == 1

        params_max = PaginationParams(page_size=100)
        assert params_max.page_size == 100

    def test_pagination_params_offset_property(self):
        """Test the offset property calculation."""
        from app.modules.common.models.base import PaginationParams

        params1 = PaginationParams(page=1, page_size=20)
        assert params1.offset == 0

        params2 = PaginationParams(page=2, page_size=20)
        assert params2.offset == 20

        params3 = PaginationParams(page=3, page_size=50)
        assert params3.offset == 100

    def test_pagination_params_limit_property(self):
        """Test the limit property."""
        from app.modules.common.models.base import PaginationParams

        params = PaginationParams(page=1, page_size=25)
        assert params.limit == 25


class TestPaginatedResponse:
    """Test PaginatedResponse model."""

    def test_paginated_response_creation(self):
        """Test PaginatedResponse creation with all fields."""
        from app.modules.common.models.base import PaginatedResponse

        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = PaginatedResponse(
            items=items, total=100, page=2, page_size=20, total_pages=5
        )

        assert response.items == items
        assert response.total == 100
        assert response.page == 2
        assert response.page_size == 20
        assert response.total_pages == 5

    def test_paginated_response_empty_items(self):
        """Test PaginatedResponse with empty items list."""
        from app.modules.common.models.base import PaginatedResponse

        response = PaginatedResponse(items=[], total=0, page=1, page_size=20, total_pages=0)

        assert response.items == []
        assert response.total == 0
        assert response.total_pages == 0

    def test_paginated_response_serialization(self):
        """Test that PaginatedResponse can be serialized."""
        from app.modules.common.models.base import PaginatedResponse

        response = PaginatedResponse(
            items=[{"id": 1}], total=1, page=1, page_size=20, total_pages=1
        )

        data = response.model_dump()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

    def test_paginated_response_with_generic_items(self):
        """Test PaginatedResponse with different item types."""
        from app.modules.common.models.base import PaginatedResponse

        # Test with list of strings
        response1 = PaginatedResponse(
            items=["item1", "item2"], total=2, page=1, page_size=20, total_pages=1
        )
        assert len(response1.items) == 2

        # Test with list of numbers
        response2 = PaginatedResponse(
            items=[1, 2, 3], total=3, page=1, page_size=20, total_pages=1
        )
        assert len(response2.items) == 3
