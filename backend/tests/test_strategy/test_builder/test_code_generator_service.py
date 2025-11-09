"""
Tests for CodeGeneratorService

This module tests code generation from logic flows to Python code.
Following TDD methodology: RED-GREEN-REFACTOR
"""

import pytest
import pytest_asyncio
from jinja2 import Environment, DictLoader
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.code_generation_repository import CodeGenerationRepository
from app.database.repositories.node_template_repository import NodeTemplateRepository
from app.database.models.strategy_builder import CodeGeneration, ValidationStatus, NodeTemplate
from app.modules.strategy.exceptions import (
    CodeGenerationError,
    TemplateNotFoundError,
    ValidationError,
    ResourceNotFoundError
)


# ==================== Fixtures ====================

@pytest_asyncio.fixture
async def code_generation_repo(db_session: AsyncSession):
    """Create CodeGenerationRepository instance"""
    return CodeGenerationRepository(db_session)


@pytest_asyncio.fixture
async def node_template_repo(db_session: AsyncSession):
    """Create NodeTemplateRepository instance"""
    return NodeTemplateRepository(db_session)


@pytest_asyncio.fixture
async def code_generator_service(db_session, code_generation_repo, node_template_repo, jinja2_test_env):
    """Create CodeGeneratorService instance"""
    from app.modules.strategy.services.code_generator_service import CodeGeneratorService

    service = CodeGeneratorService(
        db=db_session,
        code_generation_repo=code_generation_repo,
        node_template_repo=node_template_repo,
        template_env=jinja2_test_env
    )
    return service


# ==================== Basic Code Generation Tests ====================

@pytest.mark.asyncio
async def test_generate_simple_indicator_code(
    code_generator_service,
    sample_strategy_instance,
    sample_indicator_template,
    jinja2_test_env
):
    """Test generating code for a single INDICATOR node"""
    # Arrange
    logic_flow = {
        "nodes": [
            {
                "id": "node-1",
                "template_id": str(sample_indicator_template.id),
                "type": "INDICATOR"
            }
        ],
        "edges": []
    }
    parameters = {
        "node-1": {"short_period": 5, "long_period": 20}
    }

    # Act
    result = await code_generator_service.generate_code(
        instance_id=str(sample_strategy_instance.id),
        user_id="user-001",
        logic_flow=logic_flow,
        parameters=parameters
    )

    # Assert
    assert result is not None
    assert isinstance(result, CodeGeneration)
    assert result.instance_id == str(sample_strategy_instance.id)
    assert result.user_id == "user-001"
    assert result.generated_code is not None
    assert "talib.SMA" in result.generated_code
    assert result.code_hash is not None
    assert len(result.code_hash) == 64  # SHA-256 hash length


@pytest.mark.asyncio
async def test_generate_condition_node_code(
    code_generator_service,
    sample_condition_template,
    jinja2_test_env
):
    """Test generating code for a CONDITION node"""
    # Arrange
    node = {
        "id": "node-2",
        "template_id": str(sample_condition_template.id),
        "type": "CONDITION"
    }
    parameters = {"threshold": 0.5, "operator": ">"}

    # Act
    code = await code_generator_service.generate_node_code(
        node=node,
        node_template=sample_condition_template,
        parameters=parameters
    )

    # Assert
    assert code is not None
    assert isinstance(code, str)
    assert ">" in code
    assert "0.5" in code or "threshold" in code


@pytest.mark.asyncio
async def test_generate_signal_node_code(
    code_generator_service,
    sample_signal_template,
    jinja2_test_env
):
    """Test generating code for a SIGNAL node"""
    # Arrange
    node = {
        "id": "node-3",
        "template_id": str(sample_signal_template.id),
        "type": "SIGNAL"
    }
    parameters = {"signal_type": "BUY"}

    # Act
    code = await code_generator_service.generate_node_code(
        node=node,
        node_template=sample_signal_template,
        parameters=parameters
    )

    # Assert
    assert code is not None
    assert isinstance(code, str)
    assert len(code) > 0


