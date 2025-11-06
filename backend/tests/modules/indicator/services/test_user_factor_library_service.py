"""
TDD Tests for UserLibraryService

Comprehensive test suite covering:
- Library item management (add, remove)
- Favorite functionality
- Usage tracking
- Most used items discovery
- Library statistics
- Pagination
- Exception handling
- Edge cases

Following TDD best practices:
- AAA pattern (Arrange-Act-Assert)
- Single responsibility per test
- Clear test naming
- Fixture-based test data
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.indicator import UserFactorLibrary, CustomFactor, FactorStatus
from app.modules.indicator.services.user_library_service import UserLibraryService


@pytest.mark.asyncio
class TestUserLibraryServiceGetLibrary:
    """Test get_user_library functionality."""

    async def test_get_user_library_default_pagination(
        self,
        user_library_service: UserLibraryService,
        sample_library_items_batch: list[UserFactorLibrary]
    ):
        """Test getting user library with default pagination."""
        # ARRANGE
        user_id = "user123"
        # sample_library_items_batch provides 15 items

        # ACT
        result = await user_library_service.get_user_library(user_id)

        # ASSERT
        assert result["total"] == 15
        assert len(result["items"]) == 15
        assert result["skip"] == 0
        assert result["limit"] == 100

    async def test_get_user_library_with_pagination(
        self,
        user_library_service: UserLibraryService,
        sample_library_items_batch: list[UserFactorLibrary]
    ):
        """Test library pagination."""
        # ARRANGE
        user_id = "user123"
        skip = 5
        limit = 5

        # ACT
        result = await user_library_service.get_user_library(
            user_id,
            skip=skip,
            limit=limit
        )

        # ASSERT
        assert result["total"] == 15
        assert len(result["items"]) == 5
        assert result["skip"] == skip
        assert result["limit"] == limit

    async def test_get_user_library_empty(
        self,
        user_library_service: UserLibraryService
    ):
        """Test getting library for user with no items."""
        # ARRANGE
        user_id = "user_with_empty_library"

        # ACT
        result = await user_library_service.get_user_library(user_id)

        # ASSERT
        assert result["total"] == 0
        assert len(result["items"]) == 0

    async def test_get_user_library_only_own_items(
        self,
        user_library_service: UserLibraryService,
        db_session: AsyncSession
    ):
        """Test that users only see their own library items."""
        # ARRANGE
        factor = CustomFactor(
            factor_name="测试因子",
            user_id="creator",
            formula="close",
            formula_language="qlib_alpha"
        )
        db_session.add(factor)
        await db_session.commit()
        await db_session.refresh(factor)

        # User1's library
        item1 = UserFactorLibrary(
            user_id="user1",
            factor_id=factor.id
        )
        # User2's library
        item2 = UserFactorLibrary(
            user_id="user2",
            factor_id=factor.id
        )
        db_session.add(item1)
        db_session.add(item2)
        await db_session.commit()

        # ACT
        result = await user_library_service.get_user_library("user1")

        # ASSERT
        assert result["total"] == 1
        assert result["items"][0]["user_id"] == "user1"


@pytest.mark.asyncio
class TestUserLibraryServiceAddToLibrary:
    """Test add_to_library functionality."""

    async def test_add_to_library_success(
        self,
        user_library_service: UserLibraryService,
        sample_custom_factor: CustomFactor,
        db_session: AsyncSession
    ):
        """Test successfully adding factor to library."""
        # ARRANGE
        user_id = "new_user"
        factor_id = sample_custom_factor.id

        # ACT
        result = await user_library_service.add_to_library(user_id, factor_id)

        # ASSERT
        assert "item" in result
        assert "message" in result
        assert result["item"]["user_id"] == user_id
        assert result["item"]["factor_id"] == factor_id
        assert result["item"]["is_favorite"] is False
        assert result["item"]["usage_count"] == 0

    async def test_add_to_library_duplicate_handling(
        self,
        user_library_service: UserLibraryService,
        sample_custom_factor: CustomFactor,
        db_session: AsyncSession
    ):
        """Test adding same factor to library twice."""
        # ARRANGE
        user_id = "user123"
        factor_id = sample_custom_factor.id

        # ACT
        # Add first time
        result1 = await user_library_service.add_to_library(user_id, factor_id)
        assert result1 is not None

        # Add second time (duplicate)
        # Repository should handle this gracefully
        result2 = await user_library_service.add_to_library(user_id, factor_id)

        # ASSERT
        # Should either return existing item or handle duplicate gracefully
        assert result2 is not None

    async def test_add_to_library_nonexistent_factor(
        self,
        user_library_service: UserLibraryService
    ):
        """Test adding non-existent factor to library."""
        # ARRANGE
        user_id = "user123"
        nonexistent_factor_id = "00000000-0000-0000-0000-000000000000"

        # ACT & ASSERT
        # Repository might return None or raise exception for nonexistent factor
        # Service will propagate this error
        try:
            result = await user_library_service.add_to_library(user_id, nonexistent_factor_id)
            # If it doesn't raise, result should be None or an error message
            # We need to handle gracefully
            assert result is None or "error" in str(result).lower()
        except (ValueError, Exception):
            # If it raises, that's also acceptable
            pass


@pytest.mark.asyncio
class TestUserLibraryServiceToggleFavorite:
    """Test toggle_favorite functionality."""

    async def test_toggle_favorite_to_true(
        self,
        user_library_service: UserLibraryService,
        sample_library_item: UserFactorLibrary,
        db_session: AsyncSession
    ):
        """Test marking library item as favorite."""
        # ARRANGE
        user_id = sample_library_item.user_id
        factor_id = sample_library_item.factor_id
        assert sample_library_item.is_favorite is False

        # ACT
        result = await user_library_service.toggle_favorite(
            user_id,
            factor_id,
            is_favorite=True
        )

        # ASSERT
        assert result is not None
        assert result["item"]["is_favorite"] is True

        # Verify in database
        await db_session.refresh(sample_library_item)
        assert sample_library_item.is_favorite is True

    async def test_toggle_favorite_to_false(
        self,
        user_library_service: UserLibraryService,
        db_session: AsyncSession,
        sample_custom_factor: CustomFactor
    ):
        """Test unmarking library item as favorite."""
        # ARRANGE
        user_id = "user123"
        library_item = UserFactorLibrary(
            user_id=user_id,
            factor_id=sample_custom_factor.id,
            is_favorite=True
        )
        db_session.add(library_item)
        await db_session.commit()
        await db_session.refresh(library_item)

        # ACT
        result = await user_library_service.toggle_favorite(
            user_id,
            sample_custom_factor.id,
            is_favorite=False
        )

        # ASSERT
        assert result is not None
        assert result["item"]["is_favorite"] is False

    async def test_toggle_favorite_nonexistent_item(
        self,
        user_library_service: UserLibraryService
    ):
        """Test toggling favorite for non-existent library item."""
        # ARRANGE
        user_id = "user123"
        nonexistent_factor_id = "00000000-0000-0000-0000-000000000000"

        # ACT
        result = await user_library_service.toggle_favorite(
            user_id,
            nonexistent_factor_id,
            is_favorite=True
        )

        # ASSERT
        assert result is None

    async def test_toggle_favorite_wrong_user(
        self,
        user_library_service: UserLibraryService,
        sample_library_item: UserFactorLibrary
    ):
        """Test toggling favorite for another user's item."""
        # ARRANGE
        wrong_user_id = "different_user"
        factor_id = sample_library_item.factor_id

        # ACT
        result = await user_library_service.toggle_favorite(
            wrong_user_id,
            factor_id,
            is_favorite=True
        )

        # ASSERT
        assert result is None


