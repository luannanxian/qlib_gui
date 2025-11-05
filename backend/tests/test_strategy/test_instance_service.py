"""
Test InstanceService

Tests for strategy instance service business logic following TDD methodology:
- Create strategy from template
- Create custom strategy
- Duplicate strategy
- Save/restore snapshots
- Version management
"""

import pytest
from copy import deepcopy
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.strategy.services.instance_service import InstanceService
from app.database.models.strategy import StrategyTemplate, StrategyInstance, StrategyStatus, StrategyCategory
from app.database.repositories.strategy_instance import StrategyInstanceRepository


@pytest.fixture
def instance_service(db_session: AsyncSession):
    """Create InstanceService instance"""
    return InstanceService(db_session)


@pytest.fixture
async def sample_template(db_session: AsyncSession):
    """Create a sample template for testing"""
    template = StrategyTemplate(
        id="test-template-1",
        name="MA Cross Template",
        category=StrategyCategory.TREND_FOLLOWING,
        description="Moving Average Crossover",
        logic_flow={
            "nodes": [
                {"id": "ma5", "type": "INDICATOR", "indicator": "MA", "parameters": {"period": 5}},
                {"id": "ma20", "type": "INDICATOR", "indicator": "MA", "parameters": {"period": 20}},
                {"id": "buy_signal", "type": "SIGNAL", "signal_type": "BUY"}
            ],
            "edges": [
                {"from": "ma5", "to": "buy_signal"},
                {"from": "ma20", "to": "buy_signal"}
            ]
        },
        parameters={
            "ma_short_period": {"type": "int", "default": 5, "min": 3, "max": 20},
            "ma_long_period": {"type": "int", "default": 20, "min": 10, "max": 60}
        },
        is_system_template=True,
        usage_count=0,
        rating_average=4.5,
        rating_count=10,
    )
    db_session.add(template)
    await db_session.commit()
    return template


class TestCreateFromTemplate:
    """Test create_from_template method"""

    async def test_create_with_default_parameters(
        self, instance_service: InstanceService, sample_template, db_session: AsyncSession
    ):
        """Should create strategy instance with default parameters from template"""
        # Act
        instance = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="My MA Strategy"
        )

        # Assert
        assert instance is not None
        assert instance.name == "My MA Strategy"
        assert instance.template_id == "test-template-1"
        assert instance.user_id == "user-123"
        assert instance.version == 1
        assert instance.parent_version_id is None
        assert instance.status == StrategyStatus.DRAFT

        # Verify logic_flow is cloned
        assert instance.logic_flow == sample_template.logic_flow
        assert instance.logic_flow is not sample_template.logic_flow  # Deep copy

        # Verify default parameters are used
        assert "ma_short_period" in instance.parameters
        assert instance.parameters["ma_short_period"] == 5

    async def test_create_with_custom_parameters(
        self, instance_service: InstanceService, sample_template
    ):
        """Should override default parameters with custom values"""
        # Act
        instance = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Custom MA Strategy",
            parameters={"ma_short_period": 10, "ma_long_period": 30}
        )

        # Assert
        assert instance.parameters["ma_short_period"] == 10
        assert instance.parameters["ma_long_period"] == 30

    async def test_increment_usage_count(
        self, instance_service: InstanceService, sample_template, db_session: AsyncSession
    ):
        """Should increment template usage_count"""
        # Arrange
        initial_count = sample_template.usage_count

        # Act
        await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test Strategy"
        )

        # Assert
        await db_session.refresh(sample_template)
        assert sample_template.usage_count == initial_count + 1

    async def test_invalid_template_id(self, instance_service: InstanceService):
        """Should raise error for non-existent template"""
        # Act & Assert
        with pytest.raises(ValueError, match="Template not found"):
            await instance_service.create_from_template(
                template_id="non-existent",
                user_id="user-123",
                name="Test"
            )

    async def test_partial_parameter_override(
        self, instance_service: InstanceService, sample_template
    ):
        """Should merge custom parameters with defaults"""
        # Act
        instance = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Partial Override",
            parameters={"ma_short_period": 7}  # Only override one parameter
        )

        # Assert
        assert instance.parameters["ma_short_period"] == 7
        assert instance.parameters["ma_long_period"] == 20  # Default value


