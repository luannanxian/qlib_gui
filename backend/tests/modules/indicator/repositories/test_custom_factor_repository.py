"""
TDD Tests for CustomFactorRepository

Tests the new count methods for accurate pagination.
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import CustomFactor
from app.database.repositories.custom_factor_repository import CustomFactorRepository


@pytest.mark.asyncio
class TestCustomFactorRepositoryCount:
    """Test count methods for custom factors."""

    async def test_count_user_factors_all(self, db_session: AsyncSession):
        """Test counting all user factors."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)
        user_id = "test_user_123"

        factors = [
            CustomFactor(
                factor_name=f"Factor_{i}",
                user_id=user_id,
                formula=f"close * {i}",
                formula_language="qlib_alpha",
                status="draft",
                is_deleted=False
            )
            for i in range(5)
        ]

        for factor in factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        count = await repo.count_user_factors(user_id=user_id)

        # ASSERT
        assert count == 5

    async def test_count_user_factors_by_status(self, db_session: AsyncSession):
        """Test counting user factors filtered by status."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)
        user_id = "test_user_123"

        # Create factors with different statuses
        draft_factors = [
            CustomFactor(
                factor_name=f"Draft_{i}",
                user_id=user_id,
                formula="close",
                formula_language="qlib_alpha",
                status="draft",
                is_deleted=False
            )
            for i in range(3)
        ]

        published_factors = [
            CustomFactor(
                factor_name=f"Published_{i}",
                user_id=user_id,
                formula="open",
                formula_language="qlib_alpha",
                status="published",
                is_deleted=False
            )
            for i in range(2)
        ]

        for factor in draft_factors + published_factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        draft_count = await repo.count_user_factors(user_id=user_id, status="draft")
        published_count = await repo.count_user_factors(user_id=user_id, status="published")

        # ASSERT
        assert draft_count == 3
        assert published_count == 2

    async def test_count_user_factors_excludes_deleted(self, db_session: AsyncSession):
        """Test that count excludes soft-deleted factors."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)
        user_id = "test_user_123"

        active = CustomFactor(
            factor_name="Active",
            user_id=user_id,
            formula="close",
            formula_language="qlib_alpha",
            status="draft",
            is_deleted=False
        )

        deleted = CustomFactor(
            factor_name="Deleted",
            user_id=user_id,
            formula="open",
            formula_language="qlib_alpha",
            status="draft",
            is_deleted=True
        )

        db_session.add(active)
        db_session.add(deleted)
        await db_session.commit()

        # ACT
        count = await repo.count_user_factors(user_id=user_id)

        # ASSERT: Should only count active
        assert count == 1

    async def test_count_user_factors_filters_by_user(self, db_session: AsyncSession):
        """Test that count only returns factors for specific user."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        user1_factors = [
            CustomFactor(
                factor_name=f"User1_Factor_{i}",
                user_id="user1",
                formula="close",
                formula_language="qlib_alpha",
                status="draft",
                is_deleted=False
            )
            for i in range(3)
        ]

        user2_factors = [
            CustomFactor(
                factor_name=f"User2_Factor_{i}",
                user_id="user2",
                formula="open",
                formula_language="qlib_alpha",
                status="draft",
                is_deleted=False
            )
            for i in range(2)
        ]

        for factor in user1_factors + user2_factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        user1_count = await repo.count_user_factors(user_id="user1")
        user2_count = await repo.count_user_factors(user_id="user2")

        # ASSERT
        assert user1_count == 3
        assert user2_count == 2

    async def test_count_search_results(self, db_session: AsyncSession):
        """Test counting search results."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        factors = [
            CustomFactor(
                factor_name="Moving Average Factor",
                user_id="user1",
                formula="close.rolling(20).mean()",
                formula_language="qlib_alpha",
                status="published",
                is_deleted=False
            ),
            CustomFactor(
                factor_name="Exponential Moving Avg",
                user_id="user1",
                formula="close.ewm(20).mean()",
                formula_language="qlib_alpha",
                status="published",
                is_deleted=False
            ),
            CustomFactor(
                factor_name="RSI Factor",
                user_id="user2",
                formula="rsi(14)",
                formula_language="qlib_alpha",
                status="published",
                is_deleted=False
            ),
        ]

        for factor in factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT: Search for "Moving"
        count = await repo.count_search_results(keyword="Moving")

        # ASSERT: Should find 2 factors
        assert count == 2

    async def test_count_search_results_with_user_filter(self, db_session: AsyncSession):
        """Test counting search results filtered by user."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        factors = [
            CustomFactor(
                factor_name="Test Factor 1",
                user_id="user1",
                formula="close",
                formula_language="qlib_alpha",
                status="published",
                is_deleted=False
            ),
            CustomFactor(
                factor_name="Test Factor 2",
                user_id="user2",
                formula="open",
                formula_language="qlib_alpha",
                status="published",
                is_deleted=False
            ),
        ]

        for factor in factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT: Search with user filter
        count_user1 = await repo.count_search_results(keyword="Test", user_id="user1")
        count_user2 = await repo.count_search_results(keyword="Test", user_id="user2")

        # ASSERT
        assert count_user1 == 1
        assert count_user2 == 1

    async def test_count_public_factors(self, db_session: AsyncSession):
        """Test counting public published factors."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        # Create public and private factors
        public_factors = [
            CustomFactor(
                factor_name=f"Public_{i}",
                user_id="user1",
                formula="close",
                formula_language="qlib_alpha",
                status="published",
                is_public=True,
                is_deleted=False
            )
            for i in range(3)
        ]

        private_factors = [
            CustomFactor(
                factor_name=f"Private_{i}",
                user_id="user1",
                formula="open",
                formula_language="qlib_alpha",
                status="published",
                is_public=False,
                is_deleted=False
            )
            for i in range(2)
        ]

        for factor in public_factors + private_factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        count = await repo.count_public_factors()

        # ASSERT: Should only count public published factors
        assert count == 3

    async def test_count_public_factors_only_published(self, db_session: AsyncSession):
        """Test that count_public_factors only counts published factors."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        published_public = CustomFactor(
            factor_name="Published Public",
            user_id="user1",
            formula="close",
            formula_language="qlib_alpha",
            status="published",
            is_public=True,
            is_deleted=False
        )

        draft_public = CustomFactor(
            factor_name="Draft Public",
            user_id="user1",
            formula="open",
            formula_language="qlib_alpha",
            status="draft",
            is_public=True,
            is_deleted=False
        )

        db_session.add(published_public)
        db_session.add(draft_public)
        await db_session.commit()

        # ACT
        count = await repo.count_public_factors()

        # ASSERT: Should only count published
        assert count == 1


@pytest.mark.asyncio
class TestCustomFactorRepositoryGetUserFactors:
    """Test get_user_factors method for retrieving user's custom factors."""

    async def test_get_user_factors_all_statuses(self, db_session: AsyncSession):
        """Test retrieving all user factors without status filter."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)
        user_id = "test_user_123"

        factors = [
            CustomFactor(
                factor_name=f"Factor_{i}",
                user_id=user_id,
                formula=f"close * {i}",
                formula_language="qlib_alpha",
                status="draft" if i % 2 == 0 else "published",
                is_deleted=False
            )
            for i in range(5)
        ]

        for factor in factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        result = await repo.get_user_factors(user_id=user_id)

        # ASSERT
        assert len(result) == 5
        assert all(f.user_id == user_id for f in result)

    async def test_get_user_factors_filtered_by_status(self, db_session: AsyncSession):
        """Test retrieving user factors filtered by specific status."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)
        user_id = "test_user_123"

        draft_factors = [
            CustomFactor(
                factor_name=f"Draft_{i}",
                user_id=user_id,
                formula="close",
                formula_language="qlib_alpha",
                status="draft",
                is_deleted=False
            )
            for i in range(3)
        ]

        published_factors = [
            CustomFactor(
                factor_name=f"Published_{i}",
                user_id=user_id,
                formula="open",
                formula_language="qlib_alpha",
                status="published",
                is_deleted=False
            )
            for i in range(2)
        ]

        for factor in draft_factors + published_factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        drafts = await repo.get_user_factors(user_id=user_id, status="draft")
        published = await repo.get_user_factors(user_id=user_id, status="published")

        # ASSERT
        assert len(drafts) == 3
        assert all(f.status == "draft" for f in drafts)
        assert len(published) == 2
        assert all(f.status == "published" for f in published)

    async def test_get_user_factors_excludes_deleted(self, db_session: AsyncSession):
        """Test that get_user_factors excludes soft-deleted factors."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)
        user_id = "test_user_123"

        active = CustomFactor(
            factor_name="Active",
            user_id=user_id,
            formula="close",
            formula_language="qlib_alpha",
            status="draft",
            is_deleted=False
        )

        deleted = CustomFactor(
            factor_name="Deleted",
            user_id=user_id,
            formula="open",
            formula_language="qlib_alpha",
            status="draft",
            is_deleted=True
        )

        db_session.add(active)
        db_session.add(deleted)
        await db_session.commit()

        # ACT
        result = await repo.get_user_factors(user_id=user_id)

        # ASSERT
        assert len(result) == 1
        assert result[0].factor_name == "Active"

    async def test_get_user_factors_pagination(self, db_session: AsyncSession):
        """Test pagination with skip and limit parameters."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)
        user_id = "test_user_123"

        factors = [
            CustomFactor(
                factor_name=f"Factor_{i:02d}",
                user_id=user_id,
                formula="close",
                formula_language="qlib_alpha",
                status="draft",
                is_deleted=False
            )
            for i in range(10)
        ]

        for factor in factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        page1 = await repo.get_user_factors(user_id=user_id, skip=0, limit=3)
        page2 = await repo.get_user_factors(user_id=user_id, skip=3, limit=3)

        # ASSERT
        assert len(page1) == 3
        assert len(page2) == 3
        # Ensure no overlap
        page1_ids = {f.id for f in page1}
        page2_ids = {f.id for f in page2}
        assert len(page1_ids & page2_ids) == 0

    async def test_get_user_factors_ordered_by_created_at(self, db_session: AsyncSession):
        """Test that results are ordered by created_at DESC."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)
        user_id = "test_user_123"

        # Create factors with different timestamps
        import time
        factors = []
        for i in range(3):
            factor = CustomFactor(
                factor_name=f"Factor_{i}",
                user_id=user_id,
                formula="close",
                formula_language="qlib_alpha",
                status="draft",
                is_deleted=False
            )
            db_session.add(factor)
            await db_session.commit()
            await db_session.refresh(factor)
            factors.append(factor)
            time.sleep(0.01)  # Small delay to ensure different timestamps

        # ACT
        result = await repo.get_user_factors(user_id=user_id)

        # ASSERT
        assert len(result) == 3
        # Should be in reverse order (newest first)
        for i in range(len(result) - 1):
            assert result[i].created_at >= result[i + 1].created_at


@pytest.mark.asyncio
class TestCustomFactorRepositoryGetPublicFactors:
    """Test get_public_factors method for discovering public factors."""

    async def test_get_public_factors_returns_only_public_published(self, db_session: AsyncSession):
        """Test that only public and published factors are returned."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        public_published = CustomFactor(
            factor_name="Public Published",
            user_id="user1",
            formula="close",
            formula_language="qlib_alpha",
            status="published",
            is_public=True,
            is_deleted=False,
            usage_count=5
        )

        private_published = CustomFactor(
            factor_name="Private Published",
            user_id="user1",
            formula="open",
            formula_language="qlib_alpha",
            status="published",
            is_public=False,
            is_deleted=False,
            usage_count=10
        )

        public_draft = CustomFactor(
            factor_name="Public Draft",
            user_id="user1",
            formula="high",
            formula_language="qlib_alpha",
            status="draft",
            is_public=True,
            is_deleted=False,
            usage_count=3
        )

        db_session.add(public_published)
        db_session.add(private_published)
        db_session.add(public_draft)
        await db_session.commit()

        # ACT
        result = await repo.get_public_factors()

        # ASSERT
        assert len(result) == 1
        assert result[0].factor_name == "Public Published"
        assert result[0].is_public is True
        assert result[0].status == "published"

    async def test_get_public_factors_ordered_by_usage_count(self, db_session: AsyncSession):
        """Test that results are ordered by usage_count DESC."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        factors = [
            CustomFactor(
                factor_name=f"Factor_{i}",
                user_id="user1",
                formula="close",
                formula_language="qlib_alpha",
                status="published",
                is_public=True,
                is_deleted=False,
                usage_count=i * 10  # Different usage counts
            )
            for i in range(1, 5)
        ]

        for factor in factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        result = await repo.get_public_factors()

        # ASSERT
        assert len(result) == 4
        # Should be ordered by usage_count DESC
        assert result[0].usage_count == 40
        assert result[1].usage_count == 30
        assert result[2].usage_count == 20
        assert result[3].usage_count == 10

    async def test_get_public_factors_pagination(self, db_session: AsyncSession):
        """Test pagination with skip and limit."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        factors = [
            CustomFactor(
                factor_name=f"Factor_{i}",
                user_id="user1",
                formula="close",
                formula_language="qlib_alpha",
                status="published",
                is_public=True,
                is_deleted=False,
                usage_count=i
            )
            for i in range(10)
        ]

        for factor in factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        page1 = await repo.get_public_factors(skip=0, limit=3)
        page2 = await repo.get_public_factors(skip=3, limit=3)

        # ASSERT
        assert len(page1) == 3
        assert len(page2) == 3