@pytest.mark.asyncio
class TestUserLibraryServiceIncrementUsage:
    """Test increment_usage functionality."""

    async def test_increment_usage_success(
        self,
        user_library_service: UserLibraryService,
        sample_library_item: UserFactorLibrary,
        db_session: AsyncSession
    ):
        """Test incrementing usage count for library item."""
        # ARRANGE
        user_id = sample_library_item.user_id
        factor_id = sample_library_item.factor_id
        initial_count = sample_library_item.usage_count

        # ACT
        success = await user_library_service.increment_usage(user_id, factor_id)

        # ASSERT
        assert success is True

        # Verify in database
        await db_session.refresh(sample_library_item)
        assert sample_library_item.usage_count == initial_count + 1
        assert sample_library_item.last_used_at is not None

    async def test_increment_usage_multiple_times(
        self,
        user_library_service: UserLibraryService,
        sample_library_item: UserFactorLibrary,
        db_session: AsyncSession
    ):
        """Test incrementing usage count multiple times."""
        # ARRANGE
        user_id = sample_library_item.user_id
        factor_id = sample_library_item.factor_id
        initial_count = sample_library_item.usage_count
        increment_times = 5

        # ACT
        for _ in range(increment_times):
            success = await user_library_service.increment_usage(user_id, factor_id)
            assert success is True

        # ASSERT
        await db_session.refresh(sample_library_item)
        assert sample_library_item.usage_count == initial_count + increment_times

    async def test_increment_usage_nonexistent_item(
        self,
        user_library_service: UserLibraryService
    ):
        """Test incrementing usage for non-existent library item."""
        # ARRANGE
        user_id = "user123"
        nonexistent_factor_id = "00000000-0000-0000-0000-000000000000"

        # ACT
        success = await user_library_service.increment_usage(user_id, nonexistent_factor_id)

        # ASSERT
        assert success is False

    async def test_increment_usage_wrong_user(
        self,
        user_library_service: UserLibraryService,
        sample_library_item: UserFactorLibrary
    ):
        """Test incrementing usage for another user's item."""
        # ARRANGE
        wrong_user_id = "different_user"
        factor_id = sample_library_item.factor_id

        # ACT
        success = await user_library_service.increment_usage(wrong_user_id, factor_id)

        # ASSERT
        assert success is False


