"""
TDD Tests for NodeTemplateRepository

Following strict TDD methodology (Red-Green-Refactor):
1. RED: Write failing tests first
2. GREEN: Implement minimal code to pass
3. REFACTOR: Optimize code

Test Coverage:
- Create system and custom node templates
- Find by node type
- Find by user and type
- Increment usage count (atomic operation)
- Search templates with complex filters
- CRUD operations
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy_builder import NodeTemplate, NodeTypeCategory
from app.database.repositories.node_template_repository import NodeTemplateRepository


@pytest.mark.asyncio
class TestNodeTemplateRepositoryCreate:
    """Test NodeTemplate creation operations"""

    async def test_create_system_node_template(self, db_session: AsyncSession):
        """Test creating a system (built-in) node template"""
        # Arrange
        repo = NodeTemplateRepository(db_session)
        template_data = {
            "name": "ma_indicator",
            "display_name": "Moving Average",
            "description": "Calculate moving average of price",
            "node_type": NodeTypeCategory.INDICATOR.value,
            "category": "TREND",
            "parameter_schema": {
                "period": {"type": "integer", "min": 1, "max": 200, "default": 20}
            },
            "default_parameters": {"period": 20},
            "input_ports": [{"name": "price", "type": "series", "required": True}],
            "output_ports": [{"name": "ma_value", "type": "series"}],
            "is_system_template": True,
            "icon": "chart-line",
            "color": "#3b82f6"
        }

        # Act
        template = await repo.create(template_data)

        # Assert
        assert template.id is not None
        assert template.name == "ma_indicator"
        assert template.display_name == "Moving Average"
        assert template.node_type == NodeTypeCategory.INDICATOR.value
        assert template.is_system_template is True
        assert template.user_id is None
        assert template.usage_count == 0
        assert template.version == "1.0.0"
        assert template.parameter_schema["period"]["default"] == 20

    async def test_create_custom_node_template(self, db_session: AsyncSession):
        """Test creating a user-defined custom node template"""
        # Arrange
        repo = NodeTemplateRepository(db_session)
        template_data = {
            "name": "custom_signal",
            "display_name": "My Custom Signal",
            "description": "Custom signal logic",
            "node_type": NodeTypeCategory.SIGNAL.value,
            "category": "CUSTOM",
            "parameter_schema": {},
            "default_parameters": {},
            "input_ports": [{"name": "condition", "type": "boolean", "required": True}],
            "output_ports": [{"name": "signal", "type": "string"}],
            "is_system_template": False,
            "user_id": "user_123"
        }

        # Act
        template = await repo.create(template_data, user_id="user_123")

        # Assert
        assert template.id is not None
        assert template.name == "custom_signal"
        assert template.is_system_template is False
        assert template.user_id == "user_123"
        assert template.created_by == "user_123"

    async def test_create_template_with_validation_rules(self, db_session: AsyncSession):
        """Test creating template with validation rules"""
        # Arrange
        repo = NodeTemplateRepository(db_session)
        template_data = {
            "name": "conditional_node",
            "display_name": "Conditional Logic",
            "node_type": NodeTypeCategory.CONDITION.value,
            "parameter_schema": {},
            "default_parameters": {},
            "input_ports": [],
            "output_ports": [],
            "is_system_template": True,
            "validation_rules": {
                "max_connections": 10,
                "required_inputs": ["value1", "value2"]
            },
            "execution_hints": {
                "cache_result": True,
                "parallel_execution": False
            }
        }

        # Act
        template = await repo.create(template_data)

        # Assert
        assert template.validation_rules is not None
        assert template.validation_rules["max_connections"] == 10
        assert template.execution_hints["cache_result"] is True


@pytest.mark.asyncio
class TestNodeTemplateRepositoryQuery:
    """Test NodeTemplate query operations"""

    async def test_find_by_node_type(self, db_session: AsyncSession):
        """Test finding templates by node type"""
        # Arrange
        repo = NodeTemplateRepository(db_session)

        # Create multiple templates of different types
        indicator_template = await repo.create({
            "name": "ma_indicator",
            "display_name": "MA",
            "node_type": NodeTypeCategory.INDICATOR.value,
            "parameter_schema": {},
            "default_parameters": {},
            "input_ports": [],
            "output_ports": [],
            "is_system_template": True
        })

        signal_template = await repo.create({
            "name": "buy_signal",
            "display_name": "Buy Signal",
            "node_type": NodeTypeCategory.SIGNAL.value,
            "parameter_schema": {},
            "default_parameters": {},
            "input_ports": [],
            "output_ports": [],
            "is_system_template": True
        })

        # Act
        indicator_templates = await repo.find_by_type(NodeTypeCategory.INDICATOR)
        signal_templates = await repo.find_by_type(NodeTypeCategory.SIGNAL)

        # Assert
        assert len(indicator_templates) == 1
        assert indicator_templates[0].name == "ma_indicator"
        assert len(signal_templates) == 1
        assert signal_templates[0].name == "buy_signal"

    async def test_find_by_user_and_type(self, db_session: AsyncSession):
        """Test finding templates by user ID and node type"""
        # Arrange
        repo = NodeTemplateRepository(db_session)

        # Create templates for different users
        user1_template = await repo.create({
            "name": "user1_indicator",
            "display_name": "User1 Indicator",
            "node_type": NodeTypeCategory.INDICATOR.value,
            "parameter_schema": {},
            "default_parameters": {},
            "input_ports": [],
            "output_ports": [],
            "is_system_template": False,
            "user_id": "user_1"
        })

        user2_template = await repo.create({
            "name": "user2_indicator",
            "display_name": "User2 Indicator",
            "node_type": NodeTypeCategory.INDICATOR.value,
            "parameter_schema": {},
            "default_parameters": {},
            "input_ports": [],
            "output_ports": [],
            "is_system_template": False,
            "user_id": "user_2"
        })

        # Act
        user1_templates = await repo.find_by_user_and_type("user_1", NodeTypeCategory.INDICATOR)
        user2_templates = await repo.find_by_user_and_type("user_2", NodeTypeCategory.INDICATOR)

        # Assert
        assert len(user1_templates) == 1
        assert user1_templates[0].name == "user1_indicator"
        assert len(user2_templates) == 1
        assert user2_templates[0].name == "user2_indicator"

    async def test_search_templates_with_filters(self, db_session: AsyncSession):
        """Test complex template search with multiple filters"""
        # Arrange
        repo = NodeTemplateRepository(db_session)

        # Create various templates
        await repo.create({
            "name": "ma_indicator",
            "display_name": "Moving Average",
            "node_type": NodeTypeCategory.INDICATOR.value,
            "category": "TREND",
            "parameter_schema": {},
            "default_parameters": {},
            "input_ports": [],
            "output_ports": [],
            "is_system_template": True
        })

        await repo.create({
            "name": "rsi_indicator",
            "display_name": "RSI",
            "node_type": NodeTypeCategory.INDICATOR.value,
            "category": "MOMENTUM",
            "parameter_schema": {},
            "default_parameters": {},
            "input_ports": [],
            "output_ports": [],
            "is_system_template": True
        })

        await repo.create({
            "name": "custom_indicator",
            "display_name": "Custom Indicator",
            "node_type": NodeTypeCategory.INDICATOR.value,
            "category": "CUSTOM",
            "parameter_schema": {},
            "default_parameters": {},
            "input_ports": [],
            "output_ports": [],
            "is_system_template": False,
            "user_id": "user_1"
        })

        # Act - Search system templates only
        system_templates = await repo.search(
            is_system_template=True,
            node_type=NodeTypeCategory.INDICATOR
        )

        # Act - Search by category
        trend_templates = await repo.search(
            category="TREND"
        )

        # Act - Search by keyword
        ma_templates = await repo.search(
            keyword="Moving"
        )

        # Assert
        assert len(system_templates) == 2
        assert len(trend_templates) == 1
        assert trend_templates[0].name == "ma_indicator"
        assert len(ma_templates) >= 1
        assert any(t.name == "ma_indicator" for t in ma_templates)


@pytest.mark.asyncio
class TestNodeTemplateRepositoryUsage:
    """Test NodeTemplate usage tracking"""

    async def test_increment_usage_count(self, db_session: AsyncSession):
        """Test atomic increment of template usage count"""
        # Arrange
        repo = NodeTemplateRepository(db_session)
        template = await repo.create({
            "name": "test_template",
            "display_name": "Test",
            "node_type": NodeTypeCategory.INDICATOR.value,
            "parameter_schema": {},
            "default_parameters": {},
            "input_ports": [],
            "output_ports": [],
            "is_system_template": True
        })

        initial_count = template.usage_count
        assert initial_count == 0

        # Act - Increment multiple times
        await repo.increment_usage(template.id)
        await repo.increment_usage(template.id)
        await repo.increment_usage(template.id)

        # Assert
        updated_template = await repo.get(template.id)
        assert updated_template.usage_count == 3

    async def test_increment_usage_count_nonexistent_template(self, db_session: AsyncSession):
        """Test increment usage for non-existent template returns None"""
        # Arrange
        repo = NodeTemplateRepository(db_session)

        # Act
        result = await repo.increment_usage("nonexistent_id")

        # Assert
        assert result is None


@pytest.mark.asyncio
class TestNodeTemplateRepositoryCRUD:
    """Test basic CRUD operations"""

    async def test_get_template_by_id(self, db_session: AsyncSession):
        """Test retrieving template by ID"""
        # Arrange
        repo = NodeTemplateRepository(db_session)
        template = await repo.create({
            "name": "test_get",
            "display_name": "Test Get",
            "node_type": NodeTypeCategory.SIGNAL.value,
            "parameter_schema": {},
            "default_parameters": {},
            "input_ports": [],
            "output_ports": [],
            "is_system_template": True
        })

        # Act
        retrieved = await repo.get(template.id)

        # Assert
        assert retrieved is not None
        assert retrieved.id == template.id
        assert retrieved.name == "test_get"

    async def test_update_template(self, db_session: AsyncSession):
        """Test updating template attributes"""
        # Arrange
        repo = NodeTemplateRepository(db_session)
        template = await repo.create({
            "name": "test_update",
            "display_name": "Original Name",
            "node_type": NodeTypeCategory.INDICATOR.value,
            "parameter_schema": {},
            "default_parameters": {},
            "input_ports": [],
            "output_ports": [],
            "is_system_template": True
        })

        # Act
        updated = await repo.update(template.id, {
            "display_name": "Updated Name",
            "description": "New description"
        })

        # Assert
        assert updated is not None
        assert updated.display_name == "Updated Name"
        assert updated.description == "New description"

    async def test_delete_template(self, db_session: AsyncSession):
        """Test soft delete of template"""
        # Arrange
        repo = NodeTemplateRepository(db_session)
        template = await repo.create({
            "name": "test_delete",
            "display_name": "Test Delete",
            "node_type": NodeTypeCategory.CONDITION.value,
            "parameter_schema": {},
            "default_parameters": {},
            "input_ports": [],
            "output_ports": [],
            "is_system_template": True
        })

        # Act
        success = await repo.delete(template.id, soft=True)

        # Assert
        assert success is True
        deleted = await repo.get(template.id)
        assert deleted is None  # Should not be found (soft deleted)

        # Should be found when including deleted
        deleted = await repo.get(template.id, include_deleted=True)
        assert deleted is not None
        assert deleted.is_deleted is True

    async def test_get_multi_with_pagination(self, db_session: AsyncSession):
        """Test retrieving multiple templates with pagination"""
        # Arrange
        repo = NodeTemplateRepository(db_session)

        # Create 5 templates
        for i in range(5):
            await repo.create({
                "name": f"template_{i}",
                "display_name": f"Template {i}",
                "node_type": NodeTypeCategory.INDICATOR.value,
                "parameter_schema": {},
                "default_parameters": {},
                "input_ports": [],
                "output_ports": [],
                "is_system_template": True
            })

        # Act - Get first page
        page1 = await repo.get_multi(skip=0, limit=3)
        page2 = await repo.get_multi(skip=3, limit=3)

        # Assert
        assert len(page1) == 3
        assert len(page2) == 2


@pytest.mark.asyncio
class TestNodeTemplateRepositoryAdvanced:
    """Test advanced repository features"""

    async def test_count_templates(self, db_session: AsyncSession):
        """Test counting templates with filters"""
        # Arrange
        repo = NodeTemplateRepository(db_session)

        # Create templates
        await repo.create({
            "name": "template_1",
            "display_name": "Template 1",
            "node_type": NodeTypeCategory.INDICATOR.value,
            "parameter_schema": {},
            "default_parameters": {},
            "input_ports": [],
            "output_ports": [],
            "is_system_template": True
        })

        await repo.create({
            "name": "template_2",
            "display_name": "Template 2",
            "node_type": NodeTypeCategory.SIGNAL.value,
            "parameter_schema": {},
            "default_parameters": {},
            "input_ports": [],
            "output_ports": [],
            "is_system_template": True
        })

        # Act
        total_count = await repo.count()
        indicator_count = await repo.count(node_type=NodeTypeCategory.INDICATOR.value)

        # Assert
        assert total_count == 2
        assert indicator_count == 1

    async def test_search_by_name_keyword(self, db_session: AsyncSession):
        """Test searching templates by name keyword"""
        # Arrange
        repo = NodeTemplateRepository(db_session)

        await repo.create({
            "name": "moving_average",
            "display_name": "Moving Average Indicator",
            "node_type": NodeTypeCategory.INDICATOR.value,
            "parameter_schema": {},
            "default_parameters": {},
            "input_ports": [],
            "output_ports": [],
            "is_system_template": True
        })

        await repo.create({
            "name": "rsi_oscillator",
            "display_name": "RSI Oscillator",
            "node_type": NodeTypeCategory.INDICATOR.value,
            "parameter_schema": {},
            "default_parameters": {},
            "input_ports": [],
            "output_ports": [],
            "is_system_template": True
        })

        # Act
        average_results = await repo.search(keyword="average")
        rsi_results = await repo.search(keyword="RSI")

        # Assert
        assert len(average_results) >= 1
        assert any("average" in t.name.lower() or "average" in t.display_name.lower()
                  for t in average_results)
        assert len(rsi_results) >= 1
        assert any("rsi" in t.name.lower() or "rsi" in t.display_name.lower()
                  for t in rsi_results)