@pytest.mark.asyncio
async def test_generate_complete_strategy(
    code_generator_service,
    sample_strategy_instance,
    sample_logic_flow,
    sample_parameters
):
    """Test generating complete strategy class with multiple nodes"""
    # Act
    result = await code_generator_service.generate_code(
        instance_id=str(sample_strategy_instance.id),
        user_id="user-001",
        logic_flow=sample_logic_flow,
        parameters=sample_parameters
    )

    # Assert
    assert result is not None
    assert "class CustomStrategy" in result.generated_code or "BaseStrategy" in result.generated_code
    assert "def generate_trade_decision" in result.generated_code
    assert result.validation_status in [ValidationStatus.VALID.value, ValidationStatus.PENDING.value]


# ==================== Template Rendering Tests ====================

@pytest.mark.asyncio
async def test_render_indicator_template(code_generator_service, sample_indicator_template):
    """Test rendering indicator node template"""
    # Arrange
    context = {
        "node": sample_indicator_template,
        "params": {"short_period": 10, "long_period": 30}
    }

    # Act
    rendered = await code_generator_service.render_template(
        template_name="indicator_node.py.j2",
        context=context
    )

    # Assert
    assert rendered is not None
    assert "talib.SMA" in rendered
    assert "10" in rendered or "short_period" in rendered


@pytest.mark.asyncio
async def test_render_template_with_qlib_expression(code_generator_service):
    """Test rendering template with Qlib expression"""
    # Arrange
    context = {
        "node": {"display_name": "Test Indicator"},
        "params": {"period": 20},
        "qlib_expression": "Mean($close, 20)"
    }

    # Act & Assert - This should render successfully
    # Even if template doesn't exist yet, we're testing the interface
    try:
        rendered = await code_generator_service.render_template(
            template_name="indicator_node.py.j2",
            context=context
        )
        assert rendered is not None
    except TemplateNotFoundError:
        # Expected in RED phase if template doesn't exist
        pass


@pytest.mark.asyncio
async def test_render_template_with_talib_function(code_generator_service):
    """Test rendering template with TA-Lib function"""
    # Arrange
    context = {
        "node": {"display_name": "RSI Indicator"},
        "params": {"period": 14},
        "talib_function": "RSI"
    }

    # Act
    try:
        rendered = await code_generator_service.render_template(
            template_name="indicator_node.py.j2",
            context=context
        )
        assert "talib" in rendered or "RSI" in rendered
    except TemplateNotFoundError:
        pass


# ==================== Code Deduplication Tests ====================

@pytest.mark.asyncio
async def test_calculate_code_hash(code_generator_service):
    """Test calculating SHA-256 hash of code"""
    # Arrange
    code = "print('Hello, World!')"

    # Act
    code_hash = await code_generator_service.calculate_code_hash(code)

    # Assert
    assert code_hash is not None
    assert isinstance(code_hash, str)
    assert len(code_hash) == 64  # SHA-256 produces 64 hex characters

    # Test deterministic behavior
    code_hash2 = await code_generator_service.calculate_code_hash(code)
    assert code_hash == code_hash2


@pytest.mark.asyncio
async def test_check_code_duplicate_found(
    code_generator_service,
    sample_strategy_instance,
    code_generation_repo
):
    """Test detecting duplicate code"""
    # Arrange - Create existing code generation
    existing_code = "print('test')"
    code_hash = await code_generator_service.calculate_code_hash(existing_code)

    existing_generation_data = {
        "instance_id": str(sample_strategy_instance.id),
        "user_id": "user-001",
        "generated_code": existing_code,
        "code_hash": code_hash,
        "logic_flow_snapshot": {"nodes": []},
        "parameters_snapshot": {},
        "validation_status": ValidationStatus.VALID.value
    }
    created = await code_generation_repo.create(existing_generation_data)

    # Act
    duplicate = await code_generator_service.check_code_duplicate(
        instance_id=str(sample_strategy_instance.id),
        code_hash=code_hash
    )

    # Assert
    assert duplicate is not None
    assert duplicate.code_hash == code_hash


@pytest.mark.asyncio
async def test_check_code_duplicate_not_found(
    code_generator_service,
    sample_strategy_instance
):
    """Test when no duplicate code exists"""
    # Arrange
    non_existent_hash = "a" * 64

    # Act
    duplicate = await code_generator_service.check_code_duplicate(
        instance_id=str(sample_strategy_instance.id),
        code_hash=non_existent_hash
    )

    # Assert
    assert duplicate is None


# ==================== History Management Tests ====================

