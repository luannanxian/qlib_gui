"""
Strategy Builder Service Layer Interface Definitions

This module defines the complete service layer interfaces for Strategy Builder functionality.
All services follow async/await patterns and use dependency injection for repositories.

Architecture Pattern:
- Service classes handle business logic
- Repository classes handle data access
- Exceptions propagate to API layer for HTTP response mapping
- All methods are async and type-annotated
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

# Database models
from app.database.models.strategy_builder import (
    NodeTemplate,
    QuickTest,
    CodeGeneration,
    BuilderSession,
    NodeTypeCategory,
    QuickTestStatus,
    ValidationStatus,
    SessionType
)
from app.database.models.strategy import StrategyInstance

# Repositories
from app.database.repositories.base import BaseRepository


# ==================== Custom Exceptions ====================

class BuilderServiceError(Exception):
    """Base exception for Strategy Builder services"""
    pass


class ValidationError(BuilderServiceError):
    """Raised when validation fails"""
    pass


class ResourceNotFoundError(BuilderServiceError):
    """Raised when resource is not found"""
    pass


class AuthorizationError(BuilderServiceError):
    """Raised when user is not authorized"""
    pass


class LogicFlowError(BuilderServiceError):
    """Raised when logic flow is invalid"""
    pass


class CodeGenerationError(BuilderServiceError):
    """Raised when code generation fails"""
    pass


class QuickTestError(BuilderServiceError):
    """Raised when quick test execution fails"""
    pass


# ==================== Service Interfaces ====================

class BuilderService:
    """
    Core builder service for node templates, logic flow validation, and session management.

    Responsibilities:
    - Node template CRUD operations
    - Logic flow validation (circular dependency, type checking)
    - Integration with Indicator module for factor listing
    - Session auto-save and expiration cleanup
    """

    def __init__(
        self,
        db: AsyncSession,
        node_template_repo: "NodeTemplateRepository",
        session_repo: "BuilderSessionRepository",
        indicator_service: Optional[Any] = None  # IndicatorService from indicator module
    ):
        """
        Initialize builder service with dependencies.

        Args:
            db: Database session
            node_template_repo: Repository for node templates
            session_repo: Repository for builder sessions
            indicator_service: Optional indicator service for factor integration
        """
        self.db = db
        self.node_template_repo = node_template_repo
        self.session_repo = session_repo
        self.indicator_service = indicator_service

    # ==================== Node Template Operations ====================

    async def get_node_templates(
        self,
        node_type: Optional[NodeTypeCategory] = None,
        category: Optional[str] = None,
        is_system_template: Optional[bool] = None,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[NodeTemplate], int]:
        """
        Get node templates with filtering and pagination.

        Args:
            node_type: Filter by node type (INDICATOR, CONDITION, etc.)
            category: Filter by sub-category (TREND, MOMENTUM, etc.)
            is_system_template: Filter by system/custom templates
            user_id: User ID to include user's custom templates
            skip: Pagination offset
            limit: Max records to return

        Returns:
            Tuple of (template list, total count)

        Raises:
            ValidationError: If invalid filter parameters
        """
        pass

    async def get_node_template_by_id(
        self,
        template_id: str,
        user_id: Optional[str] = None
    ) -> NodeTemplate:
        """
        Get node template by ID.

        Args:
            template_id: Template ID
            user_id: Optional user ID for authorization check

        Returns:
            NodeTemplate instance

        Raises:
            ResourceNotFoundError: If template not found
            AuthorizationError: If user cannot access private template
        """
        pass

    async def create_node_template(
        self,
        user_id: str,
        name: str,
        display_name: str,
        node_type: NodeTypeCategory,
        parameter_schema: Dict[str, Any],
        default_parameters: Dict[str, Any],
        input_ports: List[Dict[str, Any]],
        output_ports: List[Dict[str, Any]],
        description: Optional[str] = None,
        category: Optional[str] = None,
        validation_rules: Optional[Dict[str, Any]] = None,
        execution_hints: Optional[Dict[str, Any]] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None
    ) -> NodeTemplate:
        """
        Create custom node template.

        Args:
            user_id: User creating the template
            name: Unique template name (snake_case)
            display_name: UI display name
            node_type: Node type category
            parameter_schema: JSON Schema for parameter validation
            default_parameters: Default parameter values
            input_ports: Input port definitions
            output_ports: Output port definitions
            description: Optional description
            category: Optional sub-category
            validation_rules: Optional validation rules
            execution_hints: Optional code generation hints
            icon: Optional icon identifier
            color: Optional color code

        Returns:
            Created NodeTemplate instance

        Raises:
            ValidationError: If template data is invalid
            ConflictError: If template with name already exists for user
        """
        pass

    async def update_node_template(
        self,
        template_id: str,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> NodeTemplate:
        """
        Update custom node template.

        Args:
            template_id: Template ID to update
            user_id: User performing update (for authorization)
            update_data: Fields to update

        Returns:
            Updated NodeTemplate instance

        Raises:
            ResourceNotFoundError: If template not found
            AuthorizationError: If user is not owner or template is system template
            ValidationError: If update data is invalid
        """
        pass

    async def delete_node_template(
        self,
        template_id: str,
        user_id: str
    ) -> bool:
        """
        Delete custom node template (soft delete).

        Args:
            template_id: Template ID to delete
            user_id: User performing deletion

        Returns:
            True if deleted successfully

        Raises:
            ResourceNotFoundError: If template not found
            AuthorizationError: If user is not owner or template is system template
        """
        pass

    async def increment_template_usage(
        self,
        template_id: str
    ) -> None:
        """
        Increment usage count for template (called when used in logic flow).

        Args:
            template_id: Template ID
        """
        pass

    # ==================== Logic Flow Validation ====================

    async def validate_logic_flow(
        self,
        logic_flow: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate logic flow structure and node connections.

        Validation checks:
        1. Node existence: All referenced templates exist
        2. Port compatibility: Connected ports have compatible types
        3. Circular dependency: No cycles in node graph
        4. Completeness: All required inputs are connected
        5. Type consistency: Data types match across connections

        Args:
            logic_flow: Logic flow JSON with nodes and edges

        Returns:
            Validation result dict with:
                - is_valid: bool
                - errors: List[Dict[str, Any]]
                - warnings: List[Dict[str, Any]]
                - metadata: Dict (node count, edge count, etc.)

        Raises:
            ValidationError: If logic flow structure is invalid
        """
        pass

    async def detect_circular_dependency(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Optional[List[str]]:
        """
        Detect circular dependencies in node graph using topological sort.

        Args:
            nodes: List of node definitions
            edges: List of edge connections

        Returns:
            None if no cycle detected, otherwise list of node IDs in cycle

        Raises:
            LogicFlowError: If graph structure is invalid
        """
        pass

    async def topological_sort_nodes(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Perform topological sort on nodes for code generation order.

        Args:
            nodes: List of node definitions
            edges: List of edge connections

        Returns:
            List of node IDs in topological order

        Raises:
            LogicFlowError: If circular dependency detected
        """
        pass

    # ==================== Factor Integration ====================

    async def get_available_factors(
        self,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get available factors from Indicator module.

        This method integrates with IndicatorService to fetch published factors
        that can be used in INDICATOR nodes.

        Args:
            category: Optional category filter
            skip: Pagination offset
            limit: Max records

        Returns:
            Tuple of (factor list, total count)
            Each factor dict contains:
                - id: Factor ID
                - name: Factor name
                - display_name: UI display name
                - description: Factor description
                - category: Factor category
                - parameters: Available parameters
                - output_type: Output data type

        Raises:
            ServiceUnavailableError: If Indicator service unavailable
        """
        pass

    # ==================== Session Management ====================

    async def create_or_update_session(
        self,
        user_id: str,
        draft_logic_flow: Dict[str, Any],
        draft_parameters: Dict[str, Any],
        instance_id: Optional[str] = None,
        session_name: Optional[str] = None,
        session_type: SessionType = SessionType.AUTOSAVE,
        draft_metadata: Optional[Dict[str, Any]] = None
    ) -> BuilderSession:
        """
        Create new session or update existing session (upsert operation).

        This method implements auto-save functionality:
        1. If instance_id provided and session exists → Update existing session
        2. If instance_id provided and no session → Create new session
        3. If no instance_id → Create new session for unsaved strategy

        Args:
            user_id: User ID
            draft_logic_flow: Draft logic flow JSON
            draft_parameters: Draft parameter values
            instance_id: Optional strategy instance ID
            session_name: Optional session name
            session_type: Session type (DRAFT, AUTOSAVE, COLLABORATIVE)
            draft_metadata: Optional UI metadata (zoom, cursor position, etc.)

        Returns:
            Created or updated BuilderSession instance

        Raises:
            ValidationError: If draft data is invalid
        """
        pass

    async def get_session_by_id(
        self,
        session_id: str,
        user_id: str
    ) -> BuilderSession:
        """
        Get builder session by ID.

        Args:
            session_id: Session ID
            user_id: User ID for authorization

        Returns:
            BuilderSession instance

        Raises:
            ResourceNotFoundError: If session not found
            AuthorizationError: If user is not session owner
        """
        pass

    async def get_active_session_by_instance(
        self,
        instance_id: str,
        user_id: str
    ) -> Optional[BuilderSession]:
        """
        Get active session for strategy instance.

        Args:
            instance_id: Strategy instance ID
            user_id: User ID

        Returns:
            BuilderSession if found, None otherwise
        """
        pass

    async def delete_session(
        self,
        session_id: str,
        user_id: str
    ) -> bool:
        """
        Delete builder session (soft delete).

        Args:
            session_id: Session ID
            user_id: User ID for authorization

        Returns:
            True if deleted successfully

        Raises:
            ResourceNotFoundError: If session not found
            AuthorizationError: If user is not session owner
        """
        pass

    async def cleanup_expired_sessions(
        self,
        expiration_hours: int = 24
    ) -> int:
        """
        Clean up expired sessions (background task).

        Args:
            expiration_hours: Hours of inactivity before expiration

        Returns:
            Number of sessions deleted
        """
        pass


# ==================== Code Generator Service ====================

class CodeGeneratorService:
    """
    Code generation service for converting logic flows to Python code.

    Responsibilities:
    - Logic flow to Python code translation
    - Code template management (Jinja2)
    - Support for all node types (INDICATOR, CONDITION, SIGNAL, POSITION, STOP_LOSS, STOP_PROFIT)
    - Code deduplication using SHA-256 hash
    """

    def __init__(
        self,
        db: AsyncSession,
        code_generation_repo: "CodeGenerationRepository",
        builder_service: BuilderService,
        template_env: Optional[Any] = None  # Jinja2 Environment
    ):
        """
        Initialize code generator service.

        Args:
            db: Database session
            code_generation_repo: Repository for code generation history
            builder_service: Builder service for logic flow validation
            template_env: Optional Jinja2 environment for templates
        """
        self.db = db
        self.code_generation_repo = code_generation_repo
        self.builder_service = builder_service
        self.template_env = template_env

    async def generate_code(
        self,
        instance_id: str,
        user_id: str,
        logic_flow: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> CodeGeneration:
        """
        Generate Python code from logic flow.

        Process:
        1. Validate logic flow structure
        2. Perform topological sort of nodes
        3. Generate code for each node type
        4. Combine into complete strategy class
        5. Calculate code hash (SHA-256)
        6. Perform syntax and security validation
        7. Store generation record

        Args:
            instance_id: Strategy instance ID
            user_id: User requesting code generation
            logic_flow: Logic flow JSON structure
            parameters: Parameter values for nodes

        Returns:
            CodeGeneration instance with generated code and validation results

        Raises:
            ValidationError: If logic flow validation fails
            CodeGenerationError: If code generation fails
        """
        pass

    async def generate_node_code(
        self,
        node: Dict[str, Any],
        node_template: NodeTemplate,
        parameters: Dict[str, Any]
    ) -> str:
        """
        Generate code for a single node.

        Args:
            node: Node definition from logic flow
            node_template: Node template with generation hints
            parameters: Parameter values for this node

        Returns:
            Generated code snippet for this node

        Raises:
            CodeGenerationError: If code generation fails
        """
        pass

    async def render_template(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Render Jinja2 code template.

        Args:
            template_name: Template file name (e.g., "indicator_node.py.j2")
            context: Template context variables

        Returns:
            Rendered code string

        Raises:
            CodeGenerationError: If template rendering fails
        """
        pass

    async def calculate_code_hash(
        self,
        code: str
    ) -> str:
        """
        Calculate SHA-256 hash of code for deduplication.

        Args:
            code: Python code string

        Returns:
            SHA-256 hash (hex string)
        """
        pass

    async def get_code_history(
        self,
        instance_id: str,
        user_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> Tuple[List[CodeGeneration], int]:
        """
        Get code generation history for strategy instance.

        Args:
            instance_id: Strategy instance ID
            user_id: User ID for authorization
            skip: Pagination offset
            limit: Max records

        Returns:
            Tuple of (code generation list, total count)

        Raises:
            ResourceNotFoundError: If instance not found
            AuthorizationError: If user is not instance owner
        """
        pass

    async def check_code_duplicate(
        self,
        instance_id: str,
        code_hash: str
    ) -> Optional[CodeGeneration]:
        """
        Check if code with same hash already exists.

        Args:
            instance_id: Strategy instance ID
            code_hash: Code hash to check

        Returns:
            Existing CodeGeneration if found, None otherwise
        """
        pass


# ==================== Validation Service ====================

class ValidationService:
    """
    Code validation service for security and correctness checks.

    Responsibilities:
    - Python syntax validation using AST module
    - Security checks (forbidden imports, dangerous operations)
    - Logic flow completeness validation
    - Parameter range validation
    """

    def __init__(self):
        """Initialize validation service."""
        # Security configuration
        self.ALLOWED_IMPORTS = {
            # Data processing
            "numpy", "pandas", "scipy",
            # Qlib
            "qlib", "qlib.data", "qlib.contrib",
            # Technical indicators
            "talib",
            # Math and stats
            "math", "statistics", "random",
            # Date/time
            "datetime", "time",
            # Data structures
            "collections", "itertools",
            # Type hints
            "typing"
        }

        self.FORBIDDEN_IMPORTS = {
            "os", "sys", "subprocess", "shutil", "socket",
            "urllib", "requests", "__import__", "eval", "exec",
            "open", "file", "compile"
        }

        self.DANGEROUS_FUNCTIONS = {
            "eval", "exec", "compile", "__import__",
            "open", "file", "input", "raw_input"
        }

    async def validate_code(
        self,
        code: str,
        strict_mode: bool = True
    ) -> Dict[str, Any]:
        """
        Comprehensive code validation.

        Performs:
        1. Syntax validation (AST parsing)
        2. Security scan (imports, dangerous calls)
        3. Complexity analysis (cyclomatic complexity)

        Args:
            code: Python code to validate
            strict_mode: If True, treat warnings as errors

        Returns:
            Validation result dict with:
                - is_valid: bool
                - validation_status: ValidationStatus enum
                - checks: Dict containing:
                    - syntax: {passed: bool, errors: List}
                    - security: {passed: bool, violations: List}
                    - imports: {allowed: List, forbidden: List}
                    - complexity: {cyclomatic: int, cognitive: int}

        Raises:
            ValidationError: If code structure is invalid
        """
        pass

    async def validate_syntax(
        self,
        code: str
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate Python syntax using AST.

        Args:
            code: Python code string

        Returns:
            Tuple of (is_valid, error_list)
            Each error dict contains:
                - line: int
                - column: int
                - message: str
        """
        pass

    async def validate_security(
        self,
        code: str
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Perform security validation.

        Checks:
        1. Forbidden imports (os, sys, subprocess, etc.)
        2. Dangerous function calls (eval, exec, __import__)
        3. File I/O operations
        4. Network access attempts

        Args:
            code: Python code string

        Returns:
            Tuple of (is_safe, violation_list)
            Each violation dict contains:
                - severity: str (LOW, MEDIUM, HIGH, CRITICAL)
                - line: int
                - code: str (code snippet)
                - message: str
                - suggestion: str

        Raises:
            ValidationError: If AST parsing fails
        """
        pass

    async def analyze_imports(
        self,
        code: str
    ) -> Tuple[List[str], List[str]]:
        """
        Analyze and categorize imports.

        Args:
            code: Python code string

        Returns:
            Tuple of (allowed_imports, forbidden_imports)
        """
        pass

    async def calculate_complexity(
        self,
        code: str
    ) -> Dict[str, int]:
        """
        Calculate code complexity metrics.

        Metrics:
        - Cyclomatic complexity (number of decision points)
        - Cognitive complexity (human readability)
        - Max nesting depth
        - Number of functions/classes

        Args:
            code: Python code string

        Returns:
            Dict with complexity metrics

        Raises:
            ValidationError: If AST parsing fails
        """
        pass

    async def validate_parameter_ranges(
        self,
        parameters: Dict[str, Any],
        parameter_schema: Dict[str, Any]
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate parameter values against schema.

        Uses JSON Schema validation to check:
        - Type correctness
        - Value ranges (min/max)
        - Required fields
        - Enum values

        Args:
            parameters: Parameter values
            parameter_schema: JSON Schema definition

        Returns:
            Tuple of (is_valid, error_list)
        """
        pass


# ==================== Quick Test Service ====================

class QuickTestService:
    """
    Quick test service for lightweight backtest execution.

    Responsibilities:
    - Integration with Backtest module
    - Lightweight backtest execution (simplified config)
    - Test result storage and retrieval
    - Performance metrics calculation
    """

    def __init__(
        self,
        db: AsyncSession,
        quick_test_repo: "QuickTestRepository",
        backtest_execution_service: Optional[Any] = None,  # From backtest module
        task_service: Optional[Any] = None  # From task_scheduling module
    ):
        """
        Initialize quick test service.

        Args:
            db: Database session
            quick_test_repo: Repository for quick tests
            backtest_execution_service: Backtest execution service
            task_service: Task scheduling service for async execution
        """
        self.db = db
        self.quick_test_repo = quick_test_repo
        self.backtest_execution_service = backtest_execution_service
        self.task_service = task_service

        # Quick test presets
        self.PRESET_CONFIGS = {
            "1M": {"days": 30, "benchmark": "CSI300"},
            "3M": {"days": 90, "benchmark": "CSI300"},
            "6M": {"days": 180, "benchmark": "CSI300"},
            "1Y": {"days": 365, "benchmark": "CSI300"}
        }

    async def execute_quick_test(
        self,
        instance_id: str,
        user_id: str,
        test_config: Dict[str, Any],
        test_name: Optional[str] = None
    ) -> QuickTest:
        """
        Execute quick backtest (asynchronous).

        Process:
        1. Validate strategy instance exists
        2. Get logic flow and parameters snapshots
        3. Create QuickTest record (status=PENDING)
        4. Submit to background task queue
        5. Return QuickTest with test_id immediately

        Args:
            instance_id: Strategy instance ID to test
            user_id: User requesting test
            test_config: Test configuration (date_range, stock_pool, initial_capital)
            test_name: Optional test name

        Returns:
            QuickTest instance with status=PENDING

        Raises:
            ResourceNotFoundError: If strategy instance not found
            ValidationError: If test config is invalid
            QuickTestError: If test submission fails
        """
        pass

    async def get_quick_test_result(
        self,
        test_id: str,
        user_id: str
    ) -> QuickTest:
        """
        Get quick test result by ID.

        Args:
            test_id: Quick test ID
            user_id: User ID for authorization

        Returns:
            QuickTest instance with current status and results

        Raises:
            ResourceNotFoundError: If test not found
            AuthorizationError: If user is not test owner
        """
        pass

    async def get_quick_test_history(
        self,
        user_id: str,
        instance_id: Optional[str] = None,
        status: Optional[QuickTestStatus] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[QuickTest], int]:
        """
        Get quick test history for user.

        Args:
            user_id: User ID
            instance_id: Optional filter by strategy instance
            status: Optional filter by test status
            skip: Pagination offset
            limit: Max records

        Returns:
            Tuple of (test list, total count)
        """
        pass

    async def update_test_status(
        self,
        test_id: str,
        status: QuickTestStatus,
        error_message: Optional[str] = None
    ) -> QuickTest:
        """
        Update test status (called by background worker).

        Args:
            test_id: Test ID
            status: New status
            error_message: Optional error message if failed

        Returns:
            Updated QuickTest instance

        Raises:
            ResourceNotFoundError: If test not found
        """
        pass

    async def complete_quick_test(
        self,
        test_id: str,
        metrics_summary: Dict[str, Any],
        test_result: Dict[str, Any],
        execution_time: float
    ) -> QuickTest:
        """
        Complete quick test with results (called by background worker).

        Args:
            test_id: Test ID
            metrics_summary: Summary metrics (returns, sharpe, etc.)
            test_result: Full test result data
            execution_time: Execution time in seconds

        Returns:
            Updated QuickTest instance with results

        Raises:
            ResourceNotFoundError: If test not found
        """
        pass

    async def cancel_quick_test(
        self,
        test_id: str,
        user_id: str
    ) -> QuickTest:
        """
        Cancel running quick test.

        Args:
            test_id: Test ID
            user_id: User ID for authorization

        Returns:
            Updated QuickTest instance with CANCELLED status

        Raises:
            ResourceNotFoundError: If test not found
            AuthorizationError: If user is not test owner
            QuickTestError: If test is not cancellable (already completed/failed)
        """
        pass

    async def build_backtest_config(
        self,
        instance: StrategyInstance,
        test_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build backtest configuration from quick test config.

        Maps simplified quick test config to full backtest config:
        - date_range → start_date, end_date
        - stock_pool → universe (CSI300, CSI500, etc.)
        - initial_capital → backtest initial_capital
        - Add default transaction costs, slippage

        Args:
            instance: Strategy instance
            test_config: Quick test configuration

        Returns:
            Full backtest configuration dict
        """
        pass

    async def extract_metrics_summary(
        self,
        backtest_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract key metrics from full backtest result.

        Extracts:
        - total_return
        - annual_return
        - sharpe_ratio
        - max_drawdown
        - win_rate
        - total_trades

        Args:
            backtest_result: Full backtest result from backtest module

        Returns:
            Metrics summary dict
        """
        pass


# ==================== Background Tasks ====================

async def cleanup_expired_sessions_task(
    db: AsyncSession,
    expiration_hours: int = 24
) -> None:
    """
    Background task to clean up expired sessions.

    Should be scheduled to run periodically (e.g., every hour).

    Args:
        db: Database session
        expiration_hours: Hours of inactivity before expiration
    """
    from app.database.repositories.builder_session_repository import BuilderSessionRepository

    session_repo = BuilderSessionRepository(db)
    builder_service = BuilderService(db, None, session_repo, None)

    deleted_count = await builder_service.cleanup_expired_sessions(expiration_hours)
    print(f"Cleaned up {deleted_count} expired builder sessions")


async def execute_quick_test_task(
    test_id: str,
    db: AsyncSession
) -> None:
    """
    Background task to execute quick test.

    This task:
    1. Retrieves QuickTest record
    2. Updates status to RUNNING
    3. Executes backtest via BacktestExecutionService
    4. Stores results and updates status to COMPLETED/FAILED

    Args:
        test_id: Quick test ID
        db: Database session
    """
    from app.database.repositories.quick_test_repository import QuickTestRepository
    from app.modules.backtest.services.execution_service import BacktestExecutionService

    quick_test_repo = QuickTestRepository(db)
    quick_test_service = QuickTestService(db, quick_test_repo, None, None)

    try:
        # Update status to RUNNING
        await quick_test_service.update_test_status(test_id, QuickTestStatus.RUNNING)

        # Get test record
        test = await quick_test_repo.get(test_id)

        # Execute backtest (implementation depends on backtest module integration)
        # backtest_result = await backtest_execution_service.execute(...)

        # Extract metrics and complete test
        # await quick_test_service.complete_quick_test(...)

    except Exception as e:
        # Mark test as failed
        await quick_test_service.update_test_status(
            test_id,
            QuickTestStatus.FAILED,
            error_message=str(e)
        )
        raise


# ==================== Type Exports ====================

__all__ = [
    "BuilderService",
    "CodeGeneratorService",
    "ValidationService",
    "QuickTestService",
    "BuilderServiceError",
    "ValidationError",
    "ResourceNotFoundError",
    "AuthorizationError",
    "LogicFlowError",
    "CodeGenerationError",
    "QuickTestError",
    "cleanup_expired_sessions_task",
    "execute_quick_test_task"
]