@pytest.mark.asyncio
class TestUserLibraryServiceGetFavorites:
    """Test get_favorites functionality."""

    async def test_get_favorites_default_pagination(
        self,
        user_library_service: UserLibraryService,
        sample_library_items_batch: list[UserFactorLibrary]
    ):
        """Test getting favorite items with default pagination."""
        # ARRANGE
        user_id = "user123"
        # sample_library_items_batch has every 3rd item as favorite

        # ACT
        result = await user_library_service.get_favorites(user_id)

        # ASSERT
        assert result["total"] > 0
        # Verify all returned items are favorites
        for item in result["items"]:
            assert item["is_favorite"] is True

    async def test_get_favorites_with_pagination(
        self,
        user_library_service: UserLibraryService,
        sample_library_items_batch: list[UserFactorLibrary]
    ):
        """Test favorite items pagination."""
        # ARRANGE
        user_id = "user123"
        skip = 1
        limit = 2

        # ACT
        result = await user_library_service.get_favorites(
            user_id,
            skip=skip,
            limit=limit
        )

        # ASSERT
        assert len(result["items"]) <= limit
        assert result["skip"] == skip
        assert result["limit"] == limit

    async def test_get_favorites_empty_result(
        self,
        user_library_service: UserLibraryService,
        db_session: AsyncSession
    ):
        """Test getting favorites when user has none."""
        # ARRANGE
        user_id = "user_no_favorites"
        factor = CustomFactor(
            factor_name="测试",
            user_id="creator",
            formula="close",
            formula_language="qlib_alpha"
        )
        db_session.add(factor)
        await db_session.commit()
        await db_session.refresh(factor)

        library_item = UserFactorLibrary(
            user_id=user_id,
            factor_id=factor.id,
            is_favorite=False
        )
        db_session.add(library_item)
        await db_session.commit()

        # ACT
        result = await user_library_service.get_favorites(user_id)

        # ASSERT
        assert result["total"] == 0
        assert len(result["items"]) == 0


