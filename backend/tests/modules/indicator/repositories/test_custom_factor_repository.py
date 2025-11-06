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
