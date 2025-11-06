"""
TDD Tests for User Factor Library Repository

Tests all CRUD operations, filters, favorites, usage tracking, and edge cases.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.indicator import UserFactorLibrary, CustomFactor, LibraryItemStatus
from app.database.repositories.user_factor_library_repository import UserFactorLibraryRepository


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def user_library_repo(db_session: AsyncSession) -> UserFactorLibraryRepository:
    """Create UserFactorLibraryRepository instance"""
    return UserFactorLibraryRepository(db_session)


@pytest.fixture
async def sample_factor(db_session: AsyncSession) -> CustomFactor:
    """Create a sample custom factor for testing"""
    factor = CustomFactor(
        user_id="user123",
        factor_name="Test Factor",
        formula="Close / Open",
        description="Test factor",
        status="published",
        is_deleted=False
    )
    db_session.add(factor)
    await db_session.commit()
    await db_session.refresh(factor)
    return factor


@pytest.fixture
async def sample_library_items(
    db_session: AsyncSession,
    sample_factor: CustomFactor
) -> list[UserFactorLibrary]:
    """Create sample library items for testing"""
    items = []

    # Item 1: Active, not favorite, used 5 times
    item1 = UserFactorLibrary(
        user_id="user123",
        factor_id=sample_factor.id,
        is_favorite=False,
        status=LibraryItemStatus.ACTIVE.value,
        usage_count=5,
        last_used_at=datetime.now(timezone.utc),
        is_deleted=False
    )
    db_session.add(item1)
    items.append(item1)

    # Item 2: Active, favorite, used 10 times (for different user)
    factor2 = CustomFactor(
        user_id="user456",
        factor_name="Another Factor",
        formula="High - Low",
        status="published",
        is_deleted=False
    )
    db_session.add(factor2)
    await db_session.flush()

    item2 = UserFactorLibrary(
        user_id="user456",
        factor_id=factor2.id,
        is_favorite=True,
        status=LibraryItemStatus.ACTIVE.value,
        usage_count=10,
        is_deleted=False
    )
    db_session.add(item2)
    items.append(item2)

    # Item 3: Archived, not favorite (for user123)
    factor3 = CustomFactor(
        user_id="user123",
        factor_name="Archived Factor",
        formula="Volume",
        status="published",
        is_deleted=False
    )
    db_session.add(factor3)
    await db_session.flush()

    item3 = UserFactorLibrary(
        user_id="user123",
        factor_id=factor3.id,
        is_favorite=False,
        status=LibraryItemStatus.ARCHIVED.value,
        usage_count=0,
        is_deleted=False
    )
    db_session.add(item3)
    items.append(item3)

    # Item 4: Deleted (soft delete)
    factor4 = CustomFactor(
        user_id="user123",
        factor_name="Deleted Factor",
        formula="Close",
        status="draft",
        is_deleted=False
    )
    db_session.add(factor4)
    await db_session.flush()

    item4 = UserFactorLibrary(
        user_id="user123",
        factor_id=factor4.id,
        is_favorite=False,
        status=LibraryItemStatus.ACTIVE.value,
        usage_count=0,
        is_deleted=True
    )
    db_session.add(item4)
    items.append(item4)

    await db_session.commit()
    for item in items:
        await db_session.refresh(item)

    return items


# ============================================================================
# Tests: get_user_library
# ============================================================================

@pytest.mark.asyncio
class TestGetUserLibrary:
    """Tests for get_user_library method"""

    async def test_get_all_library_items(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary]
    ):
        """Test getting all library items for a user"""
        items = await user_library_repo.get_user_library(user_id="user123")

        # Should return 2 items (excluding archived and deleted)
        assert len(items) == 2
        assert all(item.user_id == "user123" for item in items)
        assert all(not item.is_deleted for item in items)

    async def test_get_library_items_with_status_filter(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary]
    ):
        """Test filtering by status"""
        items = await user_library_repo.get_user_library(
            user_id="user123",
            status=LibraryItemStatus.ACTIVE.value
        )

        assert len(items) == 1
        assert items[0].status == LibraryItemStatus.ACTIVE.value

    async def test_get_library_items_with_favorite_filter(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary]
    ):
        """Test filtering by favorite status"""
        # Make one item favorite
        items = await user_library_repo.get_user_library(user_id="user123")
        items[0].is_favorite = True
        await user_library_repo.session.commit()

        favorites = await user_library_repo.get_user_library(
            user_id="user123",
            is_favorite=True
        )

        assert len(favorites) == 1
        assert favorites[0].is_favorite is True

    async def test_get_library_items_excludes_deleted(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary]
    ):
        """Test that deleted items are excluded"""
        items = await user_library_repo.get_user_library(user_id="user123")

        deleted_ids = [item.id for item in sample_library_items if item.is_deleted]
        result_ids = [item.id for item in items]

        assert not any(del_id in result_ids for del_id in deleted_ids)

    async def test_get_library_items_pagination(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary]
    ):
        """Test pagination"""
        # Get first page
        page1 = await user_library_repo.get_user_library(
            user_id="user123",
            skip=0,
            limit=1
        )

        # Get second page
        page2 = await user_library_repo.get_user_library(
            user_id="user123",
            skip=1,
            limit=1
        )

        assert len(page1) == 1
        assert len(page2) == 1
        assert page1[0].id != page2[0].id

    async def test_get_library_items_empty_result(
        self,
        user_library_repo: UserFactorLibraryRepository
    ):
        """Test getting library for user with no items"""
        items = await user_library_repo.get_user_library(user_id="nonexistent")

        assert items == []


# ============================================================================
# Tests: get_favorites
# ============================================================================

@pytest.mark.asyncio
class TestGetFavorites:
    """Tests for get_favorites method"""

    async def test_get_favorites(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary]
    ):
        """Test getting user's favorite items"""
        favorites = await user_library_repo.get_favorites(user_id="user456")

        assert len(favorites) == 1
        assert favorites[0].is_favorite is True
        assert favorites[0].user_id == "user456"

    async def test_get_favorites_pagination(
        self,
        user_library_repo: UserFactorLibraryRepository,
        db_session: AsyncSession,
        sample_factor: CustomFactor
    ):
        """Test favorites pagination"""
        # Create multiple factors first (unique constraint on user_id + factor_id)
        factors = []
        for i in range(3):
            factor = CustomFactor(
                user_id="user789",
                factor_name=f"Factor {i}",
                formula=f"Close * {i+1}",
                status="published",
                is_deleted=False
            )
            db_session.add(factor)
            factors.append(factor)
        await db_session.flush()

        # Create library items for each factor
        for factor in factors:
            item = UserFactorLibrary(
                user_id="user789",
                factor_id=factor.id,
                is_favorite=True,
                status=LibraryItemStatus.ACTIVE.value,
                is_deleted=False
            )
            db_session.add(item)
        await db_session.commit()

        # Get with limit
        favorites = await user_library_repo.get_favorites(user_id="user789", limit=2)

        assert len(favorites) == 2

    async def test_get_favorites_empty(
        self,
        user_library_repo: UserFactorLibraryRepository
    ):
        """Test getting favorites for user with none"""
        favorites = await user_library_repo.get_favorites(user_id="user123")

        assert favorites == []


