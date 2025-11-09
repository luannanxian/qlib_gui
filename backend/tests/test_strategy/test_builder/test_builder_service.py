"""
BuilderService Test Suite

TDD implementation for Strategy Builder core service layer.
Tests cover:
1. Node Template management (9 tests)
2. Logic Flow validation (3 tests)
3. Indicator integration (2 tests)
4. Session management (7 tests)

Total: 21 comprehensive tests
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy_builder import (
    NodeTemplate,
    BuilderSession,
    NodeTypeCategory,
    SessionType
)
from app.database.repositories.node_template_repository import NodeTemplateRepository
from app.database.repositories.builder_session_repository import BuilderSessionRepository
from app.modules.strategy.services.builder_service import BuilderService
from app.modules.strategy.exceptions import (
    ResourceNotFoundError,
    AuthorizationError,
    ValidationError,
    LogicFlowError
)


# ==================== Node Template Management Tests ====================

@pytest.mark.asyncio
async def test_get_node_templates_all(builder_service: BuilderService, sample_indicator_template):
    """Test: Get all node templates without filters"""
    templates, total = await builder_service.get_node_templates()

    assert total >= 1
    assert len(templates) >= 1
    assert any(t.id == sample_indicator_template.id for t in templates)


@pytest.mark.asyncio
async def test_get_node_templates_by_type(
    builder_service: BuilderService,
    sample_indicator_template,
    sample_condition_template
):
    """Test: Filter node templates by type"""
    templates, total = await builder_service.get_node_templates(
        node_type=NodeTypeCategory.INDICATOR
    )

    assert all(t.node_type == NodeTypeCategory.INDICATOR.value for t in templates)
    assert any(t.id == sample_indicator_template.id for t in templates)


@pytest.mark.asyncio
async def test_get_node_templates_by_category(
    builder_service: BuilderService,
    sample_indicator_template
):
    """Test: Filter node templates by category"""
    templates, total = await builder_service.get_node_templates(
        category="TREND"
    )

    assert all(t.category == "TREND" for t in templates)
    assert any(t.id == sample_indicator_template.id for t in templates)


@pytest.mark.asyncio
async def test_get_node_templates_system_only(
    builder_service: BuilderService,
    sample_indicator_template
):
    """Test: Get only system templates"""
    templates, total = await builder_service.get_node_templates(
        is_system_template=True
    )

    assert all(t.is_system_template for t in templates)
    assert any(t.id == sample_indicator_template.id for t in templates)


@pytest.mark.asyncio
async def test_create_custom_node_template(
    builder_service: BuilderService,
    sample_custom_template_data: dict
):
    """Test: Create custom node template"""
    template = await builder_service.create_node_template(
        user_id="user-001",
        **sample_custom_template_data
    )

    assert template.id is not None
    assert template.name == sample_custom_template_data["name"]
    assert template.user_id == "user-001"
    assert not template.is_system_template
    assert template.usage_count == 0


@pytest.mark.asyncio
async def test_update_node_template_success(
    builder_service: BuilderService,
    sample_custom_template: NodeTemplate
):
    """Test: Update custom template by owner"""
    update_data = {
        "display_name": "Updated Display Name",
        "description": "Updated description"
    }

    updated = await builder_service.update_node_template(
        template_id=sample_custom_template.id,
        user_id="user-001",
        update_data=update_data
    )

    assert updated.display_name == "Updated Display Name"
    assert updated.description == "Updated description"


@pytest.mark.asyncio
async def test_update_node_template_unauthorized(
    builder_service: BuilderService,
    sample_custom_template: NodeTemplate
):
    """Test: Cannot update template if not owner"""
    update_data = {"display_name": "Hacked"}

    with pytest.raises(AuthorizationError) as exc_info:
        await builder_service.update_node_template(
            template_id=sample_custom_template.id,
            user_id="user-002",  # Different user
            update_data=update_data
        )

    assert "not authorized" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_delete_node_template_success(
    builder_service: BuilderService,
    sample_custom_template: NodeTemplate
):
    """Test: Delete custom template by owner"""
    result = await builder_service.delete_node_template(
        template_id=sample_custom_template.id,
        user_id="user-001"
    )

    assert result is True


@pytest.mark.asyncio
async def test_delete_node_template_system_template(
    builder_service: BuilderService,
    sample_indicator_template: NodeTemplate
):
    """Test: Cannot delete system template"""
    with pytest.raises(AuthorizationError) as exc_info:
        await builder_service.delete_node_template(
            template_id=sample_indicator_template.id,
            user_id="user-001"
        )

    assert "system template" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_increment_template_usage(
    builder_service: BuilderService,
    sample_indicator_template: NodeTemplate,
    db_session: AsyncSession
):
    """Test: Increment template usage count"""
    initial_count = sample_indicator_template.usage_count

    await builder_service.increment_template_usage(
        template_id=sample_indicator_template.id
    )

    # Refresh to get updated value
    await db_session.refresh(sample_indicator_template)
    assert sample_indicator_template.usage_count == initial_count + 1


# ==================== Logic Flow Validation Tests ====================

@pytest.mark.asyncio
async def test_validate_logic_flow_valid(
    builder_service: BuilderService,
    sample_valid_logic_flow: dict
):
    """Test: Validate a valid logic flow"""
    result = await builder_service.validate_logic_flow(sample_valid_logic_flow)

    assert result["is_valid"] is True
    assert len(result["errors"]) == 0
    assert "metadata" in result


@pytest.mark.asyncio
async def test_validate_logic_flow_missing_template(
    builder_service: BuilderService
):
    """Test: Validation fails when node template doesn't exist"""
    logic_flow = {
        "nodes": [
            {
                "id": "node-1",
                "template_id": "non-existent-template-id",
                "type": "INDICATOR"
            }
        ],
        "edges": []
    }

    result = await builder_service.validate_logic_flow(logic_flow)

    assert result["is_valid"] is False
    assert len(result["errors"]) > 0
    assert any("template" in error["message"].lower() for error in result["errors"])