@pytest.mark.asyncio
class TestCustomFactorRepositoryPublishFactor:
    """Test publish_factor method for publishing factors."""

    async def test_publish_factor_success(self, db_session: AsyncSession):
        """Test successfully publishing a draft factor."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        factor = CustomFactor(
            factor_name="Draft Factor",
            user_id="user1",
            formula="close",
            formula_language="qlib_alpha",
            status="draft",
            is_deleted=False
        )

        db_session.add(factor)
        await db_session.commit()
        await db_session.refresh(factor)
        factor_id = factor.id

        # ACT
        result = await repo.publish_factor(factor_id)

        # ASSERT
        assert result is not None
        assert result.status == "published"
        assert result.published_at is not None

    async def test_publish_factor_not_found(self, db_session: AsyncSession):
        """Test publishing a non-existent factor returns None."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)
        non_existent_id = "00000000-0000-0000-0000-000000000000"

        # ACT
        result = await repo.publish_factor(non_existent_id)

        # ASSERT
        assert result is None


@pytest.mark.asyncio
class TestCustomFactorRepositoryMakePublic:
    """Test make_public method for making factors public."""

    async def test_make_public_success(self, db_session: AsyncSession):
        """Test successfully making a published factor public."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        factor = CustomFactor(
            factor_name="Published Factor",
            user_id="user1",
            formula="close",
            formula_language="qlib_alpha",
            status="published",
            is_public=False,
            is_deleted=False
        )

        db_session.add(factor)
        await db_session.commit()
        await db_session.refresh(factor)
        factor_id = factor.id

        # ACT
        result = await repo.make_public(factor_id)

        # ASSERT
        assert result is not None
        assert result.is_public is True
        assert result.shared_at is not None

    async def test_make_public_not_found(self, db_session: AsyncSession):
        """Test making a non-existent factor public returns None."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)
        non_existent_id = "00000000-0000-0000-0000-000000000000"

        # ACT
        result = await repo.make_public(non_existent_id)

        # ASSERT
        assert result is None

    async def test_make_public_unpublished_factor_fails(self, db_session: AsyncSession):
        """Test that making an unpublished factor public fails."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        draft_factor = CustomFactor(
            factor_name="Draft Factor",
            user_id="user1",
            formula="close",
            formula_language="qlib_alpha",
            status="draft",
            is_public=False,
            is_deleted=False
        )

        db_session.add(draft_factor)
        await db_session.commit()
        await db_session.refresh(draft_factor)
        factor_id = draft_factor.id

        # ACT
        result = await repo.make_public(factor_id)

        # ASSERT: Should return None because factor is not published
        assert result is None


@pytest.mark.asyncio
class TestCustomFactorRepositoryCloneFactor:
    """Test clone_factor method for cloning factors."""

    async def test_clone_factor_success(self, db_session: AsyncSession):
        """Test successfully cloning a factor."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        original = CustomFactor(
            factor_name="Original Factor",
            user_id="user1",
            formula="close * 2",
            formula_language="qlib_alpha",
            description="Original description",
            status="published",
            is_public=True,
            is_deleted=False,
            clone_count=0
        )

        db_session.add(original)
        await db_session.commit()
        await db_session.refresh(original)
        original_id = original.id

        # ACT
        cloned = await repo.clone_factor(
            factor_id=original_id,
            new_user_id="user2",
            new_factor_name="Cloned Factor"
        )

        # ASSERT
        assert cloned is not None
        assert cloned.factor_name == "Cloned Factor"
        assert cloned.user_id == "user2"
        assert cloned.formula == original.formula
        assert cloned.status == "draft"
        assert cloned.is_public is False
        assert cloned.cloned_from_id == original_id

        # Verify original's clone count was incremented
        await db_session.refresh(original)
        assert original.clone_count == 1

    async def test_clone_factor_default_name(self, db_session: AsyncSession):
        """Test cloning a factor with default name (uses original name)."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        original = CustomFactor(
            factor_name="Original Factor",
            user_id="user1",
            formula="close",
            formula_language="qlib_alpha",
            status="published",
            is_deleted=False
        )

        db_session.add(original)
        await db_session.commit()
        await db_session.refresh(original)
        original_id = original.id

        # ACT
        cloned = await repo.clone_factor(
            factor_id=original_id,
            new_user_id="user2"
        )

        # ASSERT
        assert cloned is not None
        assert cloned.factor_name == "Original Factor"

    async def test_clone_factor_not_found(self, db_session: AsyncSession):
        """Test cloning a non-existent factor returns None."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)
        non_existent_id = "00000000-0000-0000-0000-000000000000"

        # ACT
        result = await repo.clone_factor(
            factor_id=non_existent_id,
            new_user_id="user2"
        )

        # ASSERT
        assert result is None


