"""
TDD Tests for Indicator API Endpoints

Comprehensive test suite covering:
- GET /api/indicators (list with pagination and filtering)
- GET /api/indicators/categories (list categories)
- GET /api/indicators/search (search functionality)
- GET /api/indicators/popular (popular indicators)
- GET /api/indicators/{indicator_id} (get detail)
- POST /api/indicators/{indicator_id}/increment-usage (increment usage)

Following TDD best practices:
- AAA pattern (Arrange-Act-Assert)
- Test HTTP status codes and response structure
- Test request validation
- Test error handling
- Test pagination metadata
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.indicator import (
    IndicatorComponent, IndicatorCategory, IndicatorSource
)


@pytest.mark.asyncio
class TestListIndicators:
    """Test GET /api/indicators endpoint."""

    async def test_list_indicators_default_pagination(
        self,
        async_client: AsyncClient,
        sample_indicators_batch: list[IndicatorComponent]
    ):
        """Test listing indicators with default pagination."""
        # ARRANGE
        # sample_indicators_batch provides 25 indicators

        # ACT
        response = await async_client.get("/api/indicators")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["indicators"]) == 25
        assert data["skip"] == 0
        assert data["limit"] == 100

        # Verify response structure
        indicator = data["indicators"][0]
        assert "id" in indicator
        assert "code" in indicator
        assert "name_zh" in indicator
        assert "name_en" in indicator
        assert "category" in indicator
        assert "source" in indicator
        assert "usage_count" in indicator
        assert "is_enabled" in indicator

    async def test_list_indicators_custom_pagination(
        self,
        async_client: AsyncClient,
        sample_indicators_batch: list[IndicatorComponent]
    ):
        """Test listing indicators with custom skip and limit."""
        # ARRANGE
        skip = 10
        limit = 5

        # ACT
        response = await async_client.get(
            f"/api/indicators?skip={skip}&limit={limit}"
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 25
        assert len(data["indicators"]) == 5
        assert data["skip"] == skip
        assert data["limit"] == limit

    async def test_list_indicators_filter_by_category(
        self,
        async_client: AsyncClient,
        sample_indicators_batch: list[IndicatorComponent]
    ):
        """Test listing indicators filtered by category."""
        # ARRANGE
        category = IndicatorCategory.TREND.value

        # ACT
        response = await async_client.get(
            f"/api/indicators?category={category}"
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        # Verify all returned indicators have the correct category
        for indicator in data["indicators"]:
            assert indicator["category"] == category

    async def test_list_indicators_empty_database(
        self,
        async_client: AsyncClient
    ):
        """Test listing indicators when database is empty."""
        # ARRANGE
        # No indicators in database

        # ACT
        response = await async_client.get("/api/indicators")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["indicators"]) == 0

    async def test_list_indicators_invalid_pagination_negative_skip(
        self,
        async_client: AsyncClient
    ):
        """Test listing indicators with invalid negative skip."""
        # ACT
        response = await async_client.get("/api/indicators?skip=-1")

        # ASSERT
        assert response.status_code == 422  # Validation error

    async def test_list_indicators_invalid_pagination_negative_limit(
        self,
        async_client: AsyncClient
    ):
        """Test listing indicators with invalid negative limit."""
        # ACT
        response = await async_client.get("/api/indicators?limit=-1")

        # ASSERT
        assert response.status_code == 422  # Validation error

    async def test_list_indicators_invalid_pagination_limit_exceeds_max(
        self,
        async_client: AsyncClient
    ):
        """Test listing indicators with limit exceeding maximum."""
        # ACT
        response = await async_client.get("/api/indicators?limit=1001")

        # ASSERT
        assert response.status_code == 422  # Validation error

    async def test_list_indicators_with_correlation_id_header(
        self,
        async_client: AsyncClient,
        sample_indicator: IndicatorComponent
    ):
        """Test listing indicators with X-Correlation-ID header."""
        # ARRANGE
        correlation_id = "test-correlation-123"
        headers = {"X-Correlation-ID": correlation_id}

        # ACT
        response = await async_client.get("/api/indicators", headers=headers)

        # ASSERT
        assert response.status_code == 200


@pytest.mark.asyncio
class TestGetCategories:
    """Test GET /api/indicators/categories endpoint."""

    async def test_get_categories_success(
        self,
        async_client: AsyncClient
    ):
        """Test getting all indicator categories."""
        # ACT
        response = await async_client.get("/api/indicators/categories")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "categories" in data
        assert data["total"] > 0
        assert len(data["categories"]) == data["total"]

        # Verify category structure
        if data["categories"]:
            category = data["categories"][0]
            assert "value" in category
            assert "label" in category

    async def test_get_categories_returns_valid_enum_values(
        self,
        async_client: AsyncClient
    ):
        """Test that categories endpoint returns valid enum values."""
        # ACT
        response = await async_client.get("/api/indicators/categories")

        # ASSERT
        assert response.status_code == 200
        data = response.json()

        # Verify all categories are valid enum values
        valid_categories = {cat.value for cat in IndicatorCategory}
        for category in data["categories"]:
            assert category["value"] in valid_categories


@pytest.mark.asyncio
class TestSearchIndicators:
    """Test GET /api/indicators/search endpoint."""

    async def test_search_indicators_by_name(
        self,
        async_client: AsyncClient,
        sample_indicator: IndicatorComponent
    ):
        """Test searching indicators by name."""
        # ARRANGE
        keyword = "SMA"

        # ACT
        response = await async_client.get(
            f"/api/indicators/search?keyword={keyword}"
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["indicators"]) >= 1

        # Verify search results contain the keyword
        found = False
        for indicator in data["indicators"]:
            if keyword.lower() in indicator["code"].lower() or \
               keyword.lower() in indicator["name_en"].lower() or \
               keyword.lower() in indicator["name_zh"].lower():
                found = True
                break
        assert found

    async def test_search_indicators_with_pagination(
        self,
        async_client: AsyncClient,
        sample_indicators_batch: list[IndicatorComponent]
    ):
        """Test searching indicators with custom pagination."""
        # ARRANGE
        keyword = "IND"  # Matches IND_1, IND_2, etc.
        skip = 5
        limit = 5

        # ACT
        response = await async_client.get(
            f"/api/indicators/search?keyword={keyword}&skip={skip}&limit={limit}"
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert len(data["indicators"]) <= 5
        assert data["skip"] == skip
        assert data["limit"] == limit

    async def test_search_indicators_no_results(
        self,
        async_client: AsyncClient,
        sample_indicator: IndicatorComponent
    ):
        """Test searching indicators with no matching results."""
        # ARRANGE
        keyword = "NONEXISTENT_INDICATOR_XYZ"

        # ACT
        response = await async_client.get(
            f"/api/indicators/search?keyword={keyword}"
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["indicators"]) == 0

    async def test_search_indicators_missing_keyword(
        self,
        async_client: AsyncClient
    ):
        """Test searching indicators without keyword parameter."""
        # ACT
        response = await async_client.get("/api/indicators/search")

        # ASSERT
        assert response.status_code == 422  # Validation error

    async def test_search_indicators_empty_keyword(
        self,
        async_client: AsyncClient
    ):
        """Test searching indicators with empty keyword."""
        # ACT
        response = await async_client.get("/api/indicators/search?keyword=")

        # ASSERT
        assert response.status_code == 422  # Validation error (min_length=1)


@pytest.mark.asyncio
class TestGetPopularIndicators:
    """Test GET /api/indicators/popular endpoint."""

    async def test_get_popular_indicators_default_limit(
        self,
        async_client: AsyncClient,
        sample_indicators_batch: list[IndicatorComponent]
    ):
        """Test getting popular indicators with default limit."""
        # ACT
        response = await async_client.get("/api/indicators/popular")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert len(data["indicators"]) <= 10  # Default limit

        # Verify indicators are sorted by usage_count (descending)
        if len(data["indicators"]) > 1:
            usage_counts = [ind["usage_count"] for ind in data["indicators"]]
            assert usage_counts == sorted(usage_counts, reverse=True)

    async def test_get_popular_indicators_custom_limit(
        self,
        async_client: AsyncClient,
        sample_indicators_batch: list[IndicatorComponent]
    ):
        """Test getting popular indicators with custom limit."""
        # ARRANGE
        limit = 5

        # ACT
        response = await async_client.get(
            f"/api/indicators/popular?limit={limit}"
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert len(data["indicators"]) <= limit

    async def test_get_popular_indicators_empty_database(
        self,
        async_client: AsyncClient
    ):
        """Test getting popular indicators when database is empty."""
        # ACT
        response = await async_client.get("/api/indicators/popular")

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["indicators"]) == 0

    async def test_get_popular_indicators_invalid_limit_negative(
        self,
        async_client: AsyncClient
    ):
        """Test getting popular indicators with negative limit."""
        # ACT
        response = await async_client.get("/api/indicators/popular?limit=-1")

        # ASSERT
        assert response.status_code == 422  # Validation error

    async def test_get_popular_indicators_invalid_limit_exceeds_max(
        self,
        async_client: AsyncClient
    ):
        """Test getting popular indicators with limit exceeding maximum."""
        # ACT
        response = await async_client.get("/api/indicators/popular?limit=51")

        # ASSERT
        assert response.status_code == 422  # Validation error (max=50)


@pytest.mark.asyncio
class TestGetIndicatorDetail:
    """Test GET /api/indicators/{indicator_id} endpoint."""

    async def test_get_indicator_detail_success(
        self,
        async_client: AsyncClient,
        sample_indicator: IndicatorComponent
    ):
        """Test getting indicator detail by ID."""
        # ACT
        response = await async_client.get(
            f"/api/indicators/{sample_indicator.id}"
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_indicator.id)
        assert data["code"] == sample_indicator.code
        assert data["name_zh"] == sample_indicator.name_zh
        assert data["name_en"] == sample_indicator.name_en
        assert data["category"] == sample_indicator.category
        assert data["source"] == sample_indicator.source

        # Verify optional fields are present
        assert "description_zh" in data
        assert "description_en" in data
        assert "formula" in data
        assert "parameters" in data
        assert "default_params" in data
        assert "usage_count" in data
        assert "is_enabled" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_get_indicator_detail_not_found(
        self,
        async_client: AsyncClient
    ):
        """Test getting indicator detail with non-existent ID."""
        # ARRANGE
        non_existent_id = "00000000-0000-0000-0000-000000000000"

        # ACT
        response = await async_client.get(
            f"/api/indicators/{non_existent_id}"
        )

        # ASSERT
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert non_existent_id in data["detail"]


@pytest.mark.asyncio
class TestIncrementIndicatorUsage:
    """Test POST /api/indicators/{indicator_id}/increment-usage endpoint."""

    async def test_increment_usage_success(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        sample_indicator: IndicatorComponent
    ):
        """Test incrementing indicator usage count."""
        # ARRANGE
        original_count = sample_indicator.usage_count

        # ACT
        response = await async_client.post(
            f"/api/indicators/{sample_indicator.id}/increment-usage"
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "incremented successfully" in data["message"].lower()

        # Verify usage count was actually incremented in database
        await db_session.refresh(sample_indicator)
        assert sample_indicator.usage_count == original_count + 1

    async def test_increment_usage_multiple_times(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        sample_indicator: IndicatorComponent
    ):
        """Test incrementing indicator usage count multiple times."""
        # ARRANGE
        original_count = sample_indicator.usage_count
        increment_times = 3

        # ACT
        for _ in range(increment_times):
            response = await async_client.post(
                f"/api/indicators/{sample_indicator.id}/increment-usage"
            )
            assert response.status_code == 200

        # ASSERT
        await db_session.refresh(sample_indicator)
        assert sample_indicator.usage_count == original_count + increment_times

    async def test_increment_usage_not_found(
        self,
        async_client: AsyncClient
    ):
        """Test incrementing usage for non-existent indicator."""
        # ARRANGE
        non_existent_id = "00000000-0000-0000-0000-000000000000"

        # ACT
        response = await async_client.post(
            f"/api/indicators/{non_existent_id}/increment-usage"
        )

        # ASSERT
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert non_existent_id in data["detail"]


@pytest.mark.asyncio
class TestIndicatorAPIErrorHandling:
    """Test error handling for Indicator API endpoints."""

    async def test_list_indicators_server_error_handling(
        self,
        async_client: AsyncClient,
        monkeypatch
    ):
        """Test list indicators handles server errors gracefully."""
        # ARRANGE
        from app.modules.indicator.services import indicator_service

        async def mock_get_all_indicators(*args, **kwargs):
            raise Exception("Database connection failed")

        monkeypatch.setattr(
            indicator_service.IndicatorService,
            "get_all_indicators",
            mock_get_all_indicators
        )

        # ACT
        response = await async_client.get("/api/indicators")

        # ASSERT
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    async def test_search_indicators_invalid_query_parameters(
        self,
        async_client: AsyncClient
    ):
        """Test search indicators with invalid query parameters."""
        # ACT
        response = await async_client.get(
            "/api/indicators/search?keyword=test&skip=-5&limit=0"
        )

        # ASSERT
        assert response.status_code == 422


@pytest.mark.asyncio
class TestIndicatorAPIResponseFormat:
    """Test response format consistency for Indicator API."""

    async def test_list_response_includes_pagination_metadata(
        self,
        async_client: AsyncClient,
        sample_indicator: IndicatorComponent
    ):
        """Test that list response always includes pagination metadata."""
        # ACT
        response = await async_client.get("/api/indicators")

        # ASSERT
        assert response.status_code == 200
        data = response.json()

        # Verify pagination metadata
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert "indicators" in data

        assert isinstance(data["total"], int)
        assert isinstance(data["skip"], int)
        assert isinstance(data["limit"], int)
        assert isinstance(data["indicators"], list)

    async def test_indicator_detail_response_format(
        self,
        async_client: AsyncClient,
        sample_indicator: IndicatorComponent
    ):
        """Test indicator detail response has correct format."""
        # ACT
        response = await async_client.get(
            f"/api/indicators/{sample_indicator.id}"
        )

        # ASSERT
        assert response.status_code == 200
        data = response.json()

        # Verify required fields are present and have correct types
        assert isinstance(data["id"], str)
        assert isinstance(data["code"], str)
        assert isinstance(data["name_zh"], str)
        assert isinstance(data["name_en"], str)
        assert isinstance(data["category"], str)
        assert isinstance(data["source"], str)
        assert isinstance(data["usage_count"], int)
        assert isinstance(data["is_enabled"], bool)

    async def test_error_response_format(
        self,
        async_client: AsyncClient
    ):
        """Test error responses have consistent format."""
        # ACT
        response = await async_client.get(
            "/api/indicators/00000000-0000-0000-0000-000000000000"
        )

        # ASSERT
        assert response.status_code == 404
        data = response.json()

        # Verify error response structure
        assert "detail" in data
        assert isinstance(data["detail"], str)