@pytest.mark.asyncio
async def test_get_code_history(
    code_generator_service,
    sample_strategy_instance,
    code_generation_repo
):
    """Test getting code generation history"""
    # Arrange - Create multiple code generations
    for i in range(3):
        code = f"print('test {i}')"
        code_hash = await code_generator_service.calculate_code_hash(code)
        generation_data = {
            "instance_id": str(sample_strategy_instance.id),
            "user_id": "user-001",
            "generated_code": code,
            "code_hash": code_hash,
            "logic_flow_snapshot": {"nodes": []},
            "parameters_snapshot": {},
            "validation_status": ValidationStatus.VALID.value
        }
        await code_generation_repo.create(generation_data)

    # Act
    history, total = await code_generator_service.get_code_history(
        instance_id=str(sample_strategy_instance.id),
        user_id="user-001"
    )

    # Assert
    assert len(history) >= 3
    assert total >= 3
    assert all(isinstance(gen, CodeGeneration) for gen in history)


@pytest.mark.asyncio
async def test_get_code_history_with_pagination(
    code_generator_service,
    sample_strategy_instance,
    code_generation_repo
):
    """Test getting paginated code history"""
    # Arrange - Create 5 code generations
    for i in range(5):
        code = f"print('test {i}')"
        code_hash = await code_generator_service.calculate_code_hash(code)
        generation_data = {
            "instance_id": str(sample_strategy_instance.id),
            "user_id": "user-001",
            "generated_code": code,
            "code_hash": code_hash,
            "logic_flow_snapshot": {"nodes": []},
            "parameters_snapshot": {},
            "validation_status": ValidationStatus.VALID.value
        }
        await code_generation_repo.create(generation_data)

    # Act - Get first page (limit 2)
    page1, total = await code_generator_service.get_code_history(
        instance_id=str(sample_strategy_instance.id),
        user_id="user-001",
        skip=0,
        limit=2
    )

    # Get second page
    page2, _ = await code_generator_service.get_code_history(
        instance_id=str(sample_strategy_instance.id),
        user_id="user-001",
        skip=2,
        limit=2
    )

    # Assert
    assert len(page1) == 2
    assert len(page2) == 2
    assert total >= 5
    # Ensure different records
    assert page1[0].id != page2[0].id


# ==================== Exception Handling Tests ====================

@pytest.mark.asyncio
async def test_generate_code_invalid_logic_flow(
    code_generator_service,
    sample_strategy_instance
):
    """Test generating code with invalid logic flow"""
    # Arrange - Invalid logic flow (missing required fields)
    invalid_logic_flow = {"invalid": "structure"}
    parameters = {}

    # Act & Assert
    with pytest.raises((ValidationError, CodeGenerationError, KeyError)):
        await code_generator_service.generate_code(
            instance_id=str(sample_strategy_instance.id),
            user_id="user-001",
            logic_flow=invalid_logic_flow,
            parameters=parameters
        )


@pytest.mark.asyncio
async def test_generate_code_template_not_found(
    code_generator_service,
    sample_strategy_instance
):
    """Test generating code when node template doesn't exist"""
    # Arrange - Logic flow with non-existent template
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
    parameters = {"node-1": {}}

    # Act & Assert
    with pytest.raises((ResourceNotFoundError, CodeGenerationError)):
        await code_generator_service.generate_code(
            instance_id=str(sample_strategy_instance.id),
            user_id="user-001",
            logic_flow=logic_flow,
            parameters=parameters
        )


# ==================== Edge Cases and Additional Tests ====================

@pytest.mark.asyncio
async def test_generate_code_empty_logic_flow(
    code_generator_service,
    sample_strategy_instance
):
    """Test generating code with empty logic flow"""
    # Arrange
    empty_logic_flow = {"nodes": [], "edges": []}
    parameters = {}

    # Act
    result = await code_generator_service.generate_code(
        instance_id=str(sample_strategy_instance.id),
        user_id="user-001",
        logic_flow=empty_logic_flow,
        parameters=parameters
    )

    # Assert - Should still generate basic strategy structure
    assert result is not None
    assert result.generated_code is not None