@pytest.mark.asyncio
class TestCustomFactorRepositoryIncrementUsageCount:
    """Test increment_usage_count method for tracking factor usage."""

    async def test_increment_usage_count_success(self, db_session: AsyncSession):
        """Test successfully incrementing usage count."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        factor = CustomFactor(
            factor_name="Test Factor",
            user_id="user1",
            formula="close",
            formula_language="qlib_alpha",
            status="published",
            is_deleted=False,
            usage_count=5
        )

        db_session.add(factor)
        await db_session.commit()
        await db_session.refresh(factor)
        factor_id = factor.id

        # ACT
        result = await repo.increment_usage_count(factor_id)

        # ASSERT
        assert result is True
        await db_session.refresh(factor)
        assert factor.usage_count == 6

    async def test_increment_usage_count_not_found(self, db_session: AsyncSession):
        """Test incrementing usage count for non-existent factor returns False."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)
        non_existent_id = "00000000-0000-0000-0000-000000000000"

        # ACT
        result = await repo.increment_usage_count(non_existent_id)

        # ASSERT
        assert result is False


@pytest.mark.asyncio
class TestCustomFactorRepositorySearchByName:
    """Test search_by_name method for searching factors."""

    async def test_search_by_name_matches_factor_name(self, db_session: AsyncSession):
        """Test searching factors by name."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        factors = [
            CustomFactor(
                factor_name="Moving Average",
                user_id="user1",
                formula="close",
                formula_language="qlib_alpha",
                status="published",
                is_deleted=False,
                usage_count=10
            ),
            CustomFactor(
                factor_name="Exponential Moving Average",
                user_id="user1",
                formula="close",
                formula_language="qlib_alpha",
                status="published",
                is_deleted=False,
                usage_count=5
            ),
            CustomFactor(
                factor_name="RSI",
                user_id="user1",
                formula="close",
                formula_language="qlib_alpha",
                status="published",
                is_deleted=False,
                usage_count=3
            ),
        ]

        for factor in factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        result = await repo.search_by_name(keyword="Moving")

        # ASSERT
        assert len(result) == 2
        assert all("Moving" in f.factor_name for f in result)
        # Should be ordered by usage_count DESC
        assert result[0].usage_count >= result[1].usage_count

    async def test_search_by_name_matches_description(self, db_session: AsyncSession):
        """Test searching factors by description."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        factors = [
            CustomFactor(
                factor_name="Factor 1",
                description="This calculates momentum",
                user_id="user1",
                formula="close",
                formula_language="qlib_alpha",
                status="published",
                is_deleted=False
            ),
            CustomFactor(
                factor_name="Factor 2",
                description="Trend following strategy",
                user_id="user1",
                formula="close",
                formula_language="qlib_alpha",
                status="published",
                is_deleted=False
            ),
        ]

        for factor in factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        result = await repo.search_by_name(keyword="momentum")

        # ASSERT
        assert len(result) == 1
        assert "momentum" in result[0].description

    async def test_search_by_name_with_user_filter(self, db_session: AsyncSession):
        """Test searching factors filtered by user."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        factors = [
            CustomFactor(
                factor_name="Test Factor",
                user_id="user1",
                formula="close",
                formula_language="qlib_alpha",
                status="published",
                is_deleted=False
            ),
            CustomFactor(
                factor_name="Test Factor",
                user_id="user2",
                formula="close",
                formula_language="qlib_alpha",
                status="published",
                is_deleted=False
            ),
        ]

        for factor in factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        user1_results = await repo.search_by_name(keyword="Test", user_id="user1")
        user2_results = await repo.search_by_name(keyword="Test", user_id="user2")

        # ASSERT
        assert len(user1_results) == 1
        assert user1_results[0].user_id == "user1"
        assert len(user2_results) == 1
        assert user2_results[0].user_id == "user2"

    async def test_search_by_name_excludes_deleted(self, db_session: AsyncSession):
        """Test that search excludes soft-deleted factors."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        active = CustomFactor(
            factor_name="Active Factor",
            user_id="user1",
            formula="close",
            formula_language="qlib_alpha",
            status="published",
            is_deleted=False
        )

        deleted = CustomFactor(
            factor_name="Deleted Factor",
            user_id="user1",
            formula="close",
            formula_language="qlib_alpha",
            status="published",
            is_deleted=True
        )

        db_session.add(active)
        db_session.add(deleted)
        await db_session.commit()

        # ACT
        result = await repo.search_by_name(keyword="Factor")

        # ASSERT
        assert len(result) == 1
        assert result[0].factor_name == "Active Factor"

    async def test_search_by_name_pagination(self, db_session: AsyncSession):
        """Test search pagination."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        factors = [
            CustomFactor(
                factor_name=f"Test Factor {i}",
                user_id="user1",
                formula="close",
                formula_language="qlib_alpha",
                status="published",
                is_deleted=False,
                usage_count=i
            )
            for i in range(10)
        ]

        for factor in factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        page1 = await repo.search_by_name(keyword="Test", skip=0, limit=3)
        page2 = await repo.search_by_name(keyword="Test", skip=3, limit=3)

        # ASSERT
        assert len(page1) == 3
        assert len(page2) == 3


@pytest.mark.asyncio
class TestCustomFactorRepositoryGetPopularFactors:
    """Test get_popular_factors method for discovering popular factors."""

    async def test_get_popular_factors_returns_top_used(self, db_session: AsyncSession):
        """Test that popular factors are returned in order of usage."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        factors = [
            CustomFactor(
                factor_name=f"Factor_{i}",
                user_id="user1",
                formula="close",
                formula_language="qlib_alpha",
                status="published",
                is_public=True,
                is_deleted=False,
                usage_count=i * 10
            )
            for i in range(1, 6)
        ]

        for factor in factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        result = await repo.get_popular_factors(limit=3)

        # ASSERT
        assert len(result) == 3
        assert result[0].usage_count == 50
        assert result[1].usage_count == 40
        assert result[2].usage_count == 30

    async def test_get_popular_factors_only_public_published(self, db_session: AsyncSession):
        """Test that only public and published factors are included."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        public_published = CustomFactor(
            factor_name="Public Published",
            user_id="user1",
            formula="close",
            formula_language="qlib_alpha",
            status="published",
            is_public=True,
            is_deleted=False,
            usage_count=10
        )

        private_published = CustomFactor(
            factor_name="Private Published",
            user_id="user1",
            formula="close",
            formula_language="qlib_alpha",
            status="published",
            is_public=False,
            is_deleted=False,
            usage_count=20
        )

        db_session.add(public_published)
        db_session.add(private_published)
        await db_session.commit()

        # ACT
        result = await repo.get_popular_factors()

        # ASSERT
        assert len(result) == 1
        assert result[0].factor_name == "Public Published"

    async def test_get_popular_factors_requires_positive_usage(self, db_session: AsyncSession):
        """Test that factors with zero usage are excluded."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)

        used_factor = CustomFactor(
            factor_name="Used Factor",
            user_id="user1",
            formula="close",
            formula_language="qlib_alpha",
            status="published",
            is_public=True,
            is_deleted=False,
            usage_count=5
        )

        unused_factor = CustomFactor(
            factor_name="Unused Factor",
            user_id="user1",
            formula="close",
            formula_language="qlib_alpha",
            status="published",
            is_public=True,
            is_deleted=False,
            usage_count=0
        )

        db_session.add(used_factor)
        db_session.add(unused_factor)
        await db_session.commit()

        # ACT
        result = await repo.get_popular_factors()

        # ASSERT
        assert len(result) == 1
        assert result[0].factor_name == "Used Factor"


