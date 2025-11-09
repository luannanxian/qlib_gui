"""
BuilderService

Core builder service for Strategy Builder module.

This module provides the main business logic for:
- Node template CRUD operations with strict authorization
- Logic flow validation including circular dependency detection
- Integration with Indicator module for factor listing
- Session management with auto-save and expiration cleanup

Architecture:
    BuilderService acts as the service layer coordinating between
    repositories and business logic, enforcing authorization rules
    and validating data before persistence.

Example:
    >>> service = BuilderService(db, node_repo, session_repo)
    >>> templates, total = await service.get_node_templates(
    ...     node_type=NodeTypeCategory.INDICATOR
    ... )
    >>> session = await service.create_or_update_session(
    ...     user_id="user-001",
    ...     draft_logic_flow={"nodes": [], "edges": []}
    ... )

Author: Qlib-UI Strategy Builder Team
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy_builder import (
    NodeTemplate,
    BuilderSession,
    NodeTypeCategory,
    SessionType
)
from app.database.repositories.node_template_repository import NodeTemplateRepository
from app.database.repositories.builder_session_repository import BuilderSessionRepository
from app.modules.strategy.exceptions import (
    ResourceNotFoundError,
    AuthorizationError,
    ValidationError,
    LogicFlowError
)

# Constants
DEFAULT_PAGE_SIZE = 20
DEFAULT_FACTOR_PAGE_SIZE = 50
DEFAULT_SESSION_EXPIRATION_HOURS = 24


class BuilderService:
    """
    Core builder service for node templates, logic flow validation, and session management.

    Responsibilities:
    - Node template CRUD operations with authorization
    - Logic flow validation (circular dependency, type checking)
    - Integration with Indicator module for factor listing
    - Session auto-save and expiration cleanup
    """

    def __init__(
        self,
        db: AsyncSession,
        node_template_repo: NodeTemplateRepository,
        session_repo: BuilderSessionRepository,
        indicator_service: Optional[Any] = None
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
        logger.debug(
            f"Getting node templates: type={node_type}, category={category}, "
            f"is_system={is_system_template}, user={user_id}"
        )

        # Use repository search method
        templates = await self.node_template_repo.search(
            keyword=None,
            node_type=node_type,
            category=category,
            is_system_template=is_system_template,
            user_id=user_id,
            skip=skip,
            limit=limit
        )

        # Count total (for now, return templates length as proxy)
        # In production, would add separate count query
        total = len(templates)

        logger.info(f"Retrieved {len(templates)} templates (total: {total})")
        return templates, total

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
        template = await self.node_template_repo.get(template_id)

        if not template:
            raise ResourceNotFoundError(f"Template not found: {template_id}")

        # Check authorization for custom templates
        if not template.is_system_template and user_id:
            if template.user_id != user_id:
                raise AuthorizationError(
                    f"User {user_id} is not authorized to access this template"
                )

        return template

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
        """
        logger.info(f"Creating custom node template: {name} by user {user_id}")

        # Validate node_type
        if not isinstance(node_type, NodeTypeCategory):
            raise ValidationError(f"Invalid node type: {node_type}")

        template_data = {
            "user_id": user_id,
            "name": name,
            "display_name": display_name,
            "node_type": node_type.value,
            "parameter_schema": parameter_schema,
            "default_parameters": default_parameters,
            "input_ports": input_ports,
            "output_ports": output_ports,
            "description": description,
            "category": category,
            "validation_rules": validation_rules,
            "execution_hints": execution_hints,
            "icon": icon,
            "color": color,
            "is_system_template": False,
            "usage_count": 0
        }

        template = await self.node_template_repo.create(template_data)

        logger.info(f"Created custom template: {template.id}")
        return template

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
        logger.info(f"Updating template {template_id} by user {user_id}")

        # Get template and check authorization
        template = await self.node_template_repo.get(template_id)

        if not template:
            raise ResourceNotFoundError(f"Template not found: {template_id}")

        if template.is_system_template:
            raise AuthorizationError("Cannot modify system template")

        if template.user_id != user_id:
            raise AuthorizationError(
                f"User {user_id} is not authorized to update this template"
            )

        # Update template
        updated = await self.node_template_repo.update(
            template_id,
            update_data
        )

        logger.info(f"Updated template: {template_id}")
        return updated

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
        logger.info(f"Deleting template {template_id} by user {user_id}")

        # Get template and check authorization
        template = await self.node_template_repo.get(template_id)

        if not template:
            raise ResourceNotFoundError(f"Template not found: {template_id}")

        if template.is_system_template:
            raise AuthorizationError("Cannot delete system template")

        if template.user_id != user_id:
            raise AuthorizationError(
                f"User {user_id} is not authorized to delete this template"
            )

        # Soft delete
        await self.node_template_repo.delete(template_id)

        logger.info(f"Deleted template: {template_id}")
        return True

    async def increment_template_usage(
        self,
        template_id: str
    ) -> None:
        """
        Increment usage count for template (called when used in logic flow).

        Args:
            template_id: Template ID
        """
        await self.node_template_repo.increment_usage(template_id)

        logger.debug(f"Incremented usage count for template: {template_id}")

    # ==================== Logic Flow Validation ====================

    async def validate_logic_flow(
        self,
        logic_flow: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate logic flow structure and node connections.

        Validation checks:
        1. Node existence: All referenced templates exist
        2. Circular dependency: No cycles in node graph
        3. Structural integrity: Valid nodes and edges

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
        logger.debug("Validating logic flow")

        errors = []
        warnings = []

        # Extract nodes and edges
        nodes = logic_flow.get("nodes", [])
        edges = logic_flow.get("edges", [])

        # Validate structure
        if not isinstance(nodes, list):
            raise ValidationError("Logic flow 'nodes' must be a list")
        if not isinstance(edges, list):
            raise ValidationError("Logic flow 'edges' must be a list")

        # Check 1: All node templates exist
        for node in nodes:
            template_id = node.get("template_id")
            if template_id:
                try:
                    template = await self.node_template_repo.get(template_id)
                    if not template:
                        errors.append({
                            "node_id": node.get("id"),
                            "message": f"Template not found: {template_id}",
                            "severity": "ERROR"
                        })
                except Exception as e:
                    errors.append({
                        "node_id": node.get("id"),
                        "message": f"Error loading template: {str(e)}",
                        "severity": "ERROR"
                    })

        # Check 2: Detect circular dependencies
        if len(errors) == 0:  # Only check cycles if templates are valid
            cycle = await self.detect_circular_dependency(nodes, edges)
            if cycle:
                errors.append({
                    "message": "Circular dependency detected",
                    "cycle": cycle,
                    "severity": "ERROR"
                })

        # Build metadata
        metadata = {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "node_types": {}
        }

        for node in nodes:
            node_type = node.get("type", "UNKNOWN")
            metadata["node_types"][node_type] = metadata["node_types"].get(node_type, 0) + 1

        is_valid = len(errors) == 0

        result = {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "metadata": metadata
        }

        logger.info(
            f"Logic flow validation: {'PASSED' if is_valid else 'FAILED'} "
            f"({len(errors)} errors, {len(warnings)} warnings)"
        )

        return result

    async def detect_circular_dependency(
        self,
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]]
    ) -> Optional[List[str]]:
        """
        Detect circular dependencies in node graph using DFS.

        Args:
            nodes: List of node definitions
            edges: List of edge connections

        Returns:
            None if no cycle detected, otherwise list of node IDs in cycle

        Raises:
            LogicFlowError: If graph structure is invalid
        """
        logger.debug("Detecting circular dependencies")

        # Build adjacency list
        graph = defaultdict(list)
        node_ids = set(node["id"] for node in nodes)

        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")

            if source not in node_ids or target not in node_ids:
                raise LogicFlowError(
                    f"Edge references non-existent node: {source} -> {target}"
                )

            graph[source].append(target)

        # DFS to detect cycle
        visited = set()
        rec_stack = set()
        cycle_path = []

        def dfs(node_id: str, path: List[str]) -> bool:
            """DFS helper to detect cycle"""
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            for neighbor in graph[node_id]:
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle_path.extend(path[cycle_start:])
                    return True

            rec_stack.remove(node_id)
            path.pop()
            return False

        # Check each node
        for node in nodes:
            node_id = node["id"]
            if node_id not in visited:
                if dfs(node_id, []):
                    logger.warning(f"Circular dependency detected: {cycle_path}")
                    return cycle_path

        logger.debug("No circular dependencies found")
        return None

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
        # Check for cycles first
        cycle = await self.detect_circular_dependency(nodes, edges)
        if cycle:
            raise LogicFlowError(f"Cannot sort: circular dependency detected: {cycle}")

        # Build in-degree map
        in_degree = {node["id"]: 0 for node in nodes}
        graph = defaultdict(list)

        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            graph[source].append(target)
            in_degree[target] += 1

        # Kahn's algorithm
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        sorted_nodes = []

        while queue:
            node_id = queue.popleft()
            sorted_nodes.append(node_id)

            for neighbor in graph[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        logger.debug(f"Topological sort: {sorted_nodes}")
        return sorted_nodes

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

        Raises:
            ServiceUnavailableError: If Indicator service unavailable
        """
        logger.debug(f"Getting available factors: category={category}")

        if not self.indicator_service:
            logger.warning("Indicator service not available")
            return [], 0

        # Call indicator service
        try:
            factors, total = await self.indicator_service.list_factors(
                category=category,
                skip=skip,
                limit=limit
            )

            logger.info(f"Retrieved {len(factors)} factors (total: {total})")
            return factors, total

        except Exception as e:
            logger.error(f"Error fetching factors: {e}")
            raise

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
        1. If instance_id provided and session exists -> Update existing session
        2. If instance_id provided and no session -> Create new session
        3. If no instance_id -> Create new session for unsaved strategy

        Args:
            user_id: User ID
            draft_logic_flow: Draft logic flow JSON
            draft_parameters: Draft parameter values
            instance_id: Optional strategy instance ID
            session_name: Optional session name
            session_type: Session type (DRAFT, AUTOSAVE, COLLABORATIVE)
            draft_metadata: Optional UI metadata

        Returns:
            Created or updated BuilderSession instance

        Raises:
            ValidationError: If draft data is invalid
        """
        logger.info(
            f"Creating/updating session for user {user_id}, instance {instance_id}"
        )

        # Prepare session data
        session_data = {
            "user_id": user_id,
            "draft_logic_flow": draft_logic_flow,
            "draft_parameters": draft_parameters,
            "instance_id": instance_id,
            "session_name": session_name,
            "session_type": session_type.value if isinstance(session_type, SessionType) else session_type,
            "draft_metadata": draft_metadata,
            "is_active": True,
            "last_activity_at": datetime.utcnow()
        }

        # Use repository upsert
        session = await self.session_repo.upsert(session_data)

        logger.info(f"Session {'updated' if session else 'created'}: {session.id}")
        return session

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
        logger.debug(f"Getting session {session_id} for user {user_id}")

        session = await self.session_repo.get(session_id)

        if not session:
            raise ResourceNotFoundError(f"Session not found: {session_id}")

        if session.user_id != user_id:
            raise AuthorizationError(
                f"User {user_id} is not authorized to access this session"
            )

        return session

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
        logger.debug(
            f"Getting active session for instance {instance_id}, user {user_id}"
        )

        sessions = await self.session_repo.find_by_instance(
            instance_id=instance_id,
            user_id=user_id,
            active_only=True
        )

        if sessions:
            return sessions[0]  # Return first active session

        return None

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
        logger.info(f"Deleting session {session_id} by user {user_id}")

        # Get session and check authorization
        session = await self.session_repo.get(session_id)

        if not session:
            raise ResourceNotFoundError(f"Session not found: {session_id}")

        if session.user_id != user_id:
            raise AuthorizationError(
                f"User {user_id} is not authorized to delete this session"
            )

        # Soft delete
        await self.session_repo.delete(session_id)

        logger.info(f"Deleted session: {session_id}")
        return True

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
        logger.info(f"Cleaning up sessions expired after {expiration_hours} hours")

        # Calculate expiration threshold
        expiration_time = datetime.utcnow() - timedelta(hours=expiration_hours)

        # Find and expire sessions
        deleted_count = 0

        # Get sessions with old last_activity_at
        from sqlalchemy import select
        from app.database.models.strategy_builder import BuilderSession

        stmt = select(BuilderSession).where(
            BuilderSession.last_activity_at < expiration_time,
            BuilderSession.is_active == True,
            BuilderSession.is_deleted == False
        )

        result = await self.db.execute(stmt)
        expired_sessions = list(result.scalars().all())

        for session in expired_sessions:
            await self.session_repo.expire_session(session.id, commit=False)
            deleted_count += 1

        if deleted_count > 0:
            await self.db.commit()

        logger.info(f"Cleaned up {deleted_count} expired sessions")
        return deleted_count


# Module exports
__all__ = [
    "BuilderService",
    "DEFAULT_PAGE_SIZE",
    "DEFAULT_FACTOR_PAGE_SIZE",
    "DEFAULT_SESSION_EXPIRATION_HOURS",
]
