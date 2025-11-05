"""
TDD Tests for TemplateRatingRepository

Following strict TDD methodology:
1. Write failing tests first
2. Implement minimal code to pass
3. Refactor

Test Coverage:
- CRUD operations
- Get ratings by template
- Get user's specific rating
- Upsert (insert or update) rating
- Rating constraints (1-5 range)
- Unique user-template rating
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.database.models.strategy import (
    TemplateRating,
    StrategyTemplate,
    StrategyCategory
)
from app.database.repositories.template_rating import TemplateRatingRepository
from app.database.repositories.strategy_template import StrategyTemplateRepository


@pytest.mark.asyncio
class TestTemplateRatingRepositoryCreate:
    """Test TemplateRating creation"""

    async def test_create_rating(self, db_session: AsyncSession):
        """Test creating a template rating"""
        template_repo = StrategyTemplateRepository(db_session)
        rating_repo = TemplateRatingRepository(db_session)

        # Create template
        template = await template_repo.create({
            "name": "Test Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
            "is_system_template": True
        })

        # Create rating
        rating_data = {
            "template_id": template.id,
            "user_id": "user_123",
            "rating": 5,
            "comment": "Excellent strategy!"
        }

        rating = await rating_repo.create(rating_data, user_id="user_123")

        assert rating.id is not None
        assert rating.template_id == template.id
        assert rating.user_id == "user_123"
        assert rating.rating == 5
        assert rating.comment == "Excellent strategy!"

    async def test_create_rating_without_comment(self, db_session: AsyncSession):
        """Test creating rating without optional comment"""
        template_repo = StrategyTemplateRepository(db_session)
        rating_repo = TemplateRatingRepository(db_session)

        template = await template_repo.create({
            "name": "Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []}
        })

        rating_data = {
            "template_id": template.id,
            "user_id": "user_123",
            "rating": 4
        }

        rating = await rating_repo.create(rating_data, user_id="user_123")

        assert rating.comment is None

    async def test_create_rating_validates_range(self, db_session: AsyncSession):
        """Test rating value must be between 1-5"""
        template_repo = StrategyTemplateRepository(db_session)
        rating_repo = TemplateRatingRepository(db_session)

        template = await template_repo.create({
            "name": "Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []}
        })

        # Test invalid rating (0)
        with pytest.raises(IntegrityError):
            await rating_repo.create({
                "template_id": template.id,
                "user_id": "user_123",
                "rating": 0
            }, user_id="user_123")
            await db_session.commit()

    async def test_create_duplicate_rating_fails(self, db_session: AsyncSession):
        """Test user cannot create multiple ratings for same template"""
        template_repo = StrategyTemplateRepository(db_session)
        rating_repo = TemplateRatingRepository(db_session)

        template = await template_repo.create({
            "name": "Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []}
        })

        # Create first rating
        await rating_repo.create({
            "template_id": template.id,
            "user_id": "user_123",
            "rating": 5
        }, user_id="user_123")

        # Try to create duplicate - should fail
        with pytest.raises(IntegrityError):
            await rating_repo.create({
                "template_id": template.id,
                "user_id": "user_123",
                "rating": 3
            }, user_id="user_123")
            await db_session.commit()


@pytest.mark.asyncio
class TestTemplateRatingRepositoryRead:
    """Test TemplateRating read operations"""

    async def test_get_by_id(self, db_session: AsyncSession):
        """Test retrieving rating by ID"""
        template_repo = StrategyTemplateRepository(db_session)
        rating_repo = TemplateRatingRepository(db_session)

        template = await template_repo.create({
            "name": "Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []}
        })

        created = await rating_repo.create({
            "template_id": template.id,
            "user_id": "user_123",
            "rating": 4
        }, user_id="user_123")

        retrieved = await rating_repo.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.rating == 4

    async def test_get_by_template(self, db_session: AsyncSession):
        """Test getting all ratings for a template"""
        template_repo = StrategyTemplateRepository(db_session)
        rating_repo = TemplateRatingRepository(db_session)

        # Create template
        template = await template_repo.create({
            "name": "Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []}
        })

        # Create ratings from different users
        await rating_repo.create({
            "template_id": template.id,
            "user_id": "user_1",
            "rating": 5
        }, user_id="user_1")
        await rating_repo.create({
            "template_id": template.id,
            "user_id": "user_2",
            "rating": 4
        }, user_id="user_2")
        await rating_repo.create({
            "template_id": template.id,
            "user_id": "user_3",
            "rating": 3
        }, user_id="user_3")

        ratings = await rating_repo.get_by_template(template.id)

        assert len(ratings) == 3
        assert all(r.template_id == template.id for r in ratings)

    async def test_get_user_rating(self, db_session: AsyncSession):
        """Test getting specific user's rating for a template"""
        template_repo = StrategyTemplateRepository(db_session)
        rating_repo = TemplateRatingRepository(db_session)

        template = await template_repo.create({
            "name": "Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []}
        })

        # Create ratings from different users
        await rating_repo.create({
            "template_id": template.id,
            "user_id": "user_1",
            "rating": 5
        }, user_id="user_1")
        await rating_repo.create({
            "template_id": template.id,
            "user_id": "user_2",
            "rating": 3
        }, user_id="user_2")

        # Get specific user's rating
        user_1_rating = await rating_repo.get_user_rating(template.id, "user_1")

        assert user_1_rating is not None
        assert user_1_rating.user_id == "user_1"
        assert user_1_rating.rating == 5

    async def test_get_user_rating_nonexistent(self, db_session: AsyncSession):
        """Test getting non-existent user rating returns None"""
        template_repo = StrategyTemplateRepository(db_session)
        rating_repo = TemplateRatingRepository(db_session)

        template = await template_repo.create({
            "name": "Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []}
        })

        rating = await rating_repo.get_user_rating(template.id, "nonexistent_user")

        assert rating is None


