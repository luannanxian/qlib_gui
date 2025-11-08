"""
Test InstanceService

Comprehensive tests for strategy instance service business logic following TDD methodology:
- Create strategy from template
- Create custom strategy
- Duplicate strategy (copy)
- Save/restore snapshots
- Version management
- Edge cases and error handling
"""

import pytest
from copy import deepcopy
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.modules.strategy.services.instance_service import InstanceService
from app.database.models.strategy import (
    StrategyTemplate, StrategyInstance, StrategyStatus, StrategyCategory
)
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


@pytest.fixture
async def complex_template(db_session: AsyncSession):
    """Create a complex template with many parameters for testing"""
    template = StrategyTemplate(
        id="test-template-2",
        name="Complex RSI Strategy",
        category=StrategyCategory.OSCILLATION,
        description="RSI with Multiple Conditions",
        logic_flow={
            "nodes": [
                {"id": "rsi", "type": "INDICATOR", "indicator": "RSI"},
                {"id": "condition1", "type": "CONDITION", "operator": "GREATER_THAN"},
                {"id": "condition2", "type": "CONDITION", "operator": "LESS_THAN"},
                {"id": "buy_signal", "type": "SIGNAL", "signal_type": "BUY"},
                {"id": "sell_signal", "type": "SIGNAL", "signal_type": "SELL"}
            ],
            "edges": [
                {"from": "rsi", "to": "condition1"},
                {"from": "rsi", "to": "condition2"},
                {"from": "condition1", "to": "buy_signal"},
                {"from": "condition2", "to": "sell_signal"}
            ]
        },
        parameters={
            "rsi_period": {"type": "int", "default": 14, "min": 5, "max": 50},
            "rsi_overbought": {"type": "float", "default": 70.0},
            "rsi_oversold": {"type": "float", "default": 30.0},
            "threshold": {"type": "int", "default": 10}
        },
        is_system_template=False,
        usage_count=0,
        rating_average=3.5,
        rating_count=5,
    )
    db_session.add(template)
    await db_session.commit()
    return template


