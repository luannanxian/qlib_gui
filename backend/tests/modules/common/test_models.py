"""
Tests for common models (TDD - RED phase)
"""

import pytest
from datetime import datetime
from pydantic import ValidationError


class TestTimestampMixin:
    """Test TimestampMixin model"""

    def test_timestamp_mixin_creates_timestamps(self):
        """Test that TimestampMixin automatically creates timestamps"""
        from app.modules.common.models.base import TimestampMixin

        model = TimestampMixin()
        assert isinstance(model.created_at, datetime)
        assert isinstance(model.updated_at, datetime)

    def test_timestamp_mixin_updates_timestamp(self):
        """Test that updated_at can be modified"""
        from app.modules.common.models.base import TimestampMixin

        model = TimestampMixin()
        original_updated_at = model.updated_at

        # Simulate an update
        new_time = datetime.now()
        model.updated_at = new_time

        assert model.updated_at == new_time
        assert model.updated_at != original_updated_at


class TestBaseDBModel:
    """Test BaseDBModel"""

    def test_base_db_model_has_id(self):
        """Test that BaseDBModel has an id field"""
        from app.modules.common.models.base import BaseDBModel

        model = BaseDBModel(id="test-123")
        assert model.id == "test-123"

    def test_base_db_model_has_is_deleted(self):
        """Test that BaseDBModel has is_deleted field with default False"""
        from app.modules.common.models.base import BaseDBModel

        model = BaseDBModel(id="test-123")
        assert model.is_deleted is False

    def test_base_db_model_has_timestamps(self):
        """Test that BaseDBModel includes timestamp fields"""
        from app.modules.common.models.base import BaseDBModel

        model = BaseDBModel(id="test-123")
        assert hasattr(model, "created_at")
        assert hasattr(model, "updated_at")
        assert isinstance(model.created_at, datetime)


class TestPaginationParams:
    """Test PaginationParams model"""

    def test_pagination_params_default_values(self):
        """Test default pagination parameters"""
        from app.modules.common.models.base import PaginationParams

        params = PaginationParams()
        assert params.page == 1
        assert params.page_size == 20

    def test_pagination_params_custom_values(self):
        """Test custom pagination parameters"""
        from app.modules.common.models.base import PaginationParams

        params = PaginationParams(page=2, page_size=50)
        assert params.page == 2
        assert params.page_size == 50

    def test_pagination_params_offset_calculation(self):
        """Test offset property calculation"""
        from app.modules.common.models.base import PaginationParams

        params = PaginationParams(page=3, page_size=20)
        assert params.offset == 40  # (3-1) * 20

    def test_pagination_params_limit_property(self):
        """Test limit property"""
        from app.modules.common.models.base import PaginationParams

        params = PaginationParams(page_size=25)
        assert params.limit == 25

    def test_pagination_params_validates_min_page(self):
        """Test that page must be >= 1"""
        from app.modules.common.models.base import PaginationParams

        with pytest.raises(ValidationError):
            PaginationParams(page=0)

    def test_pagination_params_validates_min_page_size(self):
        """Test that page_size must be >= 1"""
        from app.modules.common.models.base import PaginationParams

        with pytest.raises(ValidationError):
            PaginationParams(page_size=0)

    def test_pagination_params_validates_max_page_size(self):
        """Test that page_size must be <= 100"""
        from app.modules.common.models.base import PaginationParams

        with pytest.raises(ValidationError):
            PaginationParams(page_size=101)


class TestPaginatedResponse:
    """Test PaginatedResponse model"""

    def test_paginated_response_creation(self):
        """Test creating a paginated response"""
        from app.modules.common.models.base import PaginatedResponse

        items = [{"id": 1}, {"id": 2}, {"id": 3}]
        response = PaginatedResponse(
            items=items, total=100, page=1, page_size=20, total_pages=5
        )

        assert response.items == items
        assert response.total == 100
        assert response.page == 1
        assert response.page_size == 20
        assert response.total_pages == 5

    def test_paginated_response_calculates_total_pages(self):
        """Test that total_pages is correctly calculated"""
        from app.modules.common.models.base import PaginatedResponse

        # 100 items, 20 per page = 5 pages
        response = PaginatedResponse(items=[], total=100, page=1, page_size=20, total_pages=5)
        assert response.total_pages == 5

        # 95 items, 20 per page = 5 pages (rounded up)
        response2 = PaginatedResponse(items=[], total=95, page=1, page_size=20, total_pages=5)
        assert response2.total_pages == 5
