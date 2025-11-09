"""
Test TemplateService

Tests for template service business logic following TDD methodology:
- Get popular templates
- Add and update ratings
- Rating calculations
- Error handling
"""

import pytest
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.strategy.services.template_service import TemplateService
from app.database.models.strategy import StrategyTemplate, TemplateRating, StrategyCategory
from app.database.repositories.strategy_template import StrategyTemplateRepository
from app.database.repositories.template_rating import TemplateRatingRepository


@pytest.fixture
def template_service(db_session: AsyncSession):
    """Create TemplateService instance"""
    return TemplateService(db_session)


@pytest.fixture
async def sample_templates(db_session: AsyncSession):
    """Create sample templates for testing"""
    templates = [
        StrategyTemplate(
            id="template-trend-1",
            name="Double MA",
            category=StrategyCategory.TREND_FOLLOWING,
            description="Double Moving Average Strategy",
            logic_flow={"nodes": [], "edges": []},
            parameters={},
            is_system_template=True,
            usage_count=100,
            rating_average=4.5,
            rating_count=10,
        ),
        StrategyTemplate(
            id="template-trend-2",
            name="MACD Strategy",
            category=StrategyCategory.TREND_FOLLOWING,
            description="MACD-based strategy",
            logic_flow={"nodes": [], "edges": []},
            parameters={},
            is_system_template=True,
            usage_count=80,
            rating_average=4.2,
            rating_count=5,
        ),
        StrategyTemplate(
            id="template-osc-1",
            name="RSI Strategy",
            category=StrategyCategory.OSCILLATION,
            description="RSI-based oscillation strategy",
            logic_flow={"nodes": [], "edges": []},
            parameters={},
            is_system_template=True,
            usage_count=60,
            rating_average=3.8,
            rating_count=8,
        ),
        StrategyTemplate(
            id="template-multi-1",
            name="Multi-Factor Strategy",
            category=StrategyCategory.MULTI_FACTOR,
            description="Multi-factor investing strategy",
            logic_flow={"nodes": [], "edges": []},
            parameters={},
            is_system_template=True,
            usage_count=40,
            rating_average=4.0,
            rating_count=3,
        ),
        StrategyTemplate(
            id="template-osc-2",
            name="KDJ Strategy",
            category=StrategyCategory.OSCILLATION,
            description="KDJ oscillation strategy",
            logic_flow={"nodes": [], "edges": []},
            parameters={},
            is_system_template=True,
            usage_count=20,
            rating_average=3.5,
            rating_count=2,
        ),
    ]

    for template in templates:
        db_session.add(template)
    await db_session.commit()

    return templates


class TestGetPopularTemplates:
    """Test get_popular_templates method"""

    async def test_get_popular_all_categories(
        self, template_service: TemplateService, sample_templates
    ):
        """Should return top N templates sorted by usage_count"""
        # Act
        result = await template_service.get_popular_templates(limit=3)

        # Assert
        assert len(result) == 3
        assert result[0].id == "template-trend-1"  # usage_count=100
        assert result[1].id == "template-trend-2"  # usage_count=80
        assert result[2].id == "template-osc-1"    # usage_count=60

    async def test_get_popular_specific_category(
        self, template_service: TemplateService, sample_templates
    ):
        """Should return popular templates filtered by category"""
        # Act
        result = await template_service.get_popular_templates(
            limit=5,
            category=StrategyCategory.TREND_FOLLOWING
        )

        # Assert
        assert len(result) == 2
        assert all(t.category == StrategyCategory.TREND_FOLLOWING for t in result)
        assert result[0].id == "template-trend-1"
        assert result[1].id == "template-trend-2"

    async def test_get_popular_with_limit(
        self, template_service: TemplateService, sample_templates
    ):
        """Should respect limit parameter"""
        # Act
        result = await template_service.get_popular_templates(limit=2)

        # Assert
        assert len(result) == 2

    async def test_get_popular_empty_result(
        self, template_service: TemplateService, db_session: AsyncSession
    ):
        """Should return empty list when no templates exist"""
        # Act
        result = await template_service.get_popular_templates(limit=5)

        # Assert
        assert len(result) == 0

    async def test_get_popular_default_limit(
        self, template_service: TemplateService, sample_templates
    ):
        """Should use default limit of 5"""
        # Act
        result = await template_service.get_popular_templates()

        # Assert
        assert len(result) == 5


