"""
Strategy Builder API Endpoints

Provides REST API endpoints for visual strategy building with drag-and-drop interface.

This module exposes endpoints for:
- Node Template management (list, create, update, delete)
- Code generation from logic flows
- Quick backtest execution
- Session management with auto-save
- Factor integration from Indicator module

Architecture:
    builder_api → BuilderService/CodeGeneratorService/ValidationService → Repository Layer

Endpoints:
- GET    /api/v1/strategy-builder/templates - List node templates
- POST   /api/v1/strategy-builder/templates - Create custom template
- GET    /api/v1/strategy-builder/templates/{id} - Get template details
- PUT    /api/v1/strategy-builder/templates/{id} - Update template
- DELETE /api/v1/strategy-builder/templates/{id} - Delete template (soft delete)
- GET    /api/v1/strategy-builder/available-factors - Get available factors
- POST   /api/v1/strategy-builder/generate-code - Generate code from logic flow
- POST   /api/v1/strategy-builder/validate-code - Validate code security
- GET    /api/v1/strategy-builder/code-history/{instance_id} - Get code history
- POST   /api/v1/strategy-builder/quick-test - Execute quick test
- GET    /api/v1/strategy-builder/quick-test/{test_id} - Get test result
- GET    /api/v1/strategy-builder/quick-test/history - Get test history
- POST   /api/v1/strategy-builder/sessions - Create/update session
- GET    /api/v1/strategy-builder/sessions/{session_id} - Get session
- DELETE /api/v1/strategy-builder/sessions/{session_id} - Delete session

Author: Qlib-UI Strategy Builder Team
Version: 1.0.0
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import get_db
from app.database.repositories.node_template_repository import NodeTemplateRepository
from app.database.repositories.code_generation_repository import CodeGenerationRepository
from app.database.repositories.quick_test_repository import QuickTestRepository
from app.database.repositories.builder_session_repository import BuilderSessionRepository
from app.modules.strategy.services.builder_service import BuilderService
from app.modules.strategy.services.code_generator_service import CodeGeneratorService
from app.modules.strategy.services.builder_validation_service import ValidationService
from app.modules.strategy.exceptions import (
    ResourceNotFoundError,
    AuthorizationError,
    ValidationError,
    LogicFlowError
)
from app.modules.strategy.schemas.builder import (
    # Node Templates
    NodeTemplateCreate,
    NodeTemplateUpdate,
    NodeTemplateResponse,
    NodeTemplateListResponse,
    NodeTypeCategory,
    # Factors
    FactorListResponse,
    # Code Generation
    CodeGenerationRequest,
    CodeValidationRequest,
    CodeGenerationResponse,
    CodeValidationResponse,
    CodeHistoryResponse,
    # Quick Test
    QuickTestRequest,
    QuickTestResponse,
    QuickTestHistoryResponse,
    QuickTestStatus,
    # Sessions
    SessionUpsertRequest,
    SessionResponse,
)

# Router configuration
router = APIRouter(
    prefix="/api/v1/strategy-builder",
    tags=["Strategy Builder"]
)

# Mock user ID for authentication (will be replaced with actual auth middleware)
MOCK_USER_ID = "test_user"


# ==================== Dependency Injection ====================

async def get_builder_service(db: AsyncSession = Depends(get_db)) -> BuilderService:
    """
    Dependency for BuilderService.

    Creates service instance with required repositories.
    """
    node_template_repo = NodeTemplateRepository(db)
    session_repo = BuilderSessionRepository(db)
    return BuilderService(db, node_template_repo, session_repo)


async def get_code_generator_service(db: AsyncSession = Depends(get_db)) -> CodeGeneratorService:
    """
    Dependency for CodeGeneratorService.

    Creates service instance with code generation repository.
    """
    code_gen_repo = CodeGenerationRepository(db)
    validation_service = ValidationService(db)
    node_template_repo = NodeTemplateRepository(db)
    return CodeGeneratorService(db, code_gen_repo, validation_service, node_template_repo)


async def get_validation_service(db: AsyncSession = Depends(get_db)) -> ValidationService:
    """
    Dependency for ValidationService.

    Creates service instance for code validation.
    """
    return ValidationService(db)


# ==================== Node Template Endpoints ====================

@router.get(
    "/templates",
    response_model=NodeTemplateListResponse,
    summary="List node templates",
    description="""
    Retrieve node templates with filtering and pagination.

    Returns both system templates and user's custom templates.

    **Filters:**
    - `node_type`: Filter by node type (INDICATOR, CONDITION, SIGNAL, etc.)
    - `category`: Filter by sub-category (TREND, MOMENTUM, etc.)
    - `is_system`: Filter system/custom templates

    **Pagination:**
    - `skip`: Number of records to skip
    - `limit`: Maximum records to return (1-100)
    """
)
async def list_node_templates(
    node_type: Optional[NodeTypeCategory] = Query(None, description="Filter by node type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_system: Optional[bool] = Query(None, alias="is_system_template", description="Filter system/custom templates"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Max results per page"),
    service: BuilderService = Depends(get_builder_service)
):
    """List node templates with filtering and pagination."""
    try:
        logger.info(
            f"Listing node templates: type={node_type}, category={category}, "
            f"is_system={is_system}, skip={skip}, limit={limit}"
        )

        templates, total = await service.get_node_templates(
            node_type=node_type,
            category=category,
            is_system_template=is_system,
            user_id=MOCK_USER_ID,
            skip=skip,
            limit=limit
        )

        return NodeTemplateListResponse(
            items=templates,
            total=total,
            skip=skip,
            limit=limit
        )

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list node templates"
        )


@router.post(
    "/templates",
    response_model=NodeTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create custom node template",
    description="""
    Create a user-defined custom node template.

    Only authenticated users can create custom templates.
    System templates cannot be created via API.

    **Requirements:**
    - Unique template name (snake_case)
    - Valid parameter schema (JSON Schema format)
    - Valid port definitions
    - Default parameters matching schema
    """
)
async def create_node_template(
    template: NodeTemplateCreate,
    service: BuilderService = Depends(get_builder_service)
):
    """Create a new custom node template."""
    try:
        logger.info(f"Creating custom template: {template.name} by user {MOCK_USER_ID}")

        # Convert Pydantic model to dict and pass individual fields
        created_template = await service.create_node_template(
            user_id=MOCK_USER_ID,
            name=template.name,
            display_name=template.display_name,
            node_type=template.node_type,
            parameter_schema=template.parameter_schema,
            default_parameters=template.default_parameters,
            input_ports=[port.model_dump() for port in template.input_ports],
            output_ports=[port.model_dump() for port in template.output_ports],
            description=template.description,
            category=template.category,
            validation_rules=template.validation_rules,
            execution_hints=template.execution_hints,
            icon=template.icon,
            color=template.color
        )

        logger.info(f"Successfully created template: {created_template.id}")
        return created_template

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create node template"
        )


@router.get(
    "/templates/{template_id}",
    response_model=NodeTemplateResponse,
    summary="Get node template details",
    description="""
    Retrieve detailed information about a specific node template.

    Returns full template configuration including:
    - Parameter schema
    - Port definitions
    - Validation rules
    - Execution hints
    """
)
async def get_node_template(
    template_id: str = Path(..., description="Template UUID"),
    service: BuilderService = Depends(get_builder_service)
):
    """Get node template by ID."""
    try:
        logger.info(f"Getting template: {template_id}")

        template = await service.get_node_template_by_id(
            template_id=template_id,
            user_id=MOCK_USER_ID
        )

        return template

    except ResourceNotFoundError as e:
        logger.error(f"Template not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthorizationError as e:
        logger.error(f"Authorization error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve template"
        )


@router.put(
    "/templates/{template_id}",
    response_model=NodeTemplateResponse,
    summary="Update custom node template",
    description="""
    Update a custom node template.

    **Restrictions:**
    - Only the owner can update custom templates
    - System templates cannot be updated
    - Template name cannot be changed

    **Updatable Fields:**
    - display_name, description
    - parameter_schema, default_parameters
    - input_ports, output_ports
    - validation_rules, execution_hints
    - icon, color
    """
)
async def update_node_template(
    template_id: str = Path(..., description="Template UUID"),
    update: NodeTemplateUpdate = ...,
    service: BuilderService = Depends(get_builder_service)
):
    """Update a custom node template."""
    try:
        logger.info(f"Updating template: {template_id} by user {MOCK_USER_ID}")

        # Build update dict from non-None fields
        update_data = update.model_dump(exclude_unset=True)

        # Convert port definitions if present
        if 'input_ports' in update_data and update_data['input_ports']:
            update_data['input_ports'] = [
                port.model_dump() if hasattr(port, 'model_dump') else port
                for port in update_data['input_ports']
            ]
        if 'output_ports' in update_data and update_data['output_ports']:
            update_data['output_ports'] = [
                port.model_dump() if hasattr(port, 'model_dump') else port
                for port in update_data['output_ports']
            ]

        updated_template = await service.update_node_template(
            template_id=template_id,
            user_id=MOCK_USER_ID,
            **update_data
        )

        logger.info(f"Successfully updated template: {template_id}")
        return updated_template

    except ResourceNotFoundError as e:
        logger.error(f"Template not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthorizationError as e:
        logger.error(f"Authorization error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update template"
        )


@router.delete(
    "/templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete custom node template",
    description="""
    Delete a custom node template (soft delete).

    **Restrictions:**
    - Only the owner can delete custom templates
    - System templates cannot be deleted
    - Templates in use may show warning (future enhancement)
    """
)
async def delete_node_template(
    template_id: str = Path(..., description="Template UUID"),
    service: BuilderService = Depends(get_builder_service)
):
    """Delete a custom node template."""
    try:
        logger.info(f"Deleting template: {template_id} by user {MOCK_USER_ID}")

        await service.delete_node_template(
            template_id=template_id,
            user_id=MOCK_USER_ID
        )

        logger.info(f"Successfully deleted template: {template_id}")
        return None

    except ResourceNotFoundError as e:
        logger.error(f"Template not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthorizationError as e:
        logger.error(f"Authorization error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete template"
        )


# ==================== Factor Integration Endpoint ====================

@router.get(
    "/available-factors",
    response_model=FactorListResponse,
    summary="Get available factors",
    description="""
    Retrieve factor list from Indicator module for use in INDICATOR nodes.

    Returns published factors that can be used in strategy logic flows.
    Factors are sourced from:
    - System built-in indicators (talib, qlib)
    - User custom factors
    - Published user library factors
    """
)
async def get_available_factors(
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Max results per page"),
    service: BuilderService = Depends(get_builder_service)
):
    """Get available factors from Indicator module."""
    try:
        logger.info(f"Getting available factors: category={category}, skip={skip}, limit={limit}")

        factors, total = await service.get_available_factors(
            category=category,
            skip=skip,
            limit=limit
        )

        return FactorListResponse(
            items=factors,
            total=total
        )

    except Exception as e:
        logger.error(f"Error getting factors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available factors"
        )


# ==================== Code Generation Endpoints ====================

@router.post(
    "/generate-code",
    response_model=CodeGenerationResponse,
    summary="Generate Python code from logic flow",
    description="""
    Convert visual logic flow JSON to executable Python code.

    **Process:**
    1. Validate logic flow completeness
    2. Topological sort of nodes
    3. Generate code using Jinja2 templates
    4. Perform syntax and security checks
    5. Calculate code hash for deduplication
    6. Store generation history

    **Code Generation Rules:**
    - INDICATOR nodes → Factor expressions
    - CONDITION nodes → Boolean conditions
    - SIGNAL nodes → Trading signals (BUY/SELL)
    - POSITION nodes → Position sizing logic
    - STOP_LOSS/STOP_PROFIT → Risk management rules
    """
)
async def generate_code(
    request: CodeGenerationRequest,
    service: CodeGeneratorService = Depends(get_code_generator_service)
):
    """Generate Python code from logic flow."""
    try:
        logger.info(f"Generating code for instance: {request.instance_id}")

        generation = await service.generate_code(
            instance_id=request.instance_id,
            logic_flow=request.logic_flow.model_dump(),
            parameters=request.parameters
        )

        logger.info(f"Successfully generated code: {generation.id}")

        return CodeGenerationResponse(
            generation_id=generation.id,
            generated_code=generation.generated_code,
            code_hash=generation.code_hash,
            validation_status=generation.validation_status,
            validation_result=generation.validation_result,
            syntax_check_passed=generation.syntax_check_passed,
            security_check_passed=generation.security_check_passed,
            line_count=generation.line_count,
            complexity_score=generation.complexity_score,
            generation_time=generation.generation_time
        )

    except LogicFlowError as e:
        logger.error(f"Logic flow error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "LOGIC_FLOW_INVALID", "message": str(e)}
        )
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate code"
        )


@router.post(
    "/validate-code",
    response_model=CodeValidationResponse,
    summary="Validate code security",
    description="""
    Perform comprehensive security validation on code.

    **Validation Checks:**
    1. **Syntax Validation**: Python AST parsing
    2. **Security Scan**: Detect dangerous imports/calls
    3. **Import Whitelist**: Verify all imports are allowed
    4. **Complexity Analysis**: Calculate cyclomatic complexity
    5. **Resource Estimation**: Estimate memory/CPU requirements

    **Security Rules:**
    - Forbidden: File I/O, network access, subprocess
    - Allowed: numpy, pandas, qlib, talib, math, datetime
    - No dynamic code execution (eval, exec, compile)
    """
)
async def validate_code(
    request: CodeValidationRequest,
    service: ValidationService = Depends(get_validation_service)
):
    """Validate code security and syntax."""
    try:
        logger.info(f"Validating code (strict={request.strict_mode})")

        # Perform syntax validation
        syntax_result = await service.validate_syntax(request.code)

        # Perform security validation
        security_result = await service.validate_security(request.code)

        # Determine overall status
        is_valid = syntax_result['is_valid'] and security_result['is_valid']

        if not is_valid:
            if not syntax_result['is_valid']:
                validation_status = ValidationStatus.SYNTAX_ERROR
            elif not security_result['is_valid']:
                validation_status = ValidationStatus.SECURITY_ERROR
            else:
                validation_status = ValidationStatus.RUNTIME_ERROR
        else:
            validation_status = ValidationStatus.VALID

        # Build response
        from app.modules.strategy.schemas.builder import (
            ValidationChecks,
            SyntaxCheck,
            SecurityCheck,
            ImportCheck,
            ComplexityMetrics
        )

        checks = ValidationChecks(
            syntax=SyntaxCheck(
                passed=syntax_result['is_valid'],
                errors=syntax_result.get('errors', [])
            ),
            security=SecurityCheck(
                passed=security_result['is_valid'],
                violations=security_result.get('violations', [])
            ),
            imports=ImportCheck(
                allowed=security_result.get('allowed_imports', []),
                forbidden=security_result.get('forbidden_imports', [])
            ),
            complexity=ComplexityMetrics(
                cyclomatic_complexity=syntax_result.get('complexity', {}).get('cyclomatic_complexity'),
                cognitive_complexity=syntax_result.get('complexity', {}).get('cognitive_complexity'),
                max_nesting_depth=syntax_result.get('complexity', {}).get('max_nesting_depth')
            )
        )

        return CodeValidationResponse(
            is_valid=is_valid,
            validation_status=validation_status,
            checks=checks
        )

    except Exception as e:
        logger.error(f"Error validating code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate code"
        )


@router.get(
    "/code-history/{instance_id}",
    response_model=CodeHistoryResponse,
    summary="Get code generation history",
    description="""
    Retrieve code generation history for a strategy instance.

    Returns chronological list of all code generations with:
    - Validation status
    - Code hash (for deduplication)
    - Complexity metrics
    - Generation timestamp
    """
)
async def get_code_history(
    instance_id: str = Path(..., description="Strategy instance UUID"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(10, ge=1, le=50, description="Max results per page"),
    service: CodeGeneratorService = Depends(get_code_generator_service)
):
    """Get code generation history for a strategy instance."""
    try:
        logger.info(f"Getting code history for instance: {instance_id}")

        history, total = await service.get_code_history(
            instance_id=instance_id,
            skip=skip,
            limit=limit
        )

        return CodeHistoryResponse(
            items=history,
            total=total
        )

    except ResourceNotFoundError as e:
        logger.error(f"Instance not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting code history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve code history"
        )


# ==================== Quick Test Endpoints ====================

@router.post(
    "/quick-test",
    response_model=QuickTestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Execute quick backtest",
    description="""
    Execute lightweight backtest for rapid strategy validation.

    **Quick Test Features:**
    - Simplified configuration (preset date ranges, stock pools)
    - Fast execution (< 30 seconds for typical cases)
    - Key performance metrics only
    - Asynchronous execution with status polling

    **Execution Flow:**
    1. Create QuickTest record (status=PENDING)
    2. Submit to background task queue
    3. Return test_id immediately
    4. Client polls GET /quick-test/{test_id} for results
    """
)
async def execute_quick_test(
    request: QuickTestRequest,
    db: AsyncSession = Depends(get_db)
):
    """Execute quick backtest for strategy validation."""
    try:
        logger.info(f"Creating quick test for instance: {request.instance_id}")

        # Create QuickTest record
        quick_test_repo = QuickTestRepository(db)

        test_data = {
            "instance_id": request.instance_id,
            "user_id": MOCK_USER_ID,
            "test_name": request.test_name,
            "test_config": request.test_config.model_dump(),
            "status": "PENDING",
        }

        quick_test = await quick_test_repo.create(test_data)
        await db.commit()
        await db.refresh(quick_test)

        # TODO: Submit to background task queue
        # For now, just return pending status

        logger.info(f"Quick test created: {quick_test.id}")

        return quick_test

    except ResourceNotFoundError as e:
        logger.error(f"Instance not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating quick test: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create quick test"
        )


@router.get(
    "/quick-test/{test_id}",
    response_model=QuickTestResponse,
    summary="Get quick test result",
    description="""
    Retrieve quick test execution status and results.

    **Status Lifecycle:**
    PENDING → RUNNING → COMPLETED/FAILED/CANCELLED

    **Result Contents:**
    - Performance metrics (returns, sharpe, max_drawdown, win_rate)
    - Equity curve (simplified)
    - Trade summary (count, win/loss)
    - Execution time and error messages (if failed)
    """
)
async def get_quick_test_result(
    test_id: str = Path(..., description="Quick test UUID"),
    db: AsyncSession = Depends(get_db)
):
    """Get quick test execution status and results."""
    try:
        logger.info(f"Getting quick test result: {test_id}")

        quick_test_repo = QuickTestRepository(db)
        quick_test = await quick_test_repo.get(test_id)

        if not quick_test:
            raise ResourceNotFoundError(f"Quick test not found: {test_id}")

        return quick_test

    except ResourceNotFoundError as e:
        logger.error(f"Test not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting test result: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve test result"
        )


@router.get(
    "/quick-test/history",
    response_model=QuickTestHistoryResponse,
    summary="Get quick test history",
    description="""
    Retrieve historical quick tests for current user or specific strategy instance.

    Returns summary information for all tests including:
    - Test status and configuration
    - Key performance metrics
    - Execution time
    - Creation timestamp
    """
)
async def get_quick_test_history(
    instance_id: Optional[str] = Query(None, description="Filter by instance UUID"),
    status: Optional[QuickTestStatus] = Query(None, description="Filter by test status"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=50, description="Max results per page"),
    db: AsyncSession = Depends(get_db)
):
    """Get quick test history for user or strategy instance."""
    try:
        logger.info(f"Getting test history: instance={instance_id}, status={status}")

        quick_test_repo = QuickTestRepository(db)

        # Build filters
        filters = {"user_id": MOCK_USER_ID}
        if instance_id:
            filters["instance_id"] = instance_id
        if status:
            filters["status"] = status.value

        # Get history
        tests = await quick_test_repo.search(
            filters=filters,
            skip=skip,
            limit=limit
        )

        total = len(tests)  # TODO: Add count query

        return QuickTestHistoryResponse(
            items=tests,
            total=total
        )

    except Exception as e:
        logger.error(f"Error getting test history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve test history"
        )


# ==================== Session Management Endpoints ====================

@router.post(
    "/sessions",
    response_model=SessionResponse,
    summary="Create or update builder session",
    description="""
    Create new session or update existing session with draft logic flow.

    **Session Auto-Save Behavior:**
    - **Create**: If no session exists for instance_id, create new
    - **Update**: If session exists, update draft_logic_flow and last_activity_at
    - Auto-save interval: Client sends every 30 seconds
    - Session expiration: 24 hours of inactivity

    **Use Cases:**
    1. User starts building → Create session
    2. User drags nodes → Auto-save every 30s
    3. User saves strategy → Commit to instance, delete session
    4. User closes browser → Session persists for 24h
    5. User re-opens → Restore from session
    """
)
async def create_or_update_session(
    request: SessionUpsertRequest,
    service: BuilderService = Depends(get_builder_service)
):
    """Create or update builder session."""
    try:
        logger.info(f"Creating/updating session for instance: {request.instance_id}")

        session = await service.create_or_update_session(
            user_id=MOCK_USER_ID,
            instance_id=request.instance_id,
            session_type=request.session_type,
            session_name=request.session_name,
            draft_logic_flow=request.draft_logic_flow,
            draft_parameters=request.draft_parameters,
            draft_metadata=request.draft_metadata
        )

        logger.info(f"Session saved: {session.id}")
        return session

    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error saving session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save session"
        )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Get builder session",
    description="""
    Retrieve builder session with draft logic flow and parameters.

    Used for restoring user's work when re-opening strategy builder.
    Returns complete session state including:
    - Draft logic flow
    - Draft parameters
    - UI metadata (viewport, cursor position)
    """
)
async def get_session(
    session_id: str = Path(..., description="Session UUID"),
    service: BuilderService = Depends(get_builder_service)
):
    """Get builder session by ID."""
    try:
        logger.info(f"Getting session: {session_id}")

        session = await service.get_session_by_id(
            session_id=session_id,
            user_id=MOCK_USER_ID
        )

        return session

    except ResourceNotFoundError as e:
        logger.error(f"Session not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthorizationError as e:
        logger.error(f"Authorization error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session"
        )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete builder session",
    description="""
    Delete builder session (soft delete).

    Called when:
    - User commits strategy to StrategyInstance
    - User explicitly discards draft
    - Session expires (automatic cleanup)
    """
)
async def delete_session(
    session_id: str = Path(..., description="Session UUID"),
    service: BuilderService = Depends(get_builder_service)
):
    """Delete builder session."""
    try:
        logger.info(f"Deleting session: {session_id}")

        await service.delete_session(
            session_id=session_id,
            user_id=MOCK_USER_ID
        )

        logger.info(f"Session deleted: {session_id}")
        return None

    except ResourceNotFoundError as e:
        logger.error(f"Session not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthorizationError as e:
        logger.error(f"Authorization error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete session"
        )