@pytest.mark.asyncio
async def test_detect_circular_dependency(builder_service: BuilderService):
    """Test: Detect circular dependency in node graph"""
    nodes = [
        {"id": "node-1", "type": "INDICATOR"},
        {"id": "node-2", "type": "CONDITION"},
        {"id": "node-3", "type": "SIGNAL"}
    ]

    # Create circular edges: 1 -> 2 -> 3 -> 1
    edges = [
        {"source": "node-1", "target": "node-2"},
        {"source": "node-2", "target": "node-3"},
        {"source": "node-3", "target": "node-1"}  # Creates cycle
    ]

    cycle = await builder_service.detect_circular_dependency(nodes, edges)

    assert cycle is not None
    assert len(cycle) > 0


# ==================== Indicator Integration Tests ====================

@pytest.mark.asyncio
async def test_get_available_factors_all(
    builder_service_with_indicator: BuilderService
):
    """Test: Get all available factors from Indicator module"""
    factors, total = await builder_service_with_indicator.get_available_factors()

    assert total >= 0
    assert isinstance(factors, list)


@pytest.mark.asyncio
async def test_get_available_factors_by_category(
    builder_service_with_indicator: BuilderService
):
    """Test: Get factors filtered by category"""
    factors, total = await builder_service_with_indicator.get_available_factors(
        category="technical"
    )

    assert isinstance(factors, list)
    # Mock should return filtered results
    if len(factors) > 0:
        assert all(f.get("category") == "technical" for f in factors)


# ==================== Session Management Tests ====================

@pytest.mark.asyncio
async def test_create_or_update_session_new(
    builder_service: BuilderService,
    sample_strategy_instance
):
    """Test: Create new session for strategy instance"""
    draft_logic_flow = {"nodes": [], "edges": []}
    draft_parameters = {"param1": "value1"}

    session = await builder_service.create_or_update_session(
        user_id="user-001",
        draft_logic_flow=draft_logic_flow,
        draft_parameters=draft_parameters,
        instance_id=sample_strategy_instance.id
    )

    assert session.id is not None
    assert session.user_id == "user-001"
    assert session.instance_id == sample_strategy_instance.id
    assert session.draft_logic_flow == draft_logic_flow
    assert session.is_active is True


@pytest.mark.asyncio
async def test_create_or_update_session_update(
    builder_service: BuilderService,
    sample_builder_session: BuilderSession
):
    """Test: Update existing session (upsert)"""
    new_logic_flow = {
        "nodes": [{"id": "node-1", "type": "INDICATOR"}],
        "edges": []
    }

    updated_session = await builder_service.create_or_update_session(
        user_id=sample_builder_session.user_id,
        draft_logic_flow=new_logic_flow,
        draft_parameters={},
        instance_id=sample_builder_session.instance_id
    )

    # Should update existing session
    assert updated_session.id == sample_builder_session.id
    assert updated_session.draft_logic_flow == new_logic_flow


@pytest.mark.asyncio
async def test_get_session_by_id_success(
    builder_service: BuilderService,
    sample_builder_session: BuilderSession
):
    """Test: Get session by ID with authorization"""
    session = await builder_service.get_session_by_id(
        session_id=sample_builder_session.id,
        user_id=sample_builder_session.user_id
    )

    assert session.id == sample_builder_session.id


@pytest.mark.asyncio
async def test_get_session_by_id_unauthorized(
    builder_service: BuilderService,
    sample_builder_session: BuilderSession
):
    """Test: Cannot get session if not owner"""
    with pytest.raises(AuthorizationError):
        await builder_service.get_session_by_id(
            session_id=sample_builder_session.id,
            user_id="user-002"  # Different user
        )


@pytest.mark.asyncio
async def test_get_active_session_by_instance(
    builder_service: BuilderService,
    sample_builder_session: BuilderSession
):
    """Test: Get active session for instance"""
    session = await builder_service.get_active_session_by_instance(
        instance_id=sample_builder_session.instance_id,
        user_id=sample_builder_session.user_id
    )

    assert session is not None
    assert session.id == sample_builder_session.id