class TestAddRating:
    """Test add_rating method"""

    async def test_add_new_rating(
        self, template_service: TemplateService, sample_templates, db_session: AsyncSession
    ):
        """Should create new rating and update template stats"""
        # Arrange
        template_id = "template-trend-1"
        user_id = "user-1"

        # Act
        rating = await template_service.add_rating(
            template_id=template_id,
            user_id=user_id,
            rating=5,
            comment="Excellent strategy!"
        )

        # Assert
        assert rating is not None
        assert rating.template_id == template_id
        assert rating.user_id == user_id
        assert rating.rating == 5
        assert rating.comment == "Excellent strategy!"

        # Verify template stats updated
        await db_session.refresh(sample_templates[0])
        template = sample_templates[0]

        # Only one rating in database now (the new one we added)
        assert template.rating_count == 1
        assert template.rating_average == 5.0

    async def test_update_existing_rating(
        self, template_service: TemplateService, sample_templates, db_session: AsyncSession
    ):
        """Should update existing rating and recalculate stats"""
        # Arrange
        template_id = "template-trend-1"
        user_id = "user-1"

        # Add initial rating
        await template_service.add_rating(template_id, user_id, rating=3)

        # Act - Update rating
        rating = await template_service.add_rating(
            template_id=template_id,
            user_id=user_id,
            rating=5,
            comment="Changed my mind, it's great!"
        )

        # Assert
        assert rating.rating == 5
        assert rating.comment == "Changed my mind, it's great!"

        # Verify only one rating exists for this user
        repo = TemplateRatingRepository(db_session)
        user_rating = await repo.get_user_rating(template_id, user_id)
        assert user_rating is not None
        assert user_rating.rating == 5

    async def test_rating_average_calculation(
        self, template_service: TemplateService, sample_templates, db_session: AsyncSession
    ):
        """Should correctly calculate rating average"""
        # Arrange
        template_id = "template-multi-1"

        # Act - Add multiple ratings
        await template_service.add_rating(template_id, "user-1", rating=5)
        await template_service.add_rating(template_id, "user-2", rating=4)
        await template_service.add_rating(template_id, "user-3", rating=3)

        # Assert
        await db_session.refresh(sample_templates[3])
        template = sample_templates[3]

        # Three new ratings: (5 + 4 + 3) / 3 = 12 / 3 = 4.0
        assert template.rating_count == 3
        assert abs(float(template.rating_average) - 4.0) < 0.01

    async def test_rating_count_increment(
        self, template_service: TemplateService, sample_templates, db_session: AsyncSession
    ):
        """Should increment rating count correctly"""
        # Arrange
        template_id = "template-osc-2"

        # Act
        await template_service.add_rating(template_id, "user-1", rating=4)
        await template_service.add_rating(template_id, "user-2", rating=5)

        # Assert
        await db_session.refresh(sample_templates[4])
        template = sample_templates[4]
        assert template.rating_count == 2  # Two new ratings

    async def test_invalid_template_id(
        self, template_service: TemplateService
    ):
        """Should raise error for non-existent template"""
        # Act & Assert
        with pytest.raises(ValueError, match="Template not found"):
            await template_service.add_rating(
                template_id="non-existent",
                user_id="user-1",
                rating=5
            )

    async def test_rating_validation_too_low(
        self, template_service: TemplateService, sample_templates
    ):
        """Should reject rating below 1"""
        # Act & Assert
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            await template_service.add_rating(
                template_id="template-trend-1",
                user_id="user-1",
                rating=0
            )

    async def test_rating_validation_too_high(
        self, template_service: TemplateService, sample_templates
    ):
        """Should reject rating above 5"""
        # Act & Assert
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            await template_service.add_rating(
                template_id="template-trend-1",
                user_id="user-1",
                rating=6
            )

    async def test_rating_with_none_comment(
        self, template_service: TemplateService, sample_templates
    ):
        """Should accept None comment"""
        # Act
        rating = await template_service.add_rating(
            template_id="template-trend-1",
            user_id="user-1",
            rating=4,
            comment=None
        )

        # Assert
        assert rating.comment is None

    async def test_multiple_users_rating_same_template(
        self, template_service: TemplateService, sample_templates, db_session: AsyncSession
    ):
        """Should handle multiple users rating the same template"""
        # Arrange
        template_id = "template-osc-1"

        # Act
        await template_service.add_rating(template_id, "user-1", rating=5)
        await template_service.add_rating(template_id, "user-2", rating=4)
        await template_service.add_rating(template_id, "user-3", rating=5)

        # Assert
        await db_session.refresh(sample_templates[2])
        template = sample_templates[2]

        # Three new ratings: (5 + 4 + 5) / 3 = 14 / 3 = 4.666...
        assert template.rating_count == 3
        assert abs(float(template.rating_average) - 4.666) < 0.01