# ============================================================================
# Tests: add_to_library
# ============================================================================

@pytest.mark.asyncio
class TestAddToLibrary:
    """Tests for add_to_library method"""

    async def test_add_new_item_to_library(
        self,
        user_library_repo: UserFactorLibraryRepository,
        db_session: AsyncSession,
        sample_factor: CustomFactor
    ):
        """Test adding a new item to library"""
        result = await user_library_repo.add_to_library(
            user_id="newuser",
            factor_id=sample_factor.id,
            is_favorite=False
        )

        assert result is not None
        assert result.user_id == "newuser"
        assert result.factor_id == sample_factor.id
        assert result.is_favorite is False
        assert result.status == LibraryItemStatus.ACTIVE.value

    async def test_add_to_library_with_favorite(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_factor: CustomFactor
    ):
        """Test adding item as favorite"""
        result = await user_library_repo.add_to_library(
            user_id="newuser2",
            factor_id=sample_factor.id,
            is_favorite=True
        )

        assert result.is_favorite is True

    async def test_add_existing_item_updates(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary]
    ):
        """Test that adding existing item updates it (idempotent)"""
        existing_item = sample_library_items[0]
        factor_id = existing_item.factor_id

        # Add same item again with different favorite status
        result = await user_library_repo.add_to_library(
            user_id="user123",
            factor_id=factor_id,
            is_favorite=True
        )

        assert result.id == existing_item.id  # Same item
        assert result.is_favorite is True  # Updated
        assert result.status == LibraryItemStatus.ACTIVE.value

    async def test_add_to_library_without_factor_id(
        self,
        user_library_repo: UserFactorLibraryRepository
    ):
        """Test adding without factor_id returns None"""
        result = await user_library_repo.add_to_library(
            user_id="user123",
            factor_id=None
        )

        assert result is None

    async def test_add_to_library_with_deleted_item_fails(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary],
        db_session: AsyncSession
    ):
        """Test that adding a soft-deleted item creates constraint violation"""
        deleted_item = [item for item in sample_library_items if item.is_deleted][0]

        # First, verify the item is actually in the database but deleted
        result = await db_session.execute(
            select(UserFactorLibrary).where(
                UserFactorLibrary.user_id == deleted_item.user_id,
                UserFactorLibrary.factor_id == deleted_item.factor_id
            )
        )
        existing = result.scalar_one_or_none()
        assert existing is not None
        assert existing.is_deleted is True

        # Trying to re-add deleted item should fail with unique constraint
        # because find_library_item excludes deleted items
        # This is expected behavior - user must undelete first
        with pytest.raises(Exception):  # Will raise IntegrityError
            await user_library_repo.add_to_library(
                user_id=deleted_item.user_id,
                factor_id=deleted_item.factor_id,
                is_favorite=False
            )