@pytest.mark.asyncio
class TestCustomFactorRepositoryGetByBaseIndicator:
    """Test get_by_base_indicator method for finding factors by base indicator."""

    async def test_get_by_base_indicator_success(self, db_session: AsyncSession):
        """Test retrieving factors by base indicator ID."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)
        base_indicator_id = "indicator_123"

        factors = [
            CustomFactor(
                factor_name=f"Factor_{i}",
                user_id="user1",
                formula="close",
                formula_language="qlib_alpha",
                status="published",
                base_indicator_id=base_indicator_id if i < 3 else "other_indicator",
                is_deleted=False
            )
            for i in range(5)
        ]

        for factor in factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        result = await repo.get_by_base_indicator(base_indicator_id)

        # ASSERT
        assert len(result) == 3
        assert all(f.base_indicator_id == base_indicator_id for f in result)

    async def test_get_by_base_indicator_excludes_deleted(self, db_session: AsyncSession):
        """Test that get_by_base_indicator excludes soft-deleted factors."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)
        base_indicator_id = "indicator_123"

        active = CustomFactor(
            factor_name="Active",
            user_id="user1",
            formula="close",
            formula_language="qlib_alpha",
            status="published",
            base_indicator_id=base_indicator_id,
            is_deleted=False
        )

        deleted = CustomFactor(
            factor_name="Deleted",
            user_id="user1",
            formula="close",
            formula_language="qlib_alpha",
            status="published",
            base_indicator_id=base_indicator_id,
            is_deleted=True
        )

        db_session.add(active)
        db_session.add(deleted)
        await db_session.commit()

        # ACT
        result = await repo.get_by_base_indicator(base_indicator_id)

        # ASSERT
        assert len(result) == 1
        assert result[0].factor_name == "Active"

    async def test_get_by_base_indicator_ordered_by_created_at(self, db_session: AsyncSession):
        """Test that results are ordered by created_at DESC."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)
        base_indicator_id = "indicator_123"

        import time
        factors = []
        for i in range(3):
            factor = CustomFactor(
                factor_name=f"Factor_{i}",
                user_id="user1",
                formula="close",
                formula_language="qlib_alpha",
                status="published",
                base_indicator_id=base_indicator_id,
                is_deleted=False
            )
            db_session.add(factor)
            await db_session.commit()
            await db_session.refresh(factor)
            factors.append(factor)
            time.sleep(0.01)

        # ACT
        result = await repo.get_by_base_indicator(base_indicator_id)

        # ASSERT
        assert len(result) == 3
        for i in range(len(result) - 1):
            assert result[i].created_at >= result[i + 1].created_at

    async def test_get_by_base_indicator_pagination(self, db_session: AsyncSession):
        """Test pagination with skip and limit."""
        # ARRANGE
        repo = CustomFactorRepository(db_session)
        base_indicator_id = "indicator_123"

        factors = [
            CustomFactor(
                factor_name=f"Factor_{i}",
                user_id="user1",
                formula="close",
                formula_language="qlib_alpha",
                status="published",
                base_indicator_id=base_indicator_id,
                is_deleted=False
            )
            for i in range(10)
        ]

        for factor in factors:
            db_session.add(factor)
        await db_session.commit()

        # ACT
        page1 = await repo.get_by_base_indicator(base_indicator_id, skip=0, limit=3)
        page2 = await repo.get_by_base_indicator(base_indicator_id, skip=3, limit=3)

        # ASSERT
        assert len(page1) == 3
        assert len(page2) == 3