class TestCreateFromTemplate:
    """Test create_from_template method - AAA Pattern"""

    async def test_create_with_default_parameters(
        self, instance_service: InstanceService, sample_template, db_session: AsyncSession
    ):
        """Should create strategy instance with default parameters from template"""
        # Arrange
        template_id = "test-template-1"
        user_id = "user-123"
        name = "My MA Strategy"

        # Act
        instance = await instance_service.create_from_template(
            template_id=template_id,
            user_id=user_id,
            name=name
        )

        # Assert
        assert instance is not None
        assert instance.name == name
        assert instance.template_id == template_id
        assert instance.user_id == user_id
        assert instance.version == 1
        assert instance.parent_version_id is None
        assert instance.status == StrategyStatus.DRAFT
        assert instance.logic_flow == sample_template.logic_flow
        assert instance.logic_flow is not sample_template.logic_flow  # Deep copy
        assert instance.parameters["ma_short_period"] == 5
        assert instance.parameters["ma_long_period"] == 20

    async def test_create_with_custom_parameters(
        self, instance_service: InstanceService, sample_template
    ):
        """Should override default parameters with custom values"""
        # Arrange
        custom_params = {"ma_short_period": 10, "ma_long_period": 30}

        # Act
        instance = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Custom MA Strategy",
            parameters=custom_params
        )

        # Assert
        assert instance.parameters["ma_short_period"] == 10
        assert instance.parameters["ma_long_period"] == 30

    async def test_create_with_empty_parameters(
        self, instance_service: InstanceService, sample_template
    ):
        """Should use defaults when empty parameters dict provided"""
        # Act
        instance = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test",
            parameters={}
        )

        # Assert
        assert instance.parameters["ma_short_period"] == 5
        assert instance.parameters["ma_long_period"] == 20

    async def test_create_with_none_parameters(
        self, instance_service: InstanceService, sample_template
    ):
        """Should use defaults when None parameters provided"""
        # Act
        instance = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test",
            parameters=None
        )

        # Assert
        assert instance.parameters["ma_short_period"] == 5
        assert instance.parameters["ma_long_period"] == 20

    async def test_partial_parameter_override(
        self, instance_service: InstanceService, sample_template
    ):
        """Should merge custom parameters with defaults"""
        # Act
        instance = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Partial Override",
            parameters={"ma_short_period": 7}
        )

        # Assert
        assert instance.parameters["ma_short_period"] == 7
        assert instance.parameters["ma_long_period"] == 20

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

    async def test_multiple_instances_increment_count(
        self, instance_service: InstanceService, sample_template, db_session: AsyncSession
    ):
        """Should increment usage count for each instance created from template"""
        # Arrange
        initial_count = sample_template.usage_count

        # Act
        await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Instance 1"
        )
        await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-456",
            name="Instance 2"
        )

        # Assert
        await db_session.refresh(sample_template)
        assert sample_template.usage_count == initial_count + 2

    async def test_invalid_template_id(self, instance_service: InstanceService):
        """Should raise error for non-existent template"""
        # Act & Assert
        with pytest.raises(ValueError, match="Template not found"):
            await instance_service.create_from_template(
                template_id="non-existent",
                user_id="user-123",
                name="Test"
            )

    async def test_deep_copy_logic_flow(
        self, instance_service: InstanceService, sample_template
    ):
        """Should deep copy logic_flow to avoid mutation"""
        # Act
        instance = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test"
        )

        # Modify instance's logic_flow
        instance.logic_flow["nodes"][0]["indicator"] = "MODIFIED"

        # Assert - Template should not be affected
        assert sample_template.logic_flow["nodes"][0]["indicator"] == "MA"

    async def test_deep_copy_parameters(
        self, instance_service: InstanceService, sample_template
    ):
        """Should deep copy parameters to avoid mutation"""
        # Act
        instance = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test"
        )

        # Modify instance parameters
        instance.parameters["ma_short_period"] = 999

        # This should not affect the template defaults in next creation
        instance2 = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-456",
            name="Test 2"
        )

        assert instance2.parameters["ma_short_period"] == 5

    async def test_complex_template_with_many_parameters(
        self, instance_service: InstanceService, complex_template
    ):
        """Should handle templates with many parameters"""
        # Act
        instance = await instance_service.create_from_template(
            template_id="test-template-2",
            user_id="user-123",
            name="Complex Strategy",
            parameters={"rsi_period": 21}
        )

        # Assert
        assert instance.parameters["rsi_period"] == 21
        assert instance.parameters["rsi_overbought"] == 70.0
        assert instance.parameters["rsi_oversold"] == 30.0
        assert instance.parameters["threshold"] == 10

    async def test_create_multiple_from_same_template(
        self, instance_service: InstanceService, sample_template
    ):
        """Should create multiple independent instances from same template"""
        # Act
        instance1 = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Instance 1",
            parameters={"ma_short_period": 5}
        )
        instance2 = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Instance 2",
            parameters={"ma_short_period": 10}
        )

        # Assert
        assert instance1.id != instance2.id
        assert instance1.parameters["ma_short_period"] == 5
        assert instance2.parameters["ma_short_period"] == 10