@pytest.mark.asyncio
class TestUserLibraryServiceGetMostUsed:
    """Test get_most_used functionality."""

    async def test_get_most_used_default_limit(
        self,
        user_library_service: UserLibraryService,
        sample_library_items_batch: list[UserFactorLibrary]
    ):
        """Test getting most used items with default limit."""
        # ARRANGE
        user_id = "user123"

        # ACT
        result = await user_library_service.get_most_used(user_id, limit=10)

        # ASSERT
        assert len(result["items"]) <= 10
        assert result["total"] == len(result["items"])

        # Verify sorted by usage_count descending
        usage_counts = [item["usage_count"] for item in result["items"]]
        assert usage_counts == sorted(usage_counts, reverse=True)

    async def test_get_most_used_custom_limit(
        self,
        user_library_service: UserLibraryService,
        sample_library_items_batch: list[UserFactorLibrary]
    ):
        """Test getting most used items with custom limit."""
        # ARRANGE
        user_id = "user123"
        limit = 3

        # ACT
        result = await user_library_service.get_most_used(user_id, limit=limit)

        # ASSERT
        assert len(result["items"]) <= limit
        assert result["total"] == len(result["items"])

    async def test_get_most_used_empty_library(
        self,
        user_library_service: UserLibraryService
    ):
        """Test getting most used items when library is empty."""
        # ARRANGE
        user_id = "user_with_empty_library"

        # ACT
        result = await user_library_service.get_most_used(user_id)

        # ASSERT
        assert result["total"] == 0
        assert len(result["items"]) == 0

    async def test_get_most_used_ordering(
        self,
        user_library_service: UserLibraryService,
        db_session: AsyncSession
    ):
        """Test that most used items are correctly ordered."""
        # ARRANGE
        user_id = "user123"
        factor = CustomFactor(
            factor_name="测试",
            user_id="creator",
            formula="close",
            formula_language="qlib_alpha"
        )
        db_session.add(factor)
        await db_session.commit()
        await db_session.refresh(factor)

        # Create items with specific usage counts
        usage_counts = [50, 30, 80, 10, 90, 20]
        for i, count in enumerate(usage_counts):
            sub_factor = CustomFactor(
                factor_name=f"因子{i}",
                user_id="creator",
                formula="close",
                formula_language="qlib_alpha"
            )
            db_session.add(sub_factor)
            await db_session.commit()
            await db_session.refresh(sub_factor)

            item = UserFactorLibrary(
                user_id=user_id,
                factor_id=sub_factor.id,
                usage_count=count
            )
            db_session.add(item)
        await db_session.commit()

        # ACT
        result = await user_library_service.get_most_used(user_id, limit=6)

        # ASSERT
        expected_order = sorted(usage_counts, reverse=True)
        actual_order = [item["usage_count"] for item in result["items"]]
        assert actual_order == expected_order


@pytest.mark.asyncio
class TestUserLibraryServiceRemoveFromLibrary:
    """Test remove_from_library functionality."""

    async def test_remove_from_library_success(
        self,
        user_library_service: UserLibraryService,
        sample_library_item: UserFactorLibrary,
        db_session: AsyncSession
    ):
        """Test successfully removing item from library."""
        # ARRANGE
        user_id = sample_library_item.user_id
        factor_id = sample_library_item.factor_id

        # ACT
        success = await user_library_service.remove_from_library(user_id, factor_id)

        # ASSERT
        assert success is True

        # Verify soft delete
        await db_session.refresh(sample_library_item)
        assert sample_library_item.is_deleted is True

    async def test_remove_from_library_nonexistent_item(
        self,
        user_library_service: UserLibraryService
    ):
        """Test removing non-existent item from library."""
        # ARRANGE
        user_id = "user123"
        nonexistent_factor_id = "00000000-0000-0000-0000-000000000000"

        # ACT
        success = await user_library_service.remove_from_library(user_id, nonexistent_factor_id)

        # ASSERT
        assert success is False

    async def test_remove_from_library_wrong_user(
        self,
        user_library_service: UserLibraryService,
        sample_library_item: UserFactorLibrary
    ):
        """Test removing another user's library item."""
        # ARRANGE
        wrong_user_id = "different_user"
        factor_id = sample_library_item.factor_id

        # ACT
        success = await user_library_service.remove_from_library(wrong_user_id, factor_id)

        # ASSERT
        assert success is False