# ============================================================================
# Tests: toggle_favorite
# ============================================================================

@pytest.mark.asyncio
class TestToggleFavorite:
    """Tests for toggle_favorite method"""

    async def test_toggle_favorite_on(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary]
    ):
        """Test toggling favorite from False to True"""
        item = sample_library_items[0]
        assert item.is_favorite is False

        result = await user_library_repo.toggle_favorite(str(item.id))

        assert result.is_favorite is True

    async def test_toggle_favorite_off(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary]
    ):
        """Test toggling favorite from True to False"""
        item = sample_library_items[1]  # This one is already favorite
        assert item.is_favorite is True

        result = await user_library_repo.toggle_favorite(str(item.id))

        assert result.is_favorite is False

    async def test_toggle_favorite_nonexistent(
        self,
        user_library_repo: UserFactorLibraryRepository
    ):
        """Test toggling favorite for nonexistent item"""
        result = await user_library_repo.toggle_favorite("99999")

        assert result is None


# ============================================================================
# Tests: increment_usage_count
# ============================================================================

@pytest.mark.asyncio
class TestIncrementUsageCount:
    """Tests for increment_usage_count method"""

    async def test_increment_usage_count(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary],
        db_session: AsyncSession
    ):
        """Test incrementing usage count"""
        item = sample_library_items[0]
        initial_count = item.usage_count

        success = await user_library_repo.increment_usage_count(str(item.id))

        assert success is True

        # Refresh to get updated value
        await db_session.refresh(item)
        assert item.usage_count == initial_count + 1
        assert item.last_used_at is not None

    async def test_increment_usage_updates_timestamp(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary],
        db_session: AsyncSession
    ):
        """Test that increment updates last_used_at"""
        item = sample_library_items[0]
        old_timestamp = item.last_used_at

        await user_library_repo.increment_usage_count(str(item.id))

        await db_session.refresh(item)
        assert item.last_used_at > old_timestamp

    async def test_increment_usage_nonexistent(
        self,
        user_library_repo: UserFactorLibraryRepository
    ):
        """Test incrementing usage for nonexistent item"""
        success = await user_library_repo.increment_usage_count("99999")

        assert success is False