class TestCreateCustom:
    """Test create_custom method - AAA Pattern"""

    async def test_create_custom_strategy(self, instance_service: InstanceService):
        """Should create strategy without template"""
        # Arrange
        user_id = "user-123"
        name = "Custom RSI Strategy"
        logic_flow = {
            "nodes": [{"id": "rsi", "type": "INDICATOR", "indicator": "RSI"}],
            "edges": []
        }
        parameters = {"rsi_period": 14}

        # Act
        instance = await instance_service.create_custom(
            user_id=user_id,
            name=name,
            logic_flow=logic_flow,
            parameters=parameters
        )

        # Assert
        assert instance is not None
        assert instance.name == name
        assert instance.template_id is None
        assert instance.user_id == user_id
        assert instance.logic_flow == logic_flow
        assert instance.parameters == parameters
        assert instance.version == 1
        assert instance.status == StrategyStatus.DRAFT
        assert instance.parent_version_id is None

    async def test_create_custom_with_empty_logic_flow(self, instance_service: InstanceService):
        """Should allow creating custom strategy with empty logic flow"""
        # Act
        instance = await instance_service.create_custom(
            user_id="user-123",
            name="Empty Strategy",
            logic_flow={"nodes": [], "edges": []},
            parameters={}
        )

        # Assert
        assert instance.logic_flow == {"nodes": [], "edges": []}
        assert instance.parameters == {}

    async def test_create_custom_with_complex_logic_flow(self, instance_service: InstanceService):
        """Should handle complex logic flow structure"""
        # Arrange
        complex_flow = {
            "nodes": [
                {"id": "n1", "type": "INDICATOR", "indicator": "RSI", "params": {"period": 14}},
                {"id": "n2", "type": "CONDITION", "operator": "GT", "value": 70},
                {"id": "n3", "type": "SIGNAL", "signal_type": "SELL"}
            ],
            "edges": [
                {"from": "n1", "to": "n2"},
                {"from": "n2", "to": "n3"}
            ]
        }

        # Act
        instance = await instance_service.create_custom(
            user_id="user-123",
            name="Complex Custom",
            logic_flow=complex_flow,
            parameters={"threshold": 70}
        )

        # Assert
        assert instance.logic_flow == complex_flow
        assert len(instance.logic_flow["nodes"]) == 3
        assert len(instance.logic_flow["edges"]) == 2

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

    async def test_custom_strategy_no_template_id(self, instance_service: InstanceService):
        """Should have template_id as None for custom strategies"""
        # Act
        instance = await instance_service.create_custom(
            user_id="user-123",
            name="Custom",
            logic_flow={"nodes": [], "edges": []},
            parameters={}
        )

        # Assert
        assert instance.template_id is None

    async def test_create_multiple_custom_strategies(self, instance_service: InstanceService):
        """Should create multiple independent custom strategies"""
        # Act
        instance1 = await instance_service.create_custom(
            user_id="user-123",
            name="Custom 1",
            logic_flow={"nodes": [{"id": "n1"}], "edges": []},
            parameters={"param": 1}
        )
        instance2 = await instance_service.create_custom(
            user_id="user-123",
            name="Custom 2",
            logic_flow={"nodes": [{"id": "n2"}], "edges": []},
            parameters={"param": 2}
        )

        # Assert
        assert instance1.id != instance2.id
        assert instance1.parameters["param"] == 1
        assert instance2.parameters["param"] == 2


class TestDuplicateStrategy:
    """Test duplicate_strategy method - AAA Pattern"""

    async def test_duplicate_existing_strategy(
        self, instance_service: InstanceService, sample_template, db_session: AsyncSession
    ):
        """Should create copy of existing strategy"""
        # Arrange
        original = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Original Strategy"
        )
        new_name = "Copied Strategy"

        # Act
        duplicate = await instance_service.duplicate_strategy(
            strategy_id=original.id,
            user_id="user-123",
            new_name=new_name
        )

        # Assert
        assert duplicate.id != original.id
        assert duplicate.name == new_name
        assert duplicate.user_id == "user-123"
        assert duplicate.template_id == original.template_id
        assert duplicate.logic_flow == original.logic_flow
        assert duplicate.parameters == original.parameters
        assert duplicate.version == 1
        assert duplicate.parent_version_id is None
        assert duplicate.status == StrategyStatus.DRAFT

    async def test_duplicate_custom_strategy(self, instance_service: InstanceService):
        """Should duplicate custom strategies without template"""
        # Arrange
        original = await instance_service.create_custom(
            user_id="user-123",
            name="Custom Strategy",
            logic_flow={"nodes": [{"id": "test"}], "edges": []},
            parameters={"custom_param": 42}
        )

        # Act
        duplicate = await instance_service.duplicate_strategy(
            strategy_id=original.id,
            user_id="user-123",
            new_name="Duplicated Custom"
        )

        # Assert
        assert duplicate.template_id is None
        assert duplicate.parameters["custom_param"] == 42

    async def test_duplicate_preserves_deep_copy(
        self, instance_service: InstanceService, sample_template, db_session: AsyncSession
    ):
        """Should deep copy logic_flow and parameters"""
        # Arrange
        original = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Original"
        )

        # Act
        duplicate = await instance_service.duplicate_strategy(
            strategy_id=original.id,
            user_id="user-123",
            new_name="Duplicate"
        )

        # Modify duplicate
        duplicate.logic_flow["nodes"][0]["indicator"] = "MODIFIED"
        duplicate.parameters["ma_short_period"] = 999

        # Assert - Original should not be affected
        assert original.logic_flow["nodes"][0]["indicator"] == "MA"

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
                user_id="user-456",
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

    async def test_duplicate_with_different_name(
        self, instance_service: InstanceService, sample_template
    ):
        """Should allow changing name when duplicating"""
        # Arrange
        original = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Original"
        )

        # Act
        duplicate = await instance_service.duplicate_strategy(
            strategy_id=original.id,
            user_id="user-123",
            new_name="Completely Different Name"
        )

        # Assert
        assert duplicate.name == "Completely Different Name"
        assert duplicate.name != original.name

    async def test_duplicate_multiple_times(
        self, instance_service: InstanceService, sample_template
    ):
        """Should allow duplicating same strategy multiple times"""
        # Arrange
        original = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Original"
        )

        # Act
        duplicate1 = await instance_service.duplicate_strategy(
            strategy_id=original.id,
            user_id="user-123",
            new_name="Duplicate 1"
        )
        duplicate2 = await instance_service.duplicate_strategy(
            strategy_id=original.id,
            user_id="user-123",
            new_name="Duplicate 2"
        )

        # Assert
        assert duplicate1.id != duplicate2.id
        assert duplicate1.name == "Duplicate 1"
        assert duplicate2.name == "Duplicate 2"