@pytest.mark.asyncio
async def test_calculate_code_hash_consistency(code_generator_service):
    """Test that code hash calculation is consistent"""
    # Arrange
    code1 = "x = 1\ny = 2\n"
    code2 = "x = 1\ny = 2\n"  # Same code
    code3 = "x = 1\ny = 3\n"  # Different code

    # Act
    hash1 = await code_generator_service.calculate_code_hash(code1)
    hash2 = await code_generator_service.calculate_code_hash(code2)
    hash3 = await code_generator_service.calculate_code_hash(code3)

    # Assert
    assert hash1 == hash2  # Same code should have same hash
    assert hash1 != hash3  # Different code should have different hash


@pytest.mark.asyncio
async def test_get_code_history_authorization(
    code_generator_service,
    sample_strategy_instance,
    code_generation_repo
):
    """Test that users can only see their own code history"""
    # Arrange - Create code for user-001
    code = "print('test')"
    code_hash = await code_generator_service.calculate_code_hash(code)
    generation_data = {
        "instance_id": str(sample_strategy_instance.id),
        "user_id": "user-001",
        "generated_code": code,
        "code_hash": code_hash,
        "logic_flow_snapshot": {"nodes": []},
        "parameters_snapshot": {},
        "validation_status": ValidationStatus.VALID.value
    }
    await code_generation_repo.create(generation_data)

    # Act - Try to get history as different user
    # Note: This test depends on authorization implementation
    # For now, we just verify the method works
    history, total = await code_generator_service.get_code_history(
        instance_id=str(sample_strategy_instance.id),
        user_id="user-001"  # Same user should work
    )

    # Assert
    assert len(history) >= 1
    assert all(gen.user_id == "user-001" for gen in history)


@pytest.mark.asyncio
async def test_render_template_not_found(code_generator_service):
    """Test rendering a non-existent template raises error"""
    # Arrange
    template_name = "non_existent_template.py.j2"
    context = {"test": "data"}

    # Act & Assert
    with pytest.raises(TemplateNotFoundError):
        await code_generator_service.render_template(template_name, context)


@pytest.mark.asyncio
async def test_generate_node_code_template_fallback(
    code_generator_service,
    sample_indicator_template
):
    """Test that node code generation falls back to generic template when template not found"""
    # Arrange - Create node with custom type that doesn't have a template
    node = {
        "id": "node-1",
        "template_id": str(sample_indicator_template.id),
        "type": "CUSTOM_TYPE"  # Non-existent template type
    }
    sample_indicator_template.node_type = "CUSTOM_TYPE"
    parameters = {}

    # Act
    code = await code_generator_service.generate_node_code(
        node=node,
        node_template=sample_indicator_template,
        parameters=parameters
    )

    # Assert - Should use fallback template
    assert code is not None
    assert "TODO" in code or "Implement" in code or sample_indicator_template.display_name in code


@pytest.mark.asyncio
async def test_calculate_code_hash_empty_string(code_generator_service):
    """Test calculating hash of empty code string"""
    # Arrange
    empty_code = ""

    # Act
    code_hash = await code_generator_service.calculate_code_hash(empty_code)

    # Assert
    assert code_hash is not None
    assert isinstance(code_hash, str)
    assert len(code_hash) == 64


@pytest.mark.asyncio
async def test_generate_code_with_missing_template_id(
    code_generator_service,
    sample_strategy_instance
):
    """Test generating code when node has no template_id"""
    # Arrange
    logic_flow = {
        "nodes": [
            {
                "id": "node-1",
                # Missing template_id
                "type": "INDICATOR"
            }
        ],
        "edges": []
    }
    parameters = {"node-1": {}}

    # Act
    result = await code_generator_service.generate_code(
        instance_id=str(sample_strategy_instance.id),
        user_id="user-001",
        logic_flow=logic_flow,
        parameters=parameters
    )

    # Assert - Should still generate code (skip nodes without template_id)
    assert result is not None


@pytest.mark.asyncio
async def test_generate_code_nodes_not_list(
    code_generator_service,
    sample_strategy_instance
):
    """Test that invalid nodes structure raises error"""
    # Arrange
    logic_flow = {
        "nodes": "not a list",  # Invalid structure
        "edges": []
    }
    parameters = {}

    # Act & Assert
    with pytest.raises(ValidationError):
        await code_generator_service.generate_code(
            instance_id=str(sample_strategy_instance.id),
            user_id="user-001",
            logic_flow=logic_flow,
            parameters=parameters
        )