class TestCreateCustom:
    """Test create_custom method"""

    async def test_create_custom_strategy(self, instance_service: InstanceService):
        """Should create strategy without template"""
        # Arrange
        logic_flow = {
            "nodes": [{"id": "rsi", "type": "INDICATOR", "indicator": "RSI"}],
            "edges": []
        }
        parameters = {"rsi_period": 14}

        # Act
        instance = await instance_service.create_custom(
            user_id="user-123",
            name="Custom RSI Strategy",
            logic_flow=logic_flow,
            parameters=parameters
        )

        # Assert
        assert instance is not None
        assert instance.name == "Custom RSI Strategy"
        assert instance.template_id is None
        assert instance.user_id == "user-123"
        assert instance.logic_flow == logic_flow
        assert instance.parameters == parameters
        assert instance.version == 1

    async def test_custom_strategy_default_status(self, instance_service: InstanceService):
        """Should set default status to DRAFT"""
        # Act
        instance = await instance_service.create_custom(
            user_id="user-123",
            name="Test",
            logic_flow={"nodes": [], "edges": []},
            parameters={}
        )

        # Assert
        assert instance.status == StrategyStatus.DRAFT


class TestDuplicateStrategy:
    """Test duplicate_strategy method"""

    async def test_duplicate_existing_strategy(
        self, instance_service: InstanceService, sample_template, db_session: AsyncSession
    ):
        """Should create copy of existing strategy"""
        # Arrange - Create original strategy
        original = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Original Strategy"
        )

        # Act
        duplicate = await instance_service.duplicate_strategy(
            strategy_id=original.id,
            user_id="user-123",
            new_name="Copied Strategy"
        )

        # Assert
        assert duplicate.id != original.id
        assert duplicate.name == "Copied Strategy"
        assert duplicate.user_id == "user-123"
        assert duplicate.template_id == original.template_id
        assert duplicate.logic_flow == original.logic_flow
        assert duplicate.parameters == original.parameters
        assert duplicate.version == 1
        assert duplicate.parent_version_id is None

    async def test_duplicate_unauthorized_user(
        self, instance_service: InstanceService, sample_template
    ):
        """Should raise error when user doesn't own strategy"""
        # Arrange
        original = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Original"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Strategy not found or access denied"):
            await instance_service.duplicate_strategy(
                strategy_id=original.id,
                user_id="user-456",  # Different user
                new_name="Copy"
            )

    async def test_duplicate_nonexistent_strategy(self, instance_service: InstanceService):
        """Should raise error for non-existent strategy"""
        # Act & Assert
        with pytest.raises(ValueError, match="Strategy not found"):
            await instance_service.duplicate_strategy(
                strategy_id="non-existent",
                user_id="user-123",
                new_name="Copy"
            )


class TestSaveSnapshot:
    """Test save_snapshot method"""

    async def test_save_first_snapshot(
        self, instance_service: InstanceService, sample_template, db_session: AsyncSession
    ):
        """Should save first version snapshot"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test Strategy"
        )

        # Act
        snapshot = await instance_service.save_snapshot(
            strategy_id=strategy.id,
            user_id="user-123"
        )

        # Assert
        assert snapshot is not None
        assert snapshot.parent_version_id == strategy.id
        assert snapshot.version == 2  # Snapshot version
        assert snapshot.user_id == "user-123"
        assert snapshot.logic_flow == strategy.logic_flow
        assert snapshot.parameters == strategy.parameters

    async def test_save_multiple_snapshots(
        self, instance_service: InstanceService, sample_template, db_session: AsyncSession
    ):
        """Should save multiple snapshots with incrementing versions"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test"
        )

        # Act
        snap1 = await instance_service.save_snapshot(strategy.id, "user-123")
        snap2 = await instance_service.save_snapshot(strategy.id, "user-123")
        snap3 = await instance_service.save_snapshot(strategy.id, "user-123")

        # Assert
        assert snap1.version == 2
        assert snap2.version == 3
        assert snap3.version == 4

    async def test_max_five_versions_limit(
        self, instance_service: InstanceService, sample_template, db_session: AsyncSession
    ):
        """Should delete oldest version when exceeding 5 snapshots"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test"
        )

        # Act - Save 6 snapshots
        snap1 = await instance_service.save_snapshot(strategy.id, "user-123")
        snap2 = await instance_service.save_snapshot(strategy.id, "user-123")
        snap3 = await instance_service.save_snapshot(strategy.id, "user-123")
        snap4 = await instance_service.save_snapshot(strategy.id, "user-123")
        snap5 = await instance_service.save_snapshot(strategy.id, "user-123")
        snap6 = await instance_service.save_snapshot(strategy.id, "user-123")

        # Assert - Should only have 5 versions (first one deleted)
        existing = await instance_service.get_versions(strategy.id, "user-123")
        assert len(existing) == 5

        # Verify oldest snapshot (snap1) is not in the list
        existing_ids = [s.id for s in existing]
        assert snap1.id not in existing_ids

        # Verify newest snapshots are retained
        assert snap2.id in existing_ids
        assert snap6.id in existing_ids

    async def test_snapshot_unauthorized_user(
        self, instance_service: InstanceService, sample_template
    ):
        """Should raise error for unauthorized user"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Strategy not found or access denied"):
            await instance_service.save_snapshot(strategy.id, "user-456")