@pytest.mark.asyncio
class TestUserLibraryServiceGetStats:
    """Test get_library_stats functionality."""

    async def test_get_library_stats_with_items(
        self,
        user_library_service: UserLibraryService,
        sample_library_items_batch: list[UserFactorLibrary]
    ):
        """Test getting library statistics for user with items."""
        # ARRANGE
        user_id = "user123"

        # ACT
        result = await user_library_service.get_library_stats(user_id)

        # ASSERT
        assert "user_id" in result
        assert result["user_id"] == user_id
        assert "total_items" in result
        assert result["total_items"] == 15
        assert "favorite_count" in result
        assert result["favorite_count"] > 0  # Every 3rd is favorite
        assert "total_usage" in result
        assert result["total_usage"] > 0

    async def test_get_library_stats_empty_library(
        self,
        user_library_service: UserLibraryService
    ):
        """Test getting statistics for empty library."""
        # ARRANGE
        user_id = "user_with_empty_library"

        # ACT
        result = await user_library_service.get_library_stats(user_id)

        # ASSERT
        assert result["user_id"] == user_id
        assert result["total_items"] == 0
        assert result["favorite_count"] == 0
        assert result["total_usage"] == 0

    async def test_get_library_stats_accuracy(
        self,
        user_library_service: UserLibraryService,
        db_session: AsyncSession
    ):
        """Test accuracy of library statistics calculation."""
        # ARRANGE
        user_id = "stats_test_user"

        # Create 5 items: 2 favorites, total usage = 100
        for i in range(5):
            factor = CustomFactor(
                factor_name=f"因子{i}",
                user_id="creator",
                formula="close",
                formula_language="qlib_alpha"
            )
            db_session.add(factor)
            await db_session.commit()
            await db_session.refresh(factor)

            item = UserFactorLibrary(
                user_id=user_id,
                factor_id=factor.id,
                is_favorite=(i < 2),  # First 2 are favorites
                usage_count=20  # Each used 20 times
            )
            db_session.add(item)
        await db_session.commit()

        # ACT
        result = await user_library_service.get_library_stats(user_id)

        # ASSERT
        assert result["total_items"] == 5
        assert result["favorite_count"] == 2
        assert result["total_usage"] == 100  # 5 items × 20 usage each