@pytest.mark.asyncio
async def test_delete_session_success(
    builder_service: BuilderService,
    sample_builder_session: BuilderSession
):
    """Test: Delete session by owner"""
    result = await builder_service.delete_session(
        session_id=sample_builder_session.id,
        user_id=sample_builder_session.user_id
    )

    assert result is True


@pytest.mark.asyncio
async def test_cleanup_expired_sessions(
    builder_service: BuilderService,
    expired_session: BuilderSession
):
    """Test: Cleanup expired sessions"""
    deleted_count = await builder_service.cleanup_expired_sessions(
        expiration_hours=24
    )

    assert deleted_count >= 1


# ==================== Additional Coverage Tests ====================

@pytest.mark.asyncio
async def test_get_node_template_by_id_not_found(builder_service: BuilderService):
    """Test: Get template by ID - not found"""
    with pytest.raises(ResourceNotFoundError):
        await builder_service.get_node_template_by_id(
            template_id="non-existent-id"
        )


@pytest.mark.asyncio
async def test_get_node_template_by_id_unauthorized_custom(
    builder_service: BuilderService,
    sample_custom_template: NodeTemplate
):
    """Test: Get custom template - unauthorized user"""
    with pytest.raises(AuthorizationError):
        await builder_service.get_node_template_by_id(
            template_id=sample_custom_template.id,
            user_id="user-002"  # Different user
        )


@pytest.mark.asyncio
async def test_topological_sort_nodes_valid(builder_service: BuilderService):
    """Test: Topological sort on valid DAG"""
    nodes = [
        {"id": "node-1", "type": "INDICATOR"},
        {"id": "node-2", "type": "CONDITION"},
        {"id": "node-3", "type": "SIGNAL"}
    ]

    edges = [
        {"source": "node-1", "target": "node-2"},
        {"source": "node-2", "target": "node-3"}
    ]

    sorted_nodes = await builder_service.topological_sort_nodes(nodes, edges)

    assert len(sorted_nodes) == 3
    assert sorted_nodes.index("node-1") < sorted_nodes.index("node-2")
    assert sorted_nodes.index("node-2") < sorted_nodes.index("node-3")


@pytest.mark.asyncio
async def test_topological_sort_nodes_with_cycle(builder_service: BuilderService):
    """Test: Topological sort fails on cycle"""
    nodes = [
        {"id": "node-1"},
        {"id": "node-2"},
        {"id": "node-3"}
    ]

    edges = [
        {"source": "node-1", "target": "node-2"},
        {"source": "node-2", "target": "node-3"},
        {"source": "node-3", "target": "node-1"}  # Creates cycle
    ]

    with pytest.raises(LogicFlowError) as exc_info:
        await builder_service.topological_sort_nodes(nodes, edges)

    assert "circular dependency" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_detect_circular_dependency_invalid_edge(builder_service: BuilderService):
    """Test: Detect invalid edge reference"""
    nodes = [{"id": "node-1"}]
    edges = [{"source": "node-1", "target": "non-existent"}]

    with pytest.raises(LogicFlowError) as exc_info:
        await builder_service.detect_circular_dependency(nodes, edges)

    assert "non-existent node" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_node_template_invalid_type(builder_service: BuilderService):
    """Test: Create template with invalid node type"""
    with pytest.raises(ValidationError):
        await builder_service.create_node_template(
            user_id="user-001",
            name="invalid_template",
            display_name="Invalid Template",
            node_type="INVALID_TYPE",  # String instead of NodeTypeCategory
            parameter_schema={},
            default_parameters={},
            input_ports=[],
            output_ports=[]
        )


@pytest.mark.asyncio
async def test_validate_logic_flow_invalid_structure(builder_service: BuilderService):
    """Test: Validate logic flow with invalid structure"""
    with pytest.raises(ValidationError) as exc_info:
        await builder_service.validate_logic_flow({
            "nodes": "invalid",  # Should be a list
            "edges": []
        })

    assert "must be a list" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_delete_session_not_found(builder_service: BuilderService):
    """Test: Delete non-existent session"""
    with pytest.raises(ResourceNotFoundError):
        await builder_service.delete_session(
            session_id="non-existent-id",
            user_id="user-001"
        )


@pytest.mark.asyncio
async def test_update_template_not_found(builder_service: BuilderService):
    """Test: Update non-existent template"""
    with pytest.raises(ResourceNotFoundError):
        await builder_service.update_node_template(
            template_id="non-existent-id",
            user_id="user-001",
            update_data={"display_name": "Updated"}
        )


@pytest.mark.asyncio
async def test_delete_template_not_found(builder_service: BuilderService):
    """Test: Delete non-existent template"""
    with pytest.raises(ResourceNotFoundError):
        await builder_service.delete_node_template(
            template_id="non-existent-id",
            user_id="user-001"
        )
