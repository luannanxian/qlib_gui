"""
TDD Tests for StrategyTemplateRepository

Following strict TDD methodology:
1. Write failing tests first
2. Implement minimal code to pass
3. Refactor

Test Coverage:
- CRUD operations
- Favorite toggling (per user)
- Rating calculations
- Popular templates query
- Search and filtering
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy import StrategyTemplate, StrategyCategory
from app.database.repositories.strategy_template import StrategyTemplateRepository


@pytest.mark.asyncio
class TestStrategyTemplateRepositoryCreate:
    """Test StrategyTemplate creation"""

    async def test_create_system_template(self, db_session: AsyncSession):
        """Test creating a built-in system template"""
        repo = StrategyTemplateRepository(db_session)

        template_data = {
            "name": "Double MA Crossover",
            "description": "Classic double moving average crossover strategy",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {
                "nodes": [
                    {"id": "node_1", "type": "INDICATOR", "indicator": "MA", "parameters": {"period": 20}}
                ],
                "edges": []
            },
            "parameters": {
                "short_period": {"default": 10, "min": 5, "max": 50},
                "long_period": {"default": 20, "min": 10, "max": 200}
            },
            "is_system_template": True,
            "backtest_example": {
                "return": 0.15,
                "sharpe": 1.5
            }
        }

        template = await repo.create(template_data)

        assert template.id is not None
        assert template.name == "Double MA Crossover"
        assert template.category == StrategyCategory.TREND_FOLLOWING.value
        assert template.is_system_template is True
        assert template.user_id is None
        assert template.usage_count == 0
        assert template.rating_average == 0.0
        assert template.rating_count == 0

    async def test_create_custom_user_template(self, db_session: AsyncSession):
        """Test creating a custom user template"""
        repo = StrategyTemplateRepository(db_session)

        template_data = {
            "name": "My Custom Strategy",
            "description": "Custom strategy for testing",
            "category": StrategyCategory.MULTI_FACTOR.value,
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {},
            "is_system_template": False,
            "user_id": "user_123"
        }

        template = await repo.create(template_data, user_id="user_123")

        assert template.id is not None
        assert template.name == "My Custom Strategy"
        assert template.is_system_template is False
        assert template.user_id == "user_123"
        assert template.created_by == "user_123"

    async def test_create_template_with_default_values(self, db_session: AsyncSession):
        """Test template creation with default values"""
        repo = StrategyTemplateRepository(db_session)

        template_data = {
            "name": "Minimal Template",
            "category": StrategyCategory.OSCILLATION.value,
            "logic_flow": {"nodes": [], "edges": []},
        }

        template = await repo.create(template_data)

        assert template.description is None
        assert template.parameters == {}
        assert template.usage_count == 0
        assert template.rating_average == 0.0
        assert template.rating_count == 0
        assert template.is_system_template is False


@pytest.mark.asyncio
class TestStrategyTemplateRepositoryRead:
    """Test StrategyTemplate read operations"""

    async def test_get_by_id(self, db_session: AsyncSession):
        """Test retrieving template by ID"""
        repo = StrategyTemplateRepository(db_session)

        # Create a template
        template_data = {
            "name": "Test Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
        }
        created = await repo.create(template_data)

        # Retrieve it
        retrieved = await repo.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Test Template"

    async def test_get_nonexistent_template(self, db_session: AsyncSession):
        """Test retrieving non-existent template returns None"""
        repo = StrategyTemplateRepository(db_session)

        result = await repo.get("nonexistent-id")

        assert result is None

    async def test_get_multi_with_pagination(self, db_session: AsyncSession):
        """Test getting multiple templates with pagination"""
        repo = StrategyTemplateRepository(db_session)

        # Create 5 templates
        for i in range(5):
            await repo.create({
                "name": f"Template {i}",
                "category": StrategyCategory.TREND_FOLLOWING.value,
                "logic_flow": {"nodes": [], "edges": []},
            })

        # Get first page (2 items)
        page1 = await repo.get_multi(skip=0, limit=2)
        assert len(page1) == 2

        # Get second page
        page2 = await repo.get_multi(skip=2, limit=2)
        assert len(page2) == 2

        # Ensure different templates
        assert page1[0].id != page2[0].id

    async def test_get_multi_with_category_filter(self, db_session: AsyncSession):
        """Test filtering templates by category"""
        repo = StrategyTemplateRepository(db_session)

        # Create templates with different categories
        await repo.create({
            "name": "Trend Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
        })
        await repo.create({
            "name": "Oscillation Template",
            "category": StrategyCategory.OSCILLATION.value,
            "logic_flow": {"nodes": [], "edges": []},
        })

        # Filter by category
        trend_templates = await repo.get_multi(category=StrategyCategory.TREND_FOLLOWING.value)

        assert len(trend_templates) == 1
        assert trend_templates[0].name == "Trend Template"

    async def test_get_system_templates_only(self, db_session: AsyncSession):
        """Test retrieving only system templates"""
        repo = StrategyTemplateRepository(db_session)

        # Create system and user templates
        await repo.create({
            "name": "System Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
            "is_system_template": True
        })
        await repo.create({
            "name": "User Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
            "is_system_template": False,
            "user_id": "user_123"
        })

        # Get only system templates
        system_templates = await repo.get_multi(is_system_template=True)

        assert len(system_templates) == 1
        assert system_templates[0].name == "System Template"

    async def test_count_templates(self, db_session: AsyncSession):
        """Test counting templates"""
        repo = StrategyTemplateRepository(db_session)

        # Create templates
        for i in range(3):
            await repo.create({
                "name": f"Template {i}",
                "category": StrategyCategory.TREND_FOLLOWING.value,
                "logic_flow": {"nodes": [], "edges": []},
            })

        total = await repo.count()

        assert total == 3

    async def test_count_with_filter(self, db_session: AsyncSession):
        """Test counting with category filter"""
        repo = StrategyTemplateRepository(db_session)

        await repo.create({
            "name": "Trend 1",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
        })
        await repo.create({
            "name": "Trend 2",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
        })
        await repo.create({
            "name": "Osc 1",
            "category": StrategyCategory.OSCILLATION.value,
            "logic_flow": {"nodes": [], "edges": []},
        })

        trend_count = await repo.count(category=StrategyCategory.TREND_FOLLOWING.value)

        assert trend_count == 2


@pytest.mark.asyncio
class TestStrategyTemplateRepositoryUpdate:
    """Test StrategyTemplate update operations"""

    async def test_update_template_basic(self, db_session: AsyncSession):
        """Test updating template basic fields"""
        repo = StrategyTemplateRepository(db_session)

        # Create template
        template = await repo.create({
            "name": "Original Name",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
        })

        # Update it
        updated = await repo.update(
            template.id,
            {"name": "Updated Name", "description": "New description"},
            user_id="admin_user"
        )

        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.description == "New description"
        assert updated.updated_by == "admin_user"

    async def test_update_logic_flow(self, db_session: AsyncSession):
        """Test updating template logic flow"""
        repo = StrategyTemplateRepository(db_session)

        template = await repo.create({
            "name": "Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
        })

        new_logic_flow = {
            "nodes": [
                {"id": "node_1", "type": "INDICATOR", "indicator": "RSI"}
            ],
            "edges": []
        }

        updated = await repo.update(template.id, {"logic_flow": new_logic_flow})

        assert updated.logic_flow == new_logic_flow

    async def test_update_nonexistent_template(self, db_session: AsyncSession):
        """Test updating non-existent template returns None"""
        repo = StrategyTemplateRepository(db_session)

        result = await repo.update("nonexistent-id", {"name": "New Name"})

        assert result is None

    async def test_increment_usage_count(self, db_session: AsyncSession):
        """Test incrementing template usage count"""
        repo = StrategyTemplateRepository(db_session)

        template = await repo.create({
            "name": "Popular Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
        })

        # Increment usage
        await repo.increment_usage_count(template.id)

        updated = await repo.get(template.id)
        assert updated.usage_count == 1

        # Increment again
        await repo.increment_usage_count(template.id)

        updated = await repo.get(template.id)
        assert updated.usage_count == 2


@pytest.mark.asyncio
class TestStrategyTemplateRepositoryDelete:
    """Test StrategyTemplate delete operations"""

    async def test_soft_delete_template(self, db_session: AsyncSession):
        """Test soft deleting a template"""
        repo = StrategyTemplateRepository(db_session)

        template = await repo.create({
            "name": "To Delete",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
        })

        # Soft delete
        success = await repo.delete(template.id, soft=True)

        assert success is True

        # Should not be found by default
        retrieved = await repo.get(template.id)
        assert retrieved is None

        # Should be found when including deleted
        deleted = await repo.get(template.id, include_deleted=True)
        assert deleted is not None
        assert deleted.is_deleted is True

    async def test_hard_delete_template(self, db_session: AsyncSession):
        """Test hard deleting a template"""
        repo = StrategyTemplateRepository(db_session)

        template = await repo.create({
            "name": "To Delete",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
        })

        # Hard delete
        success = await repo.delete(template.id, soft=False)

        assert success is True

        # Should not be found even when including deleted
        retrieved = await repo.get(template.id, include_deleted=True)
        assert retrieved is None

    async def test_delete_nonexistent_template(self, db_session: AsyncSession):
        """Test deleting non-existent template returns False"""
        repo = StrategyTemplateRepository(db_session)

        success = await repo.delete("nonexistent-id")

        assert success is False


@pytest.mark.asyncio
class TestStrategyTemplateRepositoryPopular:
    """Test popular templates functionality"""

    async def test_get_popular_templates(self, db_session: AsyncSession):
        """Test getting popular templates sorted by usage_count"""
        repo = StrategyTemplateRepository(db_session)

        # Create templates with different usage counts
        t1 = await repo.create({
            "name": "Template 1",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
        })
        t2 = await repo.create({
            "name": "Template 2",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
        })
        t3 = await repo.create({
            "name": "Template 3",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
        })

        # Set different usage counts
        await repo.update(t1.id, {"usage_count": 5})
        await repo.update(t2.id, {"usage_count": 10})
        await repo.update(t3.id, {"usage_count": 3})

        # Get top 2 popular
        popular = await repo.get_popular(limit=2)

        assert len(popular) == 2
        assert popular[0].name == "Template 2"  # usage_count = 10
        assert popular[1].name == "Template 1"  # usage_count = 5

    async def test_get_popular_with_category_filter(self, db_session: AsyncSession):
        """Test getting popular templates filtered by category"""
        repo = StrategyTemplateRepository(db_session)

        # Create templates in different categories
        trend = await repo.create({
            "name": "Trend Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
            "usage_count": 10
        })
        osc = await repo.create({
            "name": "Osc Template",
            "category": StrategyCategory.OSCILLATION.value,
            "logic_flow": {"nodes": [], "edges": []},
            "usage_count": 20
        })

        # Get popular trend templates
        popular_trend = await repo.get_popular(
            category=StrategyCategory.TREND_FOLLOWING.value,
            limit=5
        )

        assert len(popular_trend) == 1
        assert popular_trend[0].name == "Trend Template"


@pytest.mark.asyncio
class TestStrategyTemplateRepositoryRatings:
    """Test template rating-related operations"""

    async def test_update_rating_stats(self, db_session: AsyncSession):
        """Test updating template rating statistics"""
        repo = StrategyTemplateRepository(db_session)

        template = await repo.create({
            "name": "Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
        })

        # Update rating stats
        await repo.update_rating_stats(
            template.id,
            rating_average=4.5,
            rating_count=10
        )

        updated = await repo.get(template.id)
        assert float(updated.rating_average) == 4.5
        assert updated.rating_count == 10

    async def test_update_rating_stats_nonexistent_template(self, db_session: AsyncSession):
        """Test updating rating stats for non-existent template returns None"""
        repo = StrategyTemplateRepository(db_session)

        result = await repo.update_rating_stats(
            "nonexistent-id",
            rating_average=4.0,
            rating_count=5
        )

        assert result is None


@pytest.mark.asyncio
class TestStrategyTemplateRepositorySearch:
    """Test template search functionality"""

    async def test_search_by_name(self, db_session: AsyncSession):
        """Test searching templates by name"""
        repo = StrategyTemplateRepository(db_session)

        await repo.create({
            "name": "Double MA Crossover",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
        })
        await repo.create({
            "name": "MACD Strategy",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
        })

        # Search for "MA"
        results = await repo.search(query="MA")

        assert len(results) == 2  # Both contain "MA"

    async def test_search_case_insensitive(self, db_session: AsyncSession):
        """Test search is case-insensitive"""
        repo = StrategyTemplateRepository(db_session)

        await repo.create({
            "name": "RSI Strategy",
            "category": StrategyCategory.OSCILLATION.value,
            "logic_flow": {"nodes": [], "edges": []},
        })

        # Search with different case
        results = await repo.search(query="rsi")

        assert len(results) == 1
        assert results[0].name == "RSI Strategy"

    async def test_search_with_category_filter(self, db_session: AsyncSession):
        """Test searching with category filter"""
        repo = StrategyTemplateRepository(db_session)

        await repo.create({
            "name": "Strategy A",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
        })
        await repo.create({
            "name": "Strategy B",
            "category": StrategyCategory.OSCILLATION.value,
            "logic_flow": {"nodes": [], "edges": []},
        })

        # Search in specific category
        results = await repo.search(
            query="Strategy",
            category=StrategyCategory.TREND_FOLLOWING.value
        )

        assert len(results) == 1
        assert results[0].name == "Strategy A"