@pytest.mark.asyncio
class TestTemplateRatingRepositoryUpdate:
    """Test TemplateRating update operations"""

    async def test_update_rating(self, db_session: AsyncSession):
        """Test updating an existing rating"""
        template_repo = StrategyTemplateRepository(db_session)
        rating_repo = TemplateRatingRepository(db_session)

        template = await template_repo.create({
            "name": "Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []}
        })

        rating = await rating_repo.create({
            "template_id": template.id,
            "user_id": "user_123",
            "rating": 3,
            "comment": "Original comment"
        }, user_id="user_123")

        # Update rating
        updated = await rating_repo.update(
            rating.id,
            {"rating": 5, "comment": "Updated comment"},
            user_id="user_123"
        )

        assert updated is not None
        assert updated.rating == 5
        assert updated.comment == "Updated comment"


@pytest.mark.asyncio
class TestTemplateRatingRepositoryDelete:
    """Test TemplateRating delete operations"""

    async def test_delete_rating(self, db_session: AsyncSession):
        """Test deleting a rating"""
        template_repo = StrategyTemplateRepository(db_session)
        rating_repo = TemplateRatingRepository(db_session)

        template = await template_repo.create({
            "name": "Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []}
        })

        rating = await rating_repo.create({
            "template_id": template.id,
            "user_id": "user_123",
            "rating": 4
        }, user_id="user_123")

        # Delete rating
        success = await rating_repo.delete(rating.id, soft=False)

        assert success is True

        # Should not be found
        deleted = await rating_repo.get(rating.id)
        assert deleted is None


@pytest.mark.asyncio
class TestTemplateRatingRepositoryUpsert:
    """Test upsert (insert or update) functionality"""

    async def test_upsert_creates_new_rating(self, db_session: AsyncSession):
        """Test upsert creates new rating when none exists"""
        template_repo = StrategyTemplateRepository(db_session)
        rating_repo = TemplateRatingRepository(db_session)

        template = await template_repo.create({
            "name": "Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []}
        })

        # Upsert new rating
        rating = await rating_repo.upsert_rating(
            template_id=template.id,
            user_id="user_123",
            rating=5,
            comment="Great template!"
        )

        assert rating.id is not None
        assert rating.rating == 5
        assert rating.comment == "Great template!"

    async def test_upsert_updates_existing_rating(self, db_session: AsyncSession):
        """Test upsert updates existing rating"""
        template_repo = StrategyTemplateRepository(db_session)
        rating_repo = TemplateRatingRepository(db_session)

        template = await template_repo.create({
            "name": "Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []}
        })

        # Create initial rating
        initial = await rating_repo.create({
            "template_id": template.id,
            "user_id": "user_123",
            "rating": 3,
            "comment": "Original"
        }, user_id="user_123")

        # Upsert (should update)
        updated = await rating_repo.upsert_rating(
            template_id=template.id,
            user_id="user_123",
            rating=5,
            comment="Updated"
        )

        assert updated.id == initial.id  # Same rating object
        assert updated.rating == 5
        assert updated.comment == "Updated"

        # Verify only one rating exists
        all_ratings = await rating_repo.get_by_template(template.id)
        assert len(all_ratings) == 1

    async def test_upsert_without_comment(self, db_session: AsyncSession):
        """Test upsert works without optional comment"""
        template_repo = StrategyTemplateRepository(db_session)
        rating_repo = TemplateRatingRepository(db_session)

        template = await template_repo.create({
            "name": "Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []}
        })

        rating = await rating_repo.upsert_rating(
            template_id=template.id,
            user_id="user_123",
            rating=4
        )

        assert rating.comment is None


@pytest.mark.asyncio
class TestTemplateRatingRepositoryPagination:
    """Test pagination and sorting"""

    async def test_get_by_template_with_pagination(self, db_session: AsyncSession):
        """Test getting template ratings with pagination"""
        template_repo = StrategyTemplateRepository(db_session)
        rating_repo = TemplateRatingRepository(db_session)

        template = await template_repo.create({
            "name": "Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []}
        })

        # Create 5 ratings
        for i in range(5):
            await rating_repo.create({
                "template_id": template.id,
                "user_id": f"user_{i}",
                "rating": 5
            }, user_id=f"user_{i}")

        # Get first page
        page1 = await rating_repo.get_by_template(template.id, skip=0, limit=2)
        assert len(page1) == 2

        # Get second page
        page2 = await rating_repo.get_by_template(template.id, skip=2, limit=2)
        assert len(page2) == 2

    async def test_get_by_template_sorted_by_created_at(self, db_session: AsyncSession):
        """Test ratings are sorted by creation date descending"""
        template_repo = StrategyTemplateRepository(db_session)
        rating_repo = TemplateRatingRepository(db_session)

        template = await template_repo.create({
            "name": "Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []}
        })

        # Create ratings
        rating1 = await rating_repo.create({
            "template_id": template.id,
            "user_id": "user_1",
            "rating": 3
        }, user_id="user_1")

        rating2 = await rating_repo.create({
            "template_id": template.id,
            "user_id": "user_2",
            "rating": 5
        }, user_id="user_2")

        ratings = await rating_repo.get_by_template(template.id)

        # Most recent first
        assert ratings[0].id == rating2.id
        assert ratings[1].id == rating1.id
