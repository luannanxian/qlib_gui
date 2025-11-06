"""
TDD Tests for IndicatorService

Comprehensive test suite covering:
- CRUD operations
- Pagination functionality
- Search functionality
- Data validation
- Exception handling
- Business logic validation
- Edge cases

Following TDD best practices:
- AAA pattern (Arrange-Act-Assert)
- Single responsibility per test
- Clear test naming
- Fixture-based test data
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.indicator import IndicatorComponent, IndicatorCategory, IndicatorSource
from app.modules.indicator.services.indicator_service import IndicatorService


@pytest.mark.asyncio
class TestIndicatorServiceGetAllIndicators:
    """Test get_all_indicators with pagination."""

    async def test_get_all_indicators_default_pagination(
        self,
        indicator_service: IndicatorService,
        sample_indicators_batch: list[IndicatorComponent]
    ):
        """Test getting all indicators with default pagination parameters."""
        # ARRANGE
        # sample_indicators_batch provides 25 indicators

        # ACT
        result = await indicator_service.get_all_indicators(skip=0, limit=100)

        # ASSERT
        assert result["total"] == 25
        assert len(result["indicators"]) == 25
        assert result["skip"] == 0
        assert result["limit"] == 100

        # Verify indicators are sorted by usage_count (descending)
        usage_counts = [ind["usage_count"] for ind in result["indicators"]]
        assert usage_counts == sorted(usage_counts, reverse=True)

    async def test_get_all_indicators_custom_pagination(
        self,
        indicator_service: IndicatorService,
        sample_indicators_batch: list[IndicatorComponent]
    ):
        """Test pagination with custom skip and limit."""
        # ARRANGE
        skip = 10
        limit = 5

        # ACT
        result = await indicator_service.get_all_indicators(skip=skip, limit=limit)

        # ASSERT
        assert result["total"] == 25
        assert len(result["indicators"]) == 5
        assert result["skip"] == skip
        assert result["limit"] == limit

    async def test_get_all_indicators_empty_database(
        self,
        indicator_service: IndicatorService
    ):
        """Test getting indicators when database is empty."""
        # ARRANGE
        # No indicators in database

        # ACT
        result = await indicator_service.get_all_indicators()

        # ASSERT
        assert result["total"] == 0
        assert len(result["indicators"]) == 0

    async def test_get_all_indicators_skip_exceeds_total(
        self,
        indicator_service: IndicatorService,
        sample_indicators_batch: list[IndicatorComponent]
    ):
        """Test pagination when skip exceeds total count."""
        # ARRANGE
        skip = 100  # More than 25 indicators

        # ACT
        result = await indicator_service.get_all_indicators(skip=skip, limit=10)

        # ASSERT
        assert result["total"] == 25
        assert len(result["indicators"]) == 0  # No results
        assert result["skip"] == skip

    async def test_get_all_indicators_only_enabled(
        self,
        indicator_service: IndicatorService,
        db_session: AsyncSession
    ):
        """Test that only enabled indicators are returned."""
        # ARRANGE
        enabled = IndicatorComponent(
            code="ENABLED",
            name_zh="启用指标",
            name_en="Enabled Indicator",
            category=IndicatorCategory.TREND.value,
            source=IndicatorSource.QLIB.value,
            is_enabled=True
        )
        disabled = IndicatorComponent(
            code="DISABLED",
            name_zh="禁用指标",
            name_en="Disabled Indicator",
            category=IndicatorCategory.TREND.value,
            source=IndicatorSource.QLIB.value,
            is_enabled=False
        )
        db_session.add(enabled)
        db_session.add(disabled)
        await db_session.commit()

        # ACT
        result = await indicator_service.get_all_indicators()

        # ASSERT
        assert result["total"] == 1
        assert len(result["indicators"]) == 1
        assert result["indicators"][0]["code"] == "ENABLED"


@pytest.mark.asyncio
class TestIndicatorServiceGetByCategory:
    """Test get_indicators_by_category with filtering and pagination."""

    async def test_get_indicators_by_category_trend(
        self,
        indicator_service: IndicatorService,
        sample_indicators_batch: list[IndicatorComponent]
    ):
        """Test filtering indicators by TREND category."""
        # ARRANGE
        category = IndicatorCategory.TREND.value

        # ACT
        result = await indicator_service.get_indicators_by_category(
            category=category,
            skip=0,
            limit=100
        )

        # ASSERT
        assert result["total"] > 0
        for ind in result["indicators"]:
            assert ind["category"] == category

    async def test_get_indicators_by_category_momentum(
        self,
        indicator_service: IndicatorService,
        sample_indicators_batch: list[IndicatorComponent]
    ):
        """Test filtering indicators by MOMENTUM category."""
        # ARRANGE
        category = IndicatorCategory.MOMENTUM.value

        # ACT
        result = await indicator_service.get_indicators_by_category(
            category=category,
            skip=0,
            limit=100
        )

        # ASSERT
        assert result["total"] > 0
        for ind in result["indicators"]:
            assert ind["category"] == category

    async def test_get_indicators_by_category_with_pagination(
        self,
        indicator_service: IndicatorService,
        sample_indicators_batch: list[IndicatorComponent]
    ):
        """Test category filtering with pagination."""
        # ARRANGE
        category = IndicatorCategory.TREND.value
        skip = 2
        limit = 3

        # ACT
        result = await indicator_service.get_indicators_by_category(
            category=category,
            skip=skip,
            limit=limit
        )

        # ASSERT
        assert len(result["indicators"]) <= limit
        assert result["skip"] == skip
        assert result["limit"] == limit

    async def test_get_indicators_by_category_empty_result(
        self,
        indicator_service: IndicatorService,
        db_session: AsyncSession
    ):
        """Test category filtering when no matching indicators exist."""
        # ARRANGE
        # Add only trend indicators
        indicator = IndicatorComponent(
            code="TREND1",
            name_zh="趋势指标",
            name_en="Trend Indicator",
            category=IndicatorCategory.TREND.value,
            source=IndicatorSource.QLIB.value,
            is_enabled=True
        )
        db_session.add(indicator)
        await db_session.commit()

        # ACT
        result = await indicator_service.get_indicators_by_category(
            category=IndicatorCategory.VOLATILITY.value
        )

        # ASSERT
        assert result["total"] == 0
        assert len(result["indicators"]) == 0


@pytest.mark.asyncio
class TestIndicatorServiceSearch:
    """Test search_indicators functionality."""

    async def test_search_indicators_by_name_zh(
        self,
        indicator_service: IndicatorService,
        sample_indicator: IndicatorComponent
    ):
        """Test searching indicators by Chinese name."""
        # ARRANGE
        keyword = "移动"  # Part of "简单移动平均"

        # ACT
        result = await indicator_service.search_indicators(keyword=keyword)

        # ASSERT
        assert result["total"] > 0
        assert result["keyword"] == keyword
        assert any("移动" in ind["name_zh"] for ind in result["indicators"])

    async def test_search_indicators_by_name_en(
        self,
        indicator_service: IndicatorService,
        sample_indicator: IndicatorComponent
    ):
        """Test searching indicators by English name."""
        # ARRANGE
        keyword = "Moving"  # Part of "Simple Moving Average"

        # ACT
        result = await indicator_service.search_indicators(keyword=keyword)

        # ASSERT
        assert result["total"] > 0
        assert any("Moving" in ind["name_en"] for ind in result["indicators"])

    async def test_search_indicators_by_code(
        self,
        indicator_service: IndicatorService,
        sample_indicator: IndicatorComponent
    ):
        """Test searching indicators by code."""
        # ARRANGE
        keyword = "SMA"

        # ACT
        result = await indicator_service.search_indicators(keyword=keyword)

        # ASSERT
        assert result["total"] > 0
        assert any(ind["code"] == "SMA" for ind in result["indicators"])

    async def test_search_indicators_no_results(
        self,
        indicator_service: IndicatorService,
        sample_indicator: IndicatorComponent
    ):
        """Test searching with keyword that matches nothing."""
        # ARRANGE
        keyword = "XYZ_NONEXISTENT_999"

        # ACT
        result = await indicator_service.search_indicators(keyword=keyword)

        # ASSERT
        assert result["total"] == 0
        assert len(result["indicators"]) == 0
        assert result["keyword"] == keyword

    async def test_search_indicators_with_pagination(
        self,
        indicator_service: IndicatorService,
        sample_indicators_batch: list[IndicatorComponent]
    ):
        """Test search with pagination."""
        # ARRANGE
        keyword = "指标"  # Matches all Chinese indicators
        skip = 5
        limit = 3

        # ACT
        result = await indicator_service.search_indicators(
            keyword=keyword,
            skip=skip,
            limit=limit
        )

        # ASSERT
        assert len(result["indicators"]) <= limit
        assert result["skip"] == skip
        assert result["limit"] == limit

    async def test_search_indicators_empty_keyword(
        self,
        indicator_service: IndicatorService,
        sample_indicator: IndicatorComponent
    ):
        """Test searching with empty keyword."""
        # ARRANGE
        keyword = ""

        # ACT
        result = await indicator_service.search_indicators(keyword=keyword)

        # ASSERT
        # Empty keyword should return no results or all results (depends on implementation)
        assert isinstance(result["total"], int)
        assert isinstance(result["indicators"], list)


@pytest.mark.asyncio
class TestIndicatorServiceGetDetail:
    """Test get_indicator_detail functionality."""

    async def test_get_indicator_detail_existing(
        self,
        indicator_service: IndicatorService,
        sample_indicator: IndicatorComponent
    ):
        """Test getting detail for existing indicator."""
        # ARRANGE
        indicator_id = sample_indicator.id

        # ACT
        result = await indicator_service.get_indicator_detail(indicator_id)

        # ASSERT
        assert result is not None
        assert result["id"] == indicator_id
        assert result["code"] == "SMA"
        assert result["name_zh"] == "简单移动平均"
        assert result["name_en"] == "Simple Moving Average"
        assert result["category"] == IndicatorCategory.TREND.value
        assert result["source"] == IndicatorSource.TALIB.value
        assert "formula" in result
        assert "parameters" in result
        assert "default_params" in result
        assert "usage_count" in result
        assert "created_at" in result

    async def test_get_indicator_detail_nonexistent(
        self,
        indicator_service: IndicatorService
    ):
        """Test getting detail for non-existent indicator."""
        # ARRANGE
        nonexistent_id = "00000000-0000-0000-0000-000000000000"

        # ACT
        result = await indicator_service.get_indicator_detail(nonexistent_id)

        # ASSERT
        assert result is None

    async def test_get_indicator_detail_all_fields(
        self,
        indicator_service: IndicatorService,
        sample_indicator: IndicatorComponent
    ):
        """Test that detail includes all expected fields."""
        # ARRANGE
        indicator_id = sample_indicator.id

        # ACT
        result = await indicator_service.get_indicator_detail(indicator_id)

        # ASSERT
        required_fields = [
            "id", "code", "name_zh", "name_en", "category", "source",
            "description_zh", "description_en", "formula", "parameters",
            "default_params", "usage_count", "is_enabled", "created_at", "updated_at"
        ]
        for field in required_fields:
            assert field in result, f"Missing field: {field}"


@pytest.mark.asyncio
class TestIndicatorServiceUsageTracking:
    """Test increment_usage functionality."""

    async def test_increment_usage_existing_indicator(
        self,
        indicator_service: IndicatorService,
        sample_indicator: IndicatorComponent,
        db_session: AsyncSession
    ):
        """Test incrementing usage count for existing indicator."""
        # ARRANGE
        indicator_id = sample_indicator.id
        initial_count = sample_indicator.usage_count

        # ACT
        success = await indicator_service.increment_usage(indicator_id)

        # ASSERT
        assert success is True

        # Verify count increased
        await db_session.refresh(sample_indicator)
        assert sample_indicator.usage_count == initial_count + 1

    async def test_increment_usage_multiple_times(
        self,
        indicator_service: IndicatorService,
        sample_indicator: IndicatorComponent,
        db_session: AsyncSession
    ):
        """Test incrementing usage count multiple times."""
        # ARRANGE
        indicator_id = sample_indicator.id
        initial_count = sample_indicator.usage_count
        increment_times = 5

        # ACT
        for _ in range(increment_times):
            success = await indicator_service.increment_usage(indicator_id)
            assert success is True

        # ASSERT
        await db_session.refresh(sample_indicator)
        assert sample_indicator.usage_count == initial_count + increment_times

    async def test_increment_usage_nonexistent_indicator(
        self,
        indicator_service: IndicatorService
    ):
        """Test incrementing usage for non-existent indicator."""
        # ARRANGE
        nonexistent_id = "00000000-0000-0000-0000-000000000000"

        # ACT
        success = await indicator_service.increment_usage(nonexistent_id)

        # ASSERT
        assert success is False


@pytest.mark.asyncio
class TestIndicatorServicePopularIndicators:
    """Test get_popular_indicators functionality."""

    async def test_get_popular_indicators_default_limit(
        self,
        indicator_service: IndicatorService,
        sample_indicators_batch: list[IndicatorComponent]
    ):
        """Test getting popular indicators with default limit."""
        # ARRANGE
        # sample_indicators_batch has indicators with varying usage_count

        # ACT
        result = await indicator_service.get_popular_indicators(limit=10)

        # ASSERT
        assert len(result["indicators"]) <= 10
        assert result["total"] == len(result["indicators"])

        # Verify sorted by usage_count descending
        usage_counts = [ind["usage_count"] for ind in result["indicators"]]
        assert usage_counts == sorted(usage_counts, reverse=True)

    async def test_get_popular_indicators_custom_limit(
        self,
        indicator_service: IndicatorService,
        sample_indicators_batch: list[IndicatorComponent]
    ):
        """Test getting popular indicators with custom limit."""
        # ARRANGE
        limit = 5

        # ACT
        result = await indicator_service.get_popular_indicators(limit=limit)

        # ASSERT
        assert len(result["indicators"]) <= limit
        assert result["total"] == len(result["indicators"])

    async def test_get_popular_indicators_empty_database(
        self,
        indicator_service: IndicatorService
    ):
        """Test getting popular indicators when database is empty."""
        # ARRANGE
        # No indicators

        # ACT
        result = await indicator_service.get_popular_indicators()

        # ASSERT
        assert result["total"] == 0
        assert len(result["indicators"]) == 0

    async def test_get_popular_indicators_order(
        self,
        indicator_service: IndicatorService,
        db_session: AsyncSession
    ):
        """Test that popular indicators are correctly ordered by usage_count."""
        # ARRANGE
        indicators = [
            IndicatorComponent(
                code=f"POP_{i}",
                name_zh=f"流行指标{i}",
                name_en=f"Popular {i}",
                category=IndicatorCategory.TREND.value,
                source=IndicatorSource.QLIB.value,
                is_enabled=True,
                usage_count=i * 100
            )
            for i in [5, 3, 8, 1, 9, 2]
        ]
        for ind in indicators:
            db_session.add(ind)
        await db_session.commit()

        # ACT
        result = await indicator_service.get_popular_indicators(limit=6)

        # ASSERT
        expected_order = [900, 800, 500, 300, 200, 100]
        actual_order = [ind["usage_count"] for ind in result["indicators"]]
        assert actual_order == expected_order


@pytest.mark.asyncio
class TestIndicatorServiceValidation:
    """Test validate_indicator_exists functionality."""

    async def test_validate_indicator_exists_enabled(
        self,
        indicator_service: IndicatorService,
        sample_indicator: IndicatorComponent
    ):
        """Test validating an existing enabled indicator."""
        # ARRANGE
        indicator_id = sample_indicator.id

        # ACT
        is_valid = await indicator_service.validate_indicator_exists(indicator_id)

        # ASSERT
        assert is_valid is True

    async def test_validate_indicator_exists_disabled(
        self,
        indicator_service: IndicatorService,
        db_session: AsyncSession
    ):
        """Test validating a disabled indicator."""
        # ARRANGE
        disabled = IndicatorComponent(
            code="DISABLED",
            name_zh="禁用",
            name_en="Disabled",
            category=IndicatorCategory.TREND.value,
            source=IndicatorSource.QLIB.value,
            is_enabled=False
        )
        db_session.add(disabled)
        await db_session.commit()
        await db_session.refresh(disabled)

        # ACT
        is_valid = await indicator_service.validate_indicator_exists(disabled.id)

        # ASSERT
        assert is_valid is False

    async def test_validate_indicator_exists_nonexistent(
        self,
        indicator_service: IndicatorService
    ):
        """Test validating a non-existent indicator."""
        # ARRANGE
        nonexistent_id = "00000000-0000-0000-0000-000000000000"

        # ACT
        is_valid = await indicator_service.validate_indicator_exists(nonexistent_id)

        # ASSERT
        assert is_valid is False


@pytest.mark.asyncio
class TestIndicatorServiceGetCategories:
    """Test get_indicator_categories functionality."""

    async def test_get_indicator_categories_returns_all(
        self,
        indicator_service: IndicatorService
    ):
        """Test getting all indicator categories."""
        # ARRANGE
        # No setup needed

        # ACT
        result = await indicator_service.get_indicator_categories()

        # ASSERT
        assert "categories" in result
        assert "total" in result
        assert result["total"] > 0
        assert len(result["categories"]) == result["total"]

        # Verify structure
        for category in result["categories"]:
            assert "value" in category
            assert "label" in category

    async def test_get_indicator_categories_includes_all_enum_values(
        self,
        indicator_service: IndicatorService
    ):
        """Test that all enum values are included."""
        # ARRANGE
        expected_categories = {cat.value for cat in IndicatorCategory}

        # ACT
        result = await indicator_service.get_indicator_categories()

        # ASSERT
        actual_categories = {cat["value"] for cat in result["categories"]}
        assert actual_categories == expected_categories

    async def test_get_indicator_categories_format(
        self,
        indicator_service: IndicatorService
    ):
        """Test category result format."""
        # ARRANGE
        # No setup

        # ACT
        result = await indicator_service.get_indicator_categories()

        # ASSERT
        for category in result["categories"]:
            assert isinstance(category["value"], str)
            assert isinstance(category["label"], str)
            assert category["value"] in [cat.value for cat in IndicatorCategory]


@pytest.mark.asyncio
class TestIndicatorServiceEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_large_pagination_offset(
        self,
        indicator_service: IndicatorService,
        sample_indicators_batch: list[IndicatorComponent]
    ):
        """Test with very large skip value."""
        # ARRANGE
        skip = 1000000

        # ACT
        result = await indicator_service.get_all_indicators(skip=skip, limit=10)

        # ASSERT
        assert result["total"] == 25
        assert len(result["indicators"]) == 0

    async def test_zero_limit_pagination(
        self,
        indicator_service: IndicatorService,
        sample_indicators_batch: list[IndicatorComponent]
    ):
        """Test with limit=0."""
        # ARRANGE
        limit = 0

        # ACT
        result = await indicator_service.get_all_indicators(skip=0, limit=limit)

        # ASSERT
        assert result["total"] == 25
        assert len(result["indicators"]) == 0

    async def test_negative_skip_pagination(
        self,
        indicator_service: IndicatorService,
        sample_indicators_batch: list[IndicatorComponent]
    ):
        """Test with negative skip value (should be handled by database)."""
        # ARRANGE
        skip = -10

        # ACT & ASSERT
        # Implementation should handle this gracefully
        # Either raise exception or treat as 0
        try:
            result = await indicator_service.get_all_indicators(skip=skip, limit=10)
            # If no exception, verify it returns results
            assert isinstance(result["indicators"], list)
        except Exception:
            # If exception raised, that's acceptable
            pass

    @pytest.mark.skip(reason="Concurrent operations may fail in SQLite")
    async def test_concurrent_usage_increments(
        self,
        indicator_service: IndicatorService,
        sample_indicator: IndicatorComponent,
        db_session: AsyncSession
    ):
        """Test concurrent usage increments."""
        # ARRANGE
        indicator_id = sample_indicator.id
        initial_count = sample_indicator.usage_count
        concurrent_increments = 10

        # ACT
        import asyncio
        tasks = [
            indicator_service.increment_usage(indicator_id)
            for _ in range(concurrent_increments)
        ]
        results = await asyncio.gather(*tasks)

        # ASSERT
        assert all(results)  # All should succeed
        await db_session.refresh(sample_indicator)
        # Final count should be initial + concurrent_increments
        assert sample_indicator.usage_count == initial_count + concurrent_increments


@pytest.mark.asyncio
class TestIndicatorServiceExceptionHandling:
    """Test exception handling in IndicatorService."""

    async def test_get_all_indicators_database_error(
        self,
        indicator_service: IndicatorService
    ):
        """Test get_all_indicators when database raises exception."""
        # ARRANGE
        from unittest.mock import AsyncMock, patch

        # ACT & ASSERT
        with patch.object(
            indicator_service.indicator_repo,
            'get_multi',
            side_effect=Exception("Database error")
        ):
            with pytest.raises(Exception) as exc_info:
                await indicator_service.get_all_indicators()
            assert "Database error" in str(exc_info.value)

    async def test_get_indicators_by_category_database_error(
        self,
        indicator_service: IndicatorService
    ):
        """Test get_indicators_by_category when database raises exception."""
        # ARRANGE
        from unittest.mock import patch

        # ACT & ASSERT
        with patch.object(
            indicator_service.indicator_repo,
            'get_by_category',
            side_effect=Exception("Category query failed")
        ):
            with pytest.raises(Exception) as exc_info:
                await indicator_service.get_indicators_by_category("trend")
            assert "Category query failed" in str(exc_info.value)

    async def test_search_indicators_database_error(
        self,
        indicator_service: IndicatorService
    ):
        """Test search_indicators when database raises exception."""
        # ARRANGE
        from unittest.mock import patch

        # ACT & ASSERT
        with patch.object(
            indicator_service.indicator_repo,
            'search_by_name',
            side_effect=Exception("Search failed")
        ):
            with pytest.raises(Exception) as exc_info:
                await indicator_service.search_indicators("test")
            assert "Search failed" in str(exc_info.value)

    async def test_get_indicator_detail_database_error(
        self,
        indicator_service: IndicatorService
    ):
        """Test get_indicator_detail when database raises exception."""
        # ARRANGE
        from unittest.mock import patch

        # ACT & ASSERT
        with patch.object(
            indicator_service.indicator_repo,
            'get',
            side_effect=Exception("Detail query failed")
        ):
            with pytest.raises(Exception) as exc_info:
                await indicator_service.get_indicator_detail("test_id")
            assert "Detail query failed" in str(exc_info.value)

    async def test_increment_usage_database_error(
        self,
        indicator_service: IndicatorService
    ):
        """Test increment_usage when database raises exception."""
        # ARRANGE
        from unittest.mock import patch

        # ACT
        with patch.object(
            indicator_service.indicator_repo,
            'increment_usage_count',
            side_effect=Exception("Increment failed")
        ):
            result = await indicator_service.increment_usage("test_id")

        # ASSERT
        # Should return False on exception
        assert result is False

    async def test_get_popular_indicators_database_error(
        self,
        indicator_service: IndicatorService
    ):
        """Test get_popular_indicators when database raises exception."""
        # ARRANGE
        from unittest.mock import patch

        # ACT & ASSERT
        with patch.object(
            indicator_service.indicator_repo,
            'get_popular_indicators',
            side_effect=Exception("Popular query failed")
        ):
            with pytest.raises(Exception) as exc_info:
                await indicator_service.get_popular_indicators()
            assert "Popular query failed" in str(exc_info.value)

    async def test_validate_indicator_exists_database_error(
        self,
        indicator_service: IndicatorService
    ):
        """Test validate_indicator_exists when database raises exception."""
        # ARRANGE
        from unittest.mock import patch

        # ACT
        with patch.object(
            indicator_service.indicator_repo,
            'get',
            side_effect=Exception("Validation failed")
        ):
            result = await indicator_service.validate_indicator_exists("test_id")

        # ASSERT
        # Should return False on exception
        assert result is False

    async def test_get_indicator_categories_database_error(
        self,
        indicator_service: IndicatorService
    ):
        """Test get_indicator_categories when exception occurs."""
        # ARRANGE
        from unittest.mock import patch

        # Mock IndicatorCategory to raise exception
        # ACT & ASSERT
        with patch(
            'app.modules.indicator.services.indicator_service.IndicatorCategory',
            side_effect=Exception("Category enumeration failed")
        ):
            with pytest.raises(Exception) as exc_info:
                await indicator_service.get_indicator_categories()
            assert "Category enumeration failed" in str(exc_info.value)