class TestSaveSnapshot:
    """Test save_snapshot method - AAA Pattern"""

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
        assert snapshot.version == 2
        assert snapshot.user_id == "user-123"
        assert snapshot.logic_flow == strategy.logic_flow
        assert snapshot.parameters == strategy.parameters
        assert snapshot.name == strategy.name
        assert snapshot.status == strategy.status

    async def test_save_snapshot_deep_copy(
        self, instance_service: InstanceService, sample_template
    ):
        """Should deep copy logic_flow and parameters in snapshot"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test"
        )

        # Act
        snapshot = await instance_service.save_snapshot(strategy.id, "user-123")

        # Modify strategy's logic_flow
        strategy.logic_flow["nodes"][0]["indicator"] = "MODIFIED"
        strategy.parameters["ma_short_period"] = 999

        # Assert - Snapshot should not be affected
        assert snapshot.logic_flow["nodes"][0]["indicator"] == "MA"
        assert snapshot.parameters["ma_short_period"] == 5

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
        assert snap1.parent_version_id == strategy.id
        assert snap2.parent_version_id == strategy.id
        assert snap3.parent_version_id == strategy.id

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

        # Act - Save 6 snapshots (versions 2, 3, 4, 5, 6, 7)
        snap1 = await instance_service.save_snapshot(strategy.id, "user-123")
        snap2 = await instance_service.save_snapshot(strategy.id, "user-123")
        snap3 = await instance_service.save_snapshot(strategy.id, "user-123")
        snap4 = await instance_service.save_snapshot(strategy.id, "user-123")
        snap5 = await instance_service.save_snapshot(strategy.id, "user-123")
        snap6 = await instance_service.save_snapshot(strategy.id, "user-123")

        # Assert - Should only have 5 versions (oldest deleted)
        existing = await instance_service.get_versions(strategy.id, "user-123")
        assert len(existing) == 5

        # Verify oldest snapshot (snap1) is not in the list
        existing_ids = [s.id for s in existing]
        assert snap1.id not in existing_ids

        # Verify remaining snapshots are retained
        assert snap2.id in existing_ids
        assert snap6.id in existing_ids

    async def test_snapshot_preserves_strategy_status(
        self, instance_service: InstanceService, sample_template
    ):
        """Should preserve strategy status in snapshot"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test"
        )

        # Act
        snapshot = await instance_service.save_snapshot(strategy.id, "user-123")

        # Assert
        assert snapshot.status == StrategyStatus.DRAFT

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

    async def test_snapshot_nonexistent_strategy(self, instance_service: InstanceService):
        """Should raise error for non-existent strategy"""
        # Act & Assert
        with pytest.raises(ValueError, match="Strategy not found"):
            await instance_service.save_snapshot("non-existent", "user-123")