class TestRestoreSnapshot:
    """Test restore_snapshot method"""

    async def test_restore_from_snapshot(
        self, instance_service: InstanceService, sample_template, db_session: AsyncSession
    ):
        """Should restore strategy to previous snapshot"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Original",
            parameters={"ma_short_period": 5}
        )

        # Save snapshot
        snapshot = await instance_service.save_snapshot(strategy.id, "user-123")

        # Modify strategy
        repo = StrategyInstanceRepository(db_session)
        await repo.update(strategy.id, {"parameters": {"ma_short_period": 10}}, "user-123")
        await db_session.refresh(strategy)

        # Act - Restore from snapshot
        restored = await instance_service.restore_snapshot(
            strategy_id=strategy.id,
            version_id=snapshot.id,
            user_id="user-123"
        )

        # Assert
        assert restored.parameters["ma_short_period"] == 5  # Restored value

    async def test_restore_unauthorized(
        self, instance_service: InstanceService, sample_template
    ):
        """Should raise error for unauthorized restore"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test"
        )
        snapshot = await instance_service.save_snapshot(strategy.id, "user-123")

        # Act & Assert
        with pytest.raises(ValueError, match="access denied"):
            await instance_service.restore_snapshot(
                strategy_id=strategy.id,
                version_id=snapshot.id,
                user_id="user-456"
            )

    async def test_restore_invalid_snapshot(
        self, instance_service: InstanceService, sample_template
    ):
        """Should raise error for invalid snapshot"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Snapshot not found"):
            await instance_service.restore_snapshot(
                strategy_id=strategy.id,
                version_id="invalid-id",
                user_id="user-123"
            )


class TestGetVersions:
    """Test get_versions method"""

    async def test_get_version_history(
        self, instance_service: InstanceService, sample_template
    ):
        """Should return all version snapshots"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test"
        )

        snap1 = await instance_service.save_snapshot(strategy.id, "user-123")
        snap2 = await instance_service.save_snapshot(strategy.id, "user-123")

        # Act
        versions = await instance_service.get_versions(strategy.id, "user-123")

        # Assert
        assert len(versions) == 2
        assert versions[0].id in [snap1.id, snap2.id]
        assert all(v.parent_version_id == strategy.id for v in versions)

    async def test_get_versions_empty(
        self, instance_service: InstanceService, sample_template
    ):
        """Should return empty list when no snapshots exist"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test"
        )

        # Act
        versions = await instance_service.get_versions(strategy.id, "user-123")

        # Assert
        assert len(versions) == 0

    async def test_get_versions_unauthorized(
        self, instance_service: InstanceService, sample_template
    ):
        """Should raise error for unauthorized access"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="access denied"):
            await instance_service.get_versions(strategy.id, "user-456")

    async def test_versions_sorted_by_created_at(
        self, instance_service: InstanceService, sample_template
    ):
        """Should return versions sorted by creation time descending"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test"
        )

        snap1 = await instance_service.save_snapshot(strategy.id, "user-123")
        snap2 = await instance_service.save_snapshot(strategy.id, "user-123")
        snap3 = await instance_service.save_snapshot(strategy.id, "user-123")

        # Act
        versions = await instance_service.get_versions(strategy.id, "user-123")

        # Assert - Most recent first
        assert versions[0].id == snap3.id
        assert versions[1].id == snap2.id
        assert versions[2].id == snap1.id