# ============================================================================
# Tests: find_library_item
# ============================================================================

@pytest.mark.asyncio
class TestFindLibraryItem:
    """Tests for find_library_item method"""

    async def test_find_library_item_by_factor_id(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary]
    ):
        """Test finding library item by user and factor"""
        item = sample_library_items[0]

        result = await user_library_repo.find_library_item(
            user_id=item.user_id,
            factor_id=item.factor_id
        )

        assert result is not None
        assert result.id == item.id
        assert result.user_id == item.user_id

    async def test_find_library_item_without_factor_id(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary]
    ):
        """Test finding without factor_id (gets first item for user)"""
        result = await user_library_repo.find_library_item(
            user_id="user123",
            factor_id=None
        )

        assert result is not None
        assert result.user_id == "user123"

    async def test_find_library_item_excludes_deleted(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary]
    ):
        """Test that deleted items are not found"""
        deleted_item = [item for item in sample_library_items if item.is_deleted][0]

        result = await user_library_repo.find_library_item(
            user_id=deleted_item.user_id,
            factor_id=deleted_item.factor_id
        )

        # Should not find deleted item
        assert result is None

    async def test_find_library_item_nonexistent(
        self,
        user_library_repo: UserFactorLibraryRepository
    ):
        """Test finding nonexistent item"""
        result = await user_library_repo.find_library_item(
            user_id="nonexistent",
            factor_id="99999"
        )

        assert result is None


# ============================================================================
# Tests: remove_from_library
# ============================================================================

@pytest.mark.asyncio
class TestRemoveFromLibrary:
    """Tests for remove_from_library method"""

    async def test_remove_from_library_soft_delete(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary],
        db_session: AsyncSession
    ):
        """Test soft delete (default)"""
        item = sample_library_items[0]
        item_id = str(item.id)

        success = await user_library_repo.remove_from_library(item_id, soft=True)

        assert success is True

        # Verify item still exists but is marked deleted
        result = await db_session.execute(
            select(UserFactorLibrary).where(UserFactorLibrary.id == item.id)
        )
        deleted_item = result.scalar_one_or_none()

        assert deleted_item is not None
        assert deleted_item.is_deleted is True

    async def test_remove_from_library_hard_delete(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary],
        db_session: AsyncSession
    ):
        """Test hard delete"""
        item = sample_library_items[0]
        item_id = str(item.id)

        success = await user_library_repo.remove_from_library(item_id, soft=False)

        assert success is True

        # Verify item is completely removed
        result = await db_session.execute(
            select(UserFactorLibrary).where(UserFactorLibrary.id == item.id)
        )
        deleted_item = result.scalar_one_or_none()

        assert deleted_item is None

    async def test_remove_from_library_nonexistent(
        self,
        user_library_repo: UserFactorLibraryRepository
    ):
        """Test removing nonexistent item"""
        success = await user_library_repo.remove_from_library("99999")

        assert success is False


# ============================================================================
# Tests: get_most_used
# ============================================================================