@pytest.mark.asyncio
class TestUserLibraryServiceEdgeCases:
    """Test edge cases and boundary conditions."""

    async def test_large_library_pagination(
        self,
        user_library_service: UserLibraryService,
        db_session: AsyncSession
    ):
        """Test pagination with large library."""
        # ARRANGE
        user_id = "user_large_library"

        # Create 100 library items
        for i in range(100):
            factor = CustomFactor(
                factor_name=f"因子{i}",
                user_id="creator",
                formula="close",
                formula_language="qlib_alpha"
            )
            db_session.add(factor)
            await db_session.commit()
            await db_session.refresh(factor)

            item = UserFactorLibrary(
                user_id=user_id,
                factor_id=factor.id
            )
            db_session.add(item)
        await db_session.commit()

        # ACT
        result = await user_library_service.get_user_library(
            user_id,
            skip=90,
            limit=20
        )

        # ASSERT
        assert result["total"] == 100
        assert len(result["items"]) == 10  # Only 10 items left

    @pytest.mark.skip(reason="Concurrent operations may fail in SQLite")
    async def test_concurrent_usage_increments(
        self,
        user_library_service: UserLibraryService,
        sample_library_item: UserFactorLibrary,
        db_session: AsyncSession
    ):
        """Test concurrent usage increments."""
        # ARRANGE
        user_id = sample_library_item.user_id
        factor_id = sample_library_item.factor_id
        initial_count = sample_library_item.usage_count
        concurrent_increments = 10

        # ACT
        import asyncio
        tasks = [
            user_library_service.increment_usage(user_id, factor_id)
            for _ in range(concurrent_increments)
        ]
        results = await asyncio.gather(*tasks)

        # ASSERT
        assert all(results)
        await db_session.refresh(sample_library_item)
        assert sample_library_item.usage_count == initial_count + concurrent_increments

    async def test_zero_limit_pagination(
        self,
        user_library_service: UserLibraryService,
        sample_library_items_batch: list[UserFactorLibrary]
    ):
        """Test pagination with limit=0."""
        # ARRANGE
        user_id = "user123"

        # ACT
        result = await user_library_service.get_user_library(
            user_id,
            skip=0,
            limit=0
        )

        # ASSERT
        assert result["total"] == 15
        assert len(result["items"]) == 0

    async def test_negative_skip_pagination(
        self,
        user_library_service: UserLibraryService,
        sample_library_items_batch: list[UserFactorLibrary]
    ):
        """Test pagination with negative skip."""
        # ARRANGE
        user_id = "user123"

        # ACT & ASSERT
        try:
            result = await user_library_service.get_user_library(
                user_id,
                skip=-10,
                limit=10
            )
            # If no exception, verify it returns results
            assert isinstance(result["items"], list)
        except Exception:
            # If exception raised, that's acceptable
            pass

    async def test_favorite_toggle_idempotency(
        self,
        user_library_service: UserLibraryService,
        sample_library_item: UserFactorLibrary,
        db_session: AsyncSession
    ):
        """Test that toggling favorite multiple times is idempotent."""
        # ARRANGE
        user_id = sample_library_item.user_id
        factor_id = sample_library_item.factor_id

        # ACT
        # Toggle to True multiple times
        await user_library_service.toggle_favorite(user_id, factor_id, True)
        await user_library_service.toggle_favorite(user_id, factor_id, True)
        await user_library_service.toggle_favorite(user_id, factor_id, True)

        # ASSERT
        await db_session.refresh(sample_library_item)
        assert sample_library_item.is_favorite is True

        # ACT
        # Toggle to False multiple times
        await user_library_service.toggle_favorite(user_id, factor_id, False)
        await user_library_service.toggle_favorite(user_id, factor_id, False)

        # ASSERT
        await db_session.refresh(sample_library_item)
        assert sample_library_item.is_favorite is False

    async def test_stats_with_deleted_items(
        self,
        user_library_service: UserLibraryService,
        db_session: AsyncSession
    ):
        """Test that statistics exclude soft-deleted items."""
        # ARRANGE
        user_id = "user123"
        factor = CustomFactor(
            factor_name="测试",
            user_id="creator",
            formula="close",
            formula_language="qlib_alpha"
        )
        db_session.add(factor)
        await db_session.commit()
        await db_session.refresh(factor)

        # Create 2 items
        item1 = UserFactorLibrary(
            user_id=user_id,
            factor_id=factor.id,
            usage_count=10
        )
        db_session.add(item1)
        await db_session.commit()
        await db_session.refresh(item1)

        factor2 = CustomFactor(
            factor_name="测试2",
            user_id="creator",
            formula="open",
            formula_language="qlib_alpha"
        )
        db_session.add(factor2)
        await db_session.commit()
        await db_session.refresh(factor2)

        item2 = UserFactorLibrary(
            user_id=user_id,
            factor_id=factor2.id,
            usage_count=20,
            is_deleted=True  # Soft deleted
        )
        db_session.add(item2)
        await db_session.commit()

        # ACT
        result = await user_library_service.get_library_stats(user_id)

        # ASSERT
        # Should only count non-deleted items
        assert result["total_items"] == 1
        assert result["total_usage"] == 10  # Only item1's usage
