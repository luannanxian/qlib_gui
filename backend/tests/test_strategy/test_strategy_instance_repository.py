"""
TDD Tests for StrategyInstanceRepository

Following strict TDD methodology:
1. Write failing tests first
2. Implement minimal code to pass
3. Refactor

Test Coverage:
- CRUD operations
- User-specific queries
- Template-based queries
- Version history management
- Status filtering
- Snapshot management (max 5 versions)
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy import (
    StrategyInstance,
    StrategyTemplate,
    StrategyStatus,
    StrategyCategory
)
from app.database.repositories.strategy_instance import StrategyInstanceRepository
from app.database.repositories.strategy_template import StrategyTemplateRepository


@pytest.mark.asyncio
class TestStrategyInstanceRepositoryCreate:
    """Test StrategyInstance creation"""

    async def test_create_instance_from_template(self, db_session: AsyncSession):
        """Test creating instance from template"""
        template_repo = StrategyTemplateRepository(db_session)
        instance_repo = StrategyInstanceRepository(db_session)

        # Create a template first
        template = await template_repo.create({
            "name": "Double MA Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [{"id": "1", "type": "INDICATOR"}], "edges": []},
            "parameters": {"short_period": {"default": 10, "min": 5, "max": 50}},
            "is_system_template": True
        })

        # Create instance from template
        instance_data = {
            "name": "My MA Strategy",
            "template_id": template.id,
            "user_id": "user_123",
            "logic_flow": template.logic_flow,
            "parameters": {"short_period": 15},
            "status": StrategyStatus.DRAFT.value
        }

        instance = await instance_repo.create(instance_data, user_id="user_123")

        assert instance.id is not None
        assert instance.name == "My MA Strategy"
        assert instance.template_id == template.id
        assert instance.user_id == "user_123"
        assert instance.status == StrategyStatus.DRAFT.value
        assert instance.version == 1
        assert instance.parent_version_id is None
        assert instance.created_by == "user_123"

    async def test_create_custom_instance_without_template(self, db_session: AsyncSession):
        """Test creating custom instance without template"""
        instance_repo = StrategyInstanceRepository(db_session)

        instance_data = {
            "name": "Custom Strategy",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {},
            "status": StrategyStatus.DRAFT.value
        }

        instance = await instance_repo.create(instance_data, user_id="user_123")

        assert instance.id is not None
        assert instance.name == "Custom Strategy"
        assert instance.template_id is None
        assert instance.user_id == "user_123"

    async def test_create_instance_with_default_status(self, db_session: AsyncSession):
        """Test instance creation defaults to DRAFT status"""
        instance_repo = StrategyInstanceRepository(db_session)

        instance_data = {
            "name": "Strategy",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []}
        }

        instance = await instance_repo.create(instance_data, user_id="user_123")

        assert instance.status == StrategyStatus.DRAFT.value
        assert instance.version == 1


@pytest.mark.asyncio
class TestStrategyInstanceRepositoryRead:
    """Test StrategyInstance read operations"""

    async def test_get_by_id(self, db_session: AsyncSession):
        """Test retrieving instance by ID"""
        instance_repo = StrategyInstanceRepository(db_session)

        created = await instance_repo.create({
            "name": "Test Strategy",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []}
        }, user_id="user_123")

        retrieved = await instance_repo.get(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Test Strategy"

    async def test_get_nonexistent_instance(self, db_session: AsyncSession):
        """Test retrieving non-existent instance returns None"""
        instance_repo = StrategyInstanceRepository(db_session)

        result = await instance_repo.get("nonexistent-id")

        assert result is None

    async def test_get_by_user(self, db_session: AsyncSession):
        """Test getting all instances for a user"""
        instance_repo = StrategyInstanceRepository(db_session)

        # Create instances for different users
        await instance_repo.create({
            "name": "User 1 Strategy 1",
            "user_id": "user_1",
            "logic_flow": {"nodes": [], "edges": []}
        }, user_id="user_1")
        await instance_repo.create({
            "name": "User 1 Strategy 2",
            "user_id": "user_1",
            "logic_flow": {"nodes": [], "edges": []}
        }, user_id="user_1")
        await instance_repo.create({
            "name": "User 2 Strategy",
            "user_id": "user_2",
            "logic_flow": {"nodes": [], "edges": []}
        }, user_id="user_2")

        user_1_instances = await instance_repo.get_by_user("user_1")

        assert len(user_1_instances) == 2
        assert all(inst.user_id == "user_1" for inst in user_1_instances)

    async def test_get_by_user_with_status_filter(self, db_session: AsyncSession):
        """Test getting user instances filtered by status"""
        instance_repo = StrategyInstanceRepository(db_session)

        await instance_repo.create({
            "name": "Draft Strategy",
            "user_id": "user_1",
            "logic_flow": {"nodes": [], "edges": []},
            "status": StrategyStatus.DRAFT.value
        }, user_id="user_1")
        await instance_repo.create({
            "name": "Active Strategy",
            "user_id": "user_1",
            "logic_flow": {"nodes": [], "edges": []},
            "status": StrategyStatus.ACTIVE.value
        }, user_id="user_1")

        active_instances = await instance_repo.get_by_user(
            "user_1",
            status=StrategyStatus.ACTIVE.value
        )

        assert len(active_instances) == 1
        assert active_instances[0].name == "Active Strategy"

    async def test_get_by_template(self, db_session: AsyncSession):
        """Test getting all instances of a template"""
        template_repo = StrategyTemplateRepository(db_session)
        instance_repo = StrategyInstanceRepository(db_session)

        # Create template
        template = await template_repo.create({
            "name": "Template",
            "category": StrategyCategory.TREND_FOLLOWING.value,
            "logic_flow": {"nodes": [], "edges": []},
            "is_system_template": True
        })

        # Create instances from template
        await instance_repo.create({
            "name": "Instance 1",
            "template_id": template.id,
            "user_id": "user_1",
            "logic_flow": {"nodes": [], "edges": []}
        }, user_id="user_1")
        await instance_repo.create({
            "name": "Instance 2",
            "template_id": template.id,
            "user_id": "user_2",
            "logic_flow": {"nodes": [], "edges": []}
        }, user_id="user_2")

        template_instances = await instance_repo.get_by_template(template.id)

        assert len(template_instances) == 2
        assert all(inst.template_id == template.id for inst in template_instances)

    async def test_get_active_strategies(self, db_session: AsyncSession):
        """Test getting only active strategies"""
        instance_repo = StrategyInstanceRepository(db_session)

        await instance_repo.create({
            "name": "Draft",
            "user_id": "user_1",
            "logic_flow": {"nodes": [], "edges": []},
            "status": StrategyStatus.DRAFT.value
        }, user_id="user_1")
        await instance_repo.create({
            "name": "Active 1",
            "user_id": "user_1",
            "logic_flow": {"nodes": [], "edges": []},
            "status": StrategyStatus.ACTIVE.value
        }, user_id="user_1")
        await instance_repo.create({
            "name": "Active 2",
            "user_id": "user_2",
            "logic_flow": {"nodes": [], "edges": []},
            "status": StrategyStatus.ACTIVE.value
        }, user_id="user_2")

        active = await instance_repo.get_active_strategies()

        assert len(active) == 2
        assert all(inst.status == StrategyStatus.ACTIVE.value for inst in active)

    async def test_count_instances(self, db_session: AsyncSession):
        """Test counting instances"""
        instance_repo = StrategyInstanceRepository(db_session)

        for i in range(3):
            await instance_repo.create({
                "name": f"Strategy {i}",
                "user_id": "user_1",
                "logic_flow": {"nodes": [], "edges": []}
            }, user_id="user_1")

        total = await instance_repo.count()

        assert total == 3


@pytest.mark.asyncio
class TestStrategyInstanceRepositoryUpdate:
    """Test StrategyInstance update operations"""

    async def test_update_instance_basic(self, db_session: AsyncSession):
        """Test updating instance basic fields"""
        instance_repo = StrategyInstanceRepository(db_session)

        instance = await instance_repo.create({
            "name": "Original Name",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []}
        }, user_id="user_123")

        updated = await instance_repo.update(
            instance.id,
            {"name": "Updated Name", "status": StrategyStatus.ACTIVE.value},
            user_id="user_123"
        )

        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.status == StrategyStatus.ACTIVE.value
        assert updated.updated_by == "user_123"

    async def test_update_logic_flow_and_parameters(self, db_session: AsyncSession):
        """Test updating logic flow and parameters"""
        instance_repo = StrategyInstanceRepository(db_session)

        instance = await instance_repo.create({
            "name": "Strategy",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {"old_param": 10}
        }, user_id="user_123")

        new_logic_flow = {"nodes": [{"id": "1", "type": "INDICATOR"}], "edges": []}
        new_parameters = {"new_param": 20}

        updated = await instance_repo.update(
            instance.id,
            {"logic_flow": new_logic_flow, "parameters": new_parameters},
            user_id="user_123"
        )

        assert updated.logic_flow == new_logic_flow
        assert updated.parameters == new_parameters

    async def test_update_nonexistent_instance(self, db_session: AsyncSession):
        """Test updating non-existent instance returns None"""
        instance_repo = StrategyInstanceRepository(db_session)

        result = await instance_repo.update("nonexistent-id", {"name": "New Name"})

        assert result is None


@pytest.mark.asyncio
class TestStrategyInstanceRepositoryDelete:
    """Test StrategyInstance delete operations"""

    async def test_soft_delete_instance(self, db_session: AsyncSession):
        """Test soft deleting an instance"""
        instance_repo = StrategyInstanceRepository(db_session)

        instance = await instance_repo.create({
            "name": "To Delete",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []}
        }, user_id="user_123")

        success = await instance_repo.delete(instance.id, soft=True)

        assert success is True

        # Should not be found by default
        retrieved = await instance_repo.get(instance.id)
        assert retrieved is None

        # Should be found when including deleted
        deleted = await instance_repo.get(instance.id, include_deleted=True)
        assert deleted is not None
        assert deleted.is_deleted is True

    async def test_hard_delete_instance(self, db_session: AsyncSession):
        """Test hard deleting an instance"""
        instance_repo = StrategyInstanceRepository(db_session)

        instance = await instance_repo.create({
            "name": "To Delete",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []}
        }, user_id="user_123")

        success = await instance_repo.delete(instance.id, soft=False)

        assert success is True

        # Should not be found even when including deleted
        retrieved = await instance_repo.get(instance.id, include_deleted=True)
        assert retrieved is None


@pytest.mark.asyncio
class TestStrategyInstanceRepositoryVersions:
    """Test version history functionality"""

    async def test_create_version_snapshot(self, db_session: AsyncSession):
        """Test creating a version snapshot"""
        instance_repo = StrategyInstanceRepository(db_session)

        # Create original instance
        original = await instance_repo.create({
            "name": "Strategy v1",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {"param": 10}
        }, user_id="user_123")

        # Create snapshot
        snapshot = await instance_repo.create({
            "name": "Strategy v1",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
            "parameters": {"param": 10},
            "parent_version_id": original.id,
            "version": 2
        }, user_id="user_123")

        assert snapshot.parent_version_id == original.id
        assert snapshot.version == 2

    async def test_get_versions(self, db_session: AsyncSession):
        """Test getting version history"""
        instance_repo = StrategyInstanceRepository(db_session)

        # Create base instance
        base = await instance_repo.create({
            "name": "Strategy",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
        }, user_id="user_123")

        # Create 3 snapshots
        for i in range(2, 5):
            await instance_repo.create({
                "name": "Strategy",
                "user_id": "user_123",
                "logic_flow": {"nodes": [], "edges": []},
                "parent_version_id": base.id,
                "version": i
            }, user_id="user_123")

        versions = await instance_repo.get_versions(base.id)

        assert len(versions) == 3
        # Should be sorted by version descending
        assert versions[0].version == 4
        assert versions[1].version == 3
        assert versions[2].version == 2

    async def test_get_latest_version(self, db_session: AsyncSession):
        """Test getting latest version snapshot"""
        instance_repo = StrategyInstanceRepository(db_session)

        base = await instance_repo.create({
            "name": "Strategy",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
        }, user_id="user_123")

        # Create snapshots
        for i in range(2, 4):
            await instance_repo.create({
                "name": "Strategy",
                "user_id": "user_123",
                "logic_flow": {"nodes": [], "edges": []},
                "parent_version_id": base.id,
                "version": i
            }, user_id="user_123")

        latest = await instance_repo.get_latest_version(base.id)

        assert latest is not None
        assert latest.version == 3

    async def test_count_versions(self, db_session: AsyncSession):
        """Test counting version snapshots"""
        instance_repo = StrategyInstanceRepository(db_session)

        base = await instance_repo.create({
            "name": "Strategy",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
        }, user_id="user_123")

        # Create 5 snapshots
        for i in range(2, 7):
            await instance_repo.create({
                "name": "Strategy",
                "user_id": "user_123",
                "logic_flow": {"nodes": [], "edges": []},
                "parent_version_id": base.id,
                "version": i
            }, user_id="user_123")

        count = await instance_repo.count_versions(base.id)

        assert count == 5

    async def test_get_versions_empty_for_no_snapshots(self, db_session: AsyncSession):
        """Test get_versions returns empty list when no snapshots exist"""
        instance_repo = StrategyInstanceRepository(db_session)

        base = await instance_repo.create({
            "name": "Strategy",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
        }, user_id="user_123")

        versions = await instance_repo.get_versions(base.id)

        assert versions == []

    async def test_get_latest_version_none_for_no_snapshots(self, db_session: AsyncSession):
        """Test get_latest_version returns None when no snapshots exist"""
        instance_repo = StrategyInstanceRepository(db_session)

        base = await instance_repo.create({
            "name": "Strategy",
            "user_id": "user_123",
            "logic_flow": {"nodes": [], "edges": []},
        }, user_id="user_123")

        latest = await instance_repo.get_latest_version(base.id)

        assert latest is None


@pytest.mark.asyncio
class TestStrategyInstanceRepositoryPagination:
    """Test pagination functionality"""

    async def test_get_multi_with_pagination(self, db_session: AsyncSession):
        """Test getting instances with pagination"""
        instance_repo = StrategyInstanceRepository(db_session)

        # Create 5 instances
        for i in range(5):
            await instance_repo.create({
                "name": f"Strategy {i}",
                "user_id": "user_1",
                "logic_flow": {"nodes": [], "edges": []}
            }, user_id="user_1")

        # Get first page
        page1 = await instance_repo.get_multi(skip=0, limit=2)
        assert len(page1) == 2

        # Get second page
        page2 = await instance_repo.get_multi(skip=2, limit=2)
        assert len(page2) == 2

        # Ensure different instances
        assert page1[0].id != page2[0].id