class TestRestoreSnapshot:
    """Test restore_snapshot method - AAA Pattern"""

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

        # Act
        restored = await instance_service.restore_snapshot(
            strategy_id=strategy.id,
            version_id=snapshot.id,
            user_id="user-123"
        )

        # Assert
        assert restored.parameters["ma_short_period"] == 5
        assert restored.id == strategy.id  # Same strategy ID

    async def test_restore_logic_flow(
        self, instance_service: InstanceService, sample_template, db_session: AsyncSession
    ):
        """Should restore both logic_flow and parameters"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test"
        )
        original_logic = deepcopy(strategy.logic_flow)

        # Save snapshot
        snapshot = await instance_service.save_snapshot(strategy.id, "user-123")

        # Modify logic_flow
        repo = StrategyInstanceRepository(db_session)
        modified_logic = deepcopy(original_logic)
        modified_logic["nodes"][0]["indicator"] = "MODIFIED"
        await repo.update(strategy.id, {"logic_flow": modified_logic}, "user-123")

        # Act
        restored = await instance_service.restore_snapshot(
            strategy_id=strategy.id,
            version_id=snapshot.id,
            user_id="user-123"
        )

        # Assert
        assert restored.logic_flow == original_logic
        assert restored.logic_flow["nodes"][0]["indicator"] == "MA"

    async def test_restore_multiple_times(
        self, instance_service: InstanceService, sample_template, db_session: AsyncSession
    ):
        """Should allow restoring from different snapshots"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test",
            parameters={"ma_short_period": 5}
        )

        snap1 = await instance_service.save_snapshot(strategy.id, "user-123")

        # Modify and create another snapshot
        repo = StrategyInstanceRepository(db_session)
        await repo.update(strategy.id, {"parameters": {"ma_short_period": 10}}, "user-123")
        snap2 = await instance_service.save_snapshot(strategy.id, "user-123")

        # Act - Restore to first snapshot
        restored1 = await instance_service.restore_snapshot(
            strategy_id=strategy.id,
            version_id=snap1.id,
            user_id="user-123"
        )

        # Assert
        assert restored1.parameters["ma_short_period"] == 5

    async def test_restore_unauthorized_strategy(
        self, instance_service: InstanceService, sample_template
    ):
        """Should raise error when user doesn't own strategy"""
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

    async def test_restore_unauthorized_snapshot(
        self, instance_service: InstanceService, sample_template
    ):
        """Should raise error when user doesn't own snapshot"""
        # Arrange
        strategy1 = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Strategy 1"
        )
        snapshot1 = await instance_service.save_snapshot(strategy1.id, "user-123")

        # Create strategy by different user
        strategy2 = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-456",
            name="Strategy 2"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="access denied"):
            await instance_service.restore_snapshot(
                strategy_id=strategy2.id,
                version_id=snapshot1.id,
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

    async def test_restore_mismatched_snapshot(
        self, instance_service: InstanceService, sample_template
    ):
        """Should raise error when snapshot doesn't belong to strategy"""
        # Arrange
        strategy1 = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Strategy 1"
        )
        snapshot1 = await instance_service.save_snapshot(strategy1.id, "user-123")

        strategy2 = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Strategy 2"
        )

        # Act & Assert
        with pytest.raises(ValueError, match="does not belong to strategy"):
            await instance_service.restore_snapshot(
                strategy_id=strategy2.id,
                version_id=snapshot1.id,
                user_id="user-123"
            )


class TestGetVersions:
    """Test get_versions method - AAA Pattern"""

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
        assert snap1.id in [v.id for v in versions]
        assert snap2.id in [v.id for v in versions]
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
        assert isinstance(versions, list)

    async def test_get_versions_many(
        self, instance_service: InstanceService, sample_template
    ):
        """Should return multiple snapshots"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test"
        )

        # Create 5 snapshots
        snapshots = []
        for _ in range(5):
            snap = await instance_service.save_snapshot(strategy.id, "user-123")
            snapshots.append(snap)

        # Act
        versions = await instance_service.get_versions(strategy.id, "user-123")

        # Assert
        assert len(versions) == 5

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

    async def test_get_versions_nonexistent_strategy(
        self, instance_service: InstanceService
    ):
        """Should raise error for non-existent strategy"""
        # Act & Assert
        with pytest.raises(ValueError, match="access denied"):
            await instance_service.get_versions("non-existent", "user-123")

    async def test_versions_sorted_by_created_at(
        self, instance_service: InstanceService, sample_template
    ):
        """Should return versions sorted by creation time descending (newest first)"""
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

        # Assert - Most recent first (descending order by created_at)
        assert versions[0].id == snap3.id
        assert versions[1].id == snap2.id
        assert versions[2].id == snap1.id

    async def test_version_attributes(
        self, instance_service: InstanceService, sample_template
    ):
        """Should have correct version attributes"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test"
        )

        # Act
        snapshot = await instance_service.save_snapshot(strategy.id, "user-123")
        versions = await instance_service.get_versions(strategy.id, "user-123")

        # Assert
        assert len(versions) == 1
        version = versions[0]
        assert version.version == 2
        assert version.parent_version_id == strategy.id
        assert version.user_id == "user-123"
        assert version.id == snapshot.id