class TestRatingStatisticsEdgeCases:
    """Test edge cases in rating statistics calculations"""

    async def test_first_rating_for_template(
        self, template_service: TemplateService, db_session: AsyncSession
    ):
        """Should correctly set first rating"""
        # Arrange - Create template with no ratings
        template = StrategyTemplate(
            id="new-template",
            name="New Template",
            category=StrategyCategory.TREND_FOLLOWING,
            description="New template",
            logic_flow={"nodes": [], "edges": []},
            parameters={},
            is_system_template=True,
            usage_count=0,
            rating_average=0.0,
            rating_count=0,
        )
        db_session.add(template)
        await db_session.commit()

        # Act
        await template_service.add_rating("new-template", "user-1", rating=4)

        # Assert
        await db_session.refresh(template)
        assert template.rating_count == 1
        assert template.rating_average == 4.0

    async def test_rating_average_precision(
        self, template_service: TemplateService, db_session: AsyncSession
    ):
        """Should maintain precision in rating calculations"""
        # Arrange
        template = StrategyTemplate(
            id="precision-template",
            name="Precision Template",
            category=StrategyCategory.TREND_FOLLOWING,
            description="Test precision",
            logic_flow={"nodes": [], "edges": []},
            parameters={},
            is_system_template=True,
            usage_count=0,
            rating_average=0.0,
            rating_count=0,
        )
        db_session.add(template)
        await db_session.commit()

        # Act - Add ratings that should produce non-integer average
        await template_service.add_rating("precision-template", "user-1", rating=3)
        await template_service.add_rating("precision-template", "user-2", rating=4)
        await template_service.add_rating("precision-template", "user-3", rating=5)

        # Assert
        await db_session.refresh(template)
        assert template.rating_count == 3
        assert float(template.rating_average) == 4.0


class TestToggleFavorite:
    """Test toggle_favorite method"""

    async def test_toggle_favorite_not_implemented(
        self, template_service: TemplateService, sample_templates
    ):
        """Should raise NotImplementedError"""
        # Act & Assert
        with pytest.raises(NotImplementedError, match="Favorite functionality"):
            await template_service.toggle_favorite(
                template_id="template-trend-1",
                user_id="user-1"
            )


class TestTemplateServiceIntegration:
    """Integration tests for TemplateService"""

    async def test_get_popular_all_categories_sorted_by_usage(
        self, template_service: TemplateService, sample_templates, db_session: AsyncSession
    ):
        """Should return templates sorted by usage_count descending"""
        # Act
        result = await template_service.get_popular_templates(limit=5)

        # Assert
        assert len(result) == 5
        usage_counts = [t.usage_count for t in result]
        assert usage_counts == sorted(usage_counts, reverse=True)

    async def test_add_rating_with_empty_comment(
        self, template_service: TemplateService, sample_templates
    ):
        """Should accept empty string comment"""
        # Act
        rating = await template_service.add_rating(
            template_id="template-trend-1",
            user_id="user-1",
            rating=4,
            comment=""
        )

        # Assert
        assert rating.comment == ""

    async def test_rating_boundary_values(
        self, template_service: TemplateService, sample_templates, db_session: AsyncSession
    ):
        """Should accept all valid rating values (1-5)"""
        # Arrange
        template_id = "template-multi-1"

        # Act - Add ratings for all boundary values
        for rating_value in [1, 2, 3, 4, 5]:
            user_id = f"user-boundary-{rating_value}"
            rating = await template_service.add_rating(
                template_id=template_id,
                user_id=user_id,
                rating=rating_value
            )

            # Assert
            assert rating.rating == rating_value

        # Verify average calculation
        await db_session.refresh(sample_templates[3])
        template = sample_templates[3]
        expected_average = (1 + 2 + 3 + 4 + 5) / 5
        assert abs(float(template.rating_average) - expected_average) < 0.01

    async def test_rating_just_below_boundary(
        self, template_service: TemplateService, sample_templates
    ):
        """Should reject rating < 1"""
        # Act & Assert
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            await template_service.add_rating(
                template_id="template-trend-1",
                user_id="user-1",
                rating=0.99
            )

    async def test_rating_just_above_boundary(
        self, template_service: TemplateService, sample_templates
    ):
        """Should reject rating > 5"""
        # Act & Assert
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            await template_service.add_rating(
                template_id="template-trend-1",
                user_id="user-1",
                rating=5.01
            )

    async def test_add_rating_to_non_existent_template(
        self, template_service: TemplateService
    ):
        """Should raise ValueError for non-existent template"""
        # Act & Assert
        with pytest.raises(ValueError, match="Template not found"):
            await template_service.add_rating(
                template_id="completely-invalid-id-xyz",
                user_id="user-1",
                rating=3
            )

    async def test_get_popular_with_zero_limit(
        self, template_service: TemplateService, sample_templates
    ):
        """Should handle zero limit gracefully"""
        # Act
        result = await template_service.get_popular_templates(limit=0)

        # Assert
        assert len(result) == 0

    async def test_get_popular_with_high_limit(
        self, template_service: TemplateService, sample_templates
    ):
        """Should return all templates when limit exceeds total"""
        # Act
        result = await template_service.get_popular_templates(limit=1000)

        # Assert
        assert len(result) == 5  # Only 5 templates available