@pytest.mark.asyncio
class TestGetMostUsed:
    """Tests for get_most_used method"""

    async def test_get_most_used(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary]
    ):
        """Test getting most used items"""
        # user123 has items with usage_count = 5 and 0
        most_used = await user_library_repo.get_most_used(user_id="user123", limit=10)

        assert len(most_used) == 1  # Only one with usage_count > 0
        assert most_used[0].usage_count == 5

    async def test_get_most_used_ordered_by_count(
        self,
        user_library_repo: UserFactorLibraryRepository,
        db_session: AsyncSession
    ):
        """Test that results are ordered by usage count descending"""
        # Create factors first
        factors = []
        for i, count in enumerate([3, 7, 1, 5]):
            factor = CustomFactor(
                user_id="testuser",
                factor_name=f"Ordered Factor {i}",
                formula=f"Close + {i}",
                status="published",
                is_deleted=False
            )
            db_session.add(factor)
            factors.append(factor)
        await db_session.flush()

        # Create library items with different usage counts
        for i, (factor, count) in enumerate(zip(factors, [3, 7, 1, 5])):
            item = UserFactorLibrary(
                user_id="testuser",
                factor_id=factor.id,
                status=LibraryItemStatus.ACTIVE.value,
                usage_count=count,
                is_deleted=False
            )
            db_session.add(item)
        await db_session.commit()

        most_used = await user_library_repo.get_most_used(user_id="testuser", limit=10)

        assert len(most_used) == 4
        # Should be ordered: 7, 5, 3, 1
        assert most_used[0].usage_count == 7
        assert most_used[1].usage_count == 5
        assert most_used[2].usage_count == 3
        assert most_used[3].usage_count == 1

    async def test_get_most_used_excludes_zero_usage(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary]
    ):
        """Test that items with 0 usage are excluded"""
        most_used = await user_library_repo.get_most_used(user_id="user123", limit=10)

        assert all(item.usage_count > 0 for item in most_used)

    async def test_get_most_used_respects_limit(
        self,
        user_library_repo: UserFactorLibraryRepository,
        db_session: AsyncSession
    ):
        """Test limit parameter"""
        # Create 5 factors first
        factors = []
        for i in range(5):
            factor = CustomFactor(
                user_id="limituser",
                factor_name=f"Limit Factor {i}",
                formula=f"Open * {i+1}",
                status="published",
                is_deleted=False
            )
            db_session.add(factor)
            factors.append(factor)
        await db_session.flush()

        # Create 5 items with usage
        for i, factor in enumerate(factors):
            item = UserFactorLibrary(
                user_id="limituser",
                factor_id=factor.id,
                status=LibraryItemStatus.ACTIVE.value,
                usage_count=i + 1,
                is_deleted=False
            )
            db_session.add(item)
        await db_session.commit()

        most_used = await user_library_repo.get_most_used(user_id="limituser", limit=3)

        assert len(most_used) == 3

    async def test_get_most_used_empty(
        self,
        user_library_repo: UserFactorLibraryRepository
    ):
        """Test getting most used for user with no usage"""
        most_used = await user_library_repo.get_most_used(user_id="unused_user")

        assert most_used == []


# ============================================================================
# Tests: count_user_library
# ============================================================================

@pytest.mark.asyncio
class TestCountUserLibrary:
    """Tests for count_user_library method"""

    async def test_count_all_library_items(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary]
    ):
        """Test counting all library items for user"""
        count = await user_library_repo.count_user_library(user_id="user123")

        # Should count 2 (excluding deleted)
        assert count == 2

    async def test_count_with_status_filter(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary]
    ):
        """Test counting with status filter"""
        count = await user_library_repo.count_user_library(
            user_id="user123",
            status=LibraryItemStatus.ACTIVE.value
        )

        assert count == 1

    async def test_count_with_favorite_filter(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary]
    ):
        """Test counting with favorite filter"""
        # Make one item favorite
        items = await user_library_repo.get_user_library(user_id="user123")
        items[0].is_favorite = True
        await user_library_repo.session.commit()

        count = await user_library_repo.count_user_library(
            user_id="user123",
            is_favorite=True
        )

        assert count == 1

    async def test_count_excludes_deleted(
        self,
        user_library_repo: UserFactorLibraryRepository,
        sample_library_items: list[UserFactorLibrary]
    ):
        """Test that count excludes deleted items"""
        # user123 has 3 non-deleted + 1 deleted = 4 total
        count = await user_library_repo.count_user_library(user_id="user123")

        assert count == 2  # Excludes deleted

    async def test_count_empty(
        self,
        user_library_repo: UserFactorLibraryRepository
    ):
        """Test counting for user with no items"""
        count = await user_library_repo.count_user_library(user_id="nonexistent")

        assert count == 0