class TestIntegrationScenarios:
    """Integration tests for complex scenarios - AAA Pattern"""

    async def test_complete_lifecycle(
        self, instance_service: InstanceService, sample_template, db_session: AsyncSession
    ):
        """Should handle complete strategy lifecycle"""
        # Arrange & Act - Create
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Lifecycle Test",
            parameters={"ma_short_period": 5}
        )

        assert strategy.version == 1
        assert strategy.status == StrategyStatus.DRAFT

        # Save snapshot
        snapshot1 = await instance_service.save_snapshot(strategy.id, "user-123")
        assert snapshot1.version == 2

        # Duplicate
        duplicate = await instance_service.duplicate_strategy(
            strategy_id=strategy.id,
            user_id="user-123",
            new_name="Duplicate Strategy"
        )
        assert duplicate.id != strategy.id
        assert duplicate.version == 1

        # Get versions
        versions = await instance_service.get_versions(strategy.id, "user-123")
        assert len(versions) == 1

        # Assert
        assert strategy.id != duplicate.id
        assert snapshot1.parent_version_id == strategy.id

    async def test_multiple_users_isolation(
        self, instance_service: InstanceService, sample_template
    ):
        """Should isolate strategies between different users"""
        # Arrange
        user1_strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="User 1 Strategy"
        )

        user2_strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-456",
            name="User 2 Strategy"
        )

        # Act
        user1_versions = await instance_service.get_versions(user1_strategy.id, "user-123")

        # Assert - User 2 should not be able to access User 1's versions
        with pytest.raises(ValueError, match="access denied"):
            await instance_service.get_versions(user1_strategy.id, "user-456")

        assert len(user1_versions) == 0

    async def test_snapshot_restore_workflow(
        self, instance_service: InstanceService, sample_template, db_session: AsyncSession
    ):
        """Should handle snapshot save and restore workflow"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test",
            parameters={"ma_short_period": 5, "ma_long_period": 20}
        )

        # Save snapshot before modification
        snapshot = await instance_service.save_snapshot(strategy.id, "user-123")

        # Modify parameters
        repo = StrategyInstanceRepository(db_session)
        await repo.update(
            strategy.id,
            {"parameters": {"ma_short_period": 15, "ma_long_period": 40}},
            "user-123"
        )

        # Act - Restore from snapshot
        restored = await instance_service.restore_snapshot(
            strategy_id=strategy.id,
            version_id=snapshot.id,
            user_id="user-123"
        )

        # Assert
        assert restored.parameters["ma_short_period"] == 5
        assert restored.parameters["ma_long_period"] == 20

    async def test_version_limit_enforcement(
        self, instance_service: InstanceService, sample_template, db_session: AsyncSession
    ):
        """Should enforce maximum version limit"""
        # Arrange
        strategy = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Test"
        )

        # Act - Create more than MAX_VERSIONS snapshots
        for i in range(7):
            await instance_service.save_snapshot(strategy.id, "user-123")

        # Assert
        versions = await instance_service.get_versions(strategy.id, "user-123")
        assert len(versions) == instance_service.MAX_VERSIONS

    async def test_create_from_different_templates(
        self, instance_service: InstanceService, sample_template, complex_template
    ):
        """Should create instances from different templates independently"""
        # Arrange & Act
        instance1 = await instance_service.create_from_template(
            template_id="test-template-1",
            user_id="user-123",
            name="Instance from Template 1"
        )

        instance2 = await instance_service.create_from_template(
            template_id="test-template-2",
            user_id="user-123",
            name="Instance from Template 2"
        )

        # Assert
        assert instance1.template_id == "test-template-1"
        assert instance2.template_id == "test-template-2"
        assert instance1.id != instance2.id
        assert "ma_short_period" in instance1.parameters
        assert "rsi_period" in instance2.parameters

    async def test_custom_strategy_snapshot_workflow(
        self, instance_service: InstanceService
    ):
        """Should handle snapshot workflow for custom strategies"""
        # Arrange
        strategy = await instance_service.create_custom(
            user_id="user-123",
            name="Custom Strategy",
            logic_flow={"nodes": [{"id": "n1"}], "edges": []},
            parameters={"custom_param": 10}
        )

        # Act
        snapshot = await instance_service.save_snapshot(strategy.id, "user-123")
        versions = await instance_service.get_versions(strategy.id, "user-123")

        # Assert
        assert len(versions) == 1
        assert snapshot.template_id is None
        assert snapshot.parameters["custom_param"] == 10
