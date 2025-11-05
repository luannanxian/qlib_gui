"""
ValidationService

Validates strategy logic flow structure and business rules.

Validation Checks:
1. Logic flow structure (non-empty, node connectivity)
2. Signal completeness (buy and sell signals required)
3. Position constraints (total <= 100%)
4. Stop loss configuration
5. Node-specific validations
"""

from typing import Set, List
from collections import defaultdict

from app.modules.strategy.schemas.strategy import (
    LogicFlow,
    LogicNode,
    ValidationError,
    StrategyValidationResponse
)
from app.database.models.strategy import NodeType, SignalType


class ValidationService:
    """Service for validating strategy logic flows"""

    def validate_logic_flow(self, flow: LogicFlow) -> StrategyValidationResponse:
        """
        Validate basic logic flow structure

        Checks:
        - Flow is not empty
        - Nodes are connected
        - No invalid node references in edges

        Args:
            flow: Logic flow to validate

        Returns:
            Validation response with errors/warnings
        """
        errors: List[ValidationError] = []
        warnings: List[ValidationError] = []

        # Check if flow is empty
        if not flow.nodes:
            errors.append(ValidationError(
                type="empty_flow",
                message="Logic flow cannot be empty. Please add at least one node.",
                severity="error"
            ))
            return StrategyValidationResponse(is_valid=False, errors=errors)

        # Build node ID set
        node_ids: Set[str] = {node.id for node in flow.nodes}

        # Validate edge references
        for edge in flow.edges:
            if edge.from_ not in node_ids:
                errors.append(ValidationError(
                    type="invalid_edge_source",
                    message=f"Edge references non-existent source node: {edge.from_}",
                    node_id=edge.from_,
                    severity="error"
                ))
            if edge.to not in node_ids:
                errors.append(ValidationError(
                    type="invalid_edge_target",
                    message=f"Edge references non-existent target node: {edge.to}",
                    node_id=edge.to,
                    severity="error"
                ))

        # Check for disconnected nodes (nodes with no edges)
        if flow.edges:
            connected_nodes: Set[str] = set()
            for edge in flow.edges:
                connected_nodes.add(edge.from_)
                connected_nodes.add(edge.to)

            disconnected = node_ids - connected_nodes
            if disconnected:
                warnings.append(ValidationError(
                    type="disconnected_nodes",
                    message=f"Found {len(disconnected)} disconnected node(s). Consider connecting all nodes.",
                    severity="warning"
                ))

        # Check for circular dependencies (warning only, allowed for feedback loops)
        if self._has_cycle(flow):
            warnings.append(ValidationError(
                type="circular_dependency",
                message="Detected circular dependencies in logic flow. This may be intentional for feedback loops.",
                severity="warning"
            ))

        is_valid = len(errors) == 0
        return StrategyValidationResponse(is_valid=is_valid, errors=errors, warnings=warnings)

    def check_signals(self, flow: LogicFlow) -> StrategyValidationResponse:
        """
        Validate signal nodes

        Checks:
        - At least one BUY signal exists
        - At least one SELL signal exists

        Args:
            flow: Logic flow to validate

        Returns:
            Validation response
        """
        errors: List[ValidationError] = []

        signal_nodes = [node for node in flow.nodes if node.type == NodeType.SIGNAL]

        has_buy = any(node.signal_type == SignalType.BUY for node in signal_nodes)
        has_sell = any(node.signal_type == SignalType.SELL for node in signal_nodes)

        if not has_buy:
            errors.append(ValidationError(
                type="missing_buy_signal",
                message="Strategy must contain at least one BUY signal node.",
                severity="error"
            ))

        if not has_sell:
            errors.append(ValidationError(
                type="missing_sell_signal",
                message="Strategy must contain at least one SELL signal node.",
                severity="error"
            ))

        is_valid = len(errors) == 0
        return StrategyValidationResponse(is_valid=is_valid, errors=errors)

    def check_positions(self, flow: LogicFlow) -> StrategyValidationResponse:
        """
        Validate position nodes

        Checks:
        - All position nodes have position_value set
        - Total position allocation <= 100%

        Args:
            flow: Logic flow to validate

        Returns:
            Validation response
        """
        errors: List[ValidationError] = []

        position_nodes = [node for node in flow.nodes if node.type == NodeType.POSITION]

        if not position_nodes:
            # No position nodes is valid (default behavior)
            return StrategyValidationResponse(is_valid=True, errors=[])

        total_position = 0.0

        for node in position_nodes:
            if node.position_value is None:
                errors.append(ValidationError(
                    type="missing_position_value",
                    message=f"Position node must have position_value set.",
                    node_id=node.id,
                    severity="error"
                ))
            else:
                total_position += node.position_value

        if total_position > 100.0:
            errors.append(ValidationError(
                type="position_exceeded",
                message=f"Total position allocation ({total_position}%) exceeds 100%.",
                severity="error"
            ))

        is_valid = len(errors) == 0
        return StrategyValidationResponse(is_valid=is_valid, errors=errors)

    def check_stop_loss(self, flow: LogicFlow) -> StrategyValidationResponse:
        """
        Validate stop loss nodes

        Checks:
        - All stop loss nodes have stop_loss_value set

        Args:
            flow: Logic flow to validate

        Returns:
            Validation response
        """
        errors: List[ValidationError] = []

        stop_loss_nodes = [node for node in flow.nodes if node.type == NodeType.STOP_LOSS]

        for node in stop_loss_nodes:
            if node.stop_loss_value is None:
                errors.append(ValidationError(
                    type="missing_stop_loss_value",
                    message=f"Stop loss node must have stop_loss_value set.",
                    node_id=node.id,
                    severity="error"
                ))

        is_valid = len(errors) == 0
        return StrategyValidationResponse(is_valid=is_valid, errors=errors)

    def validate(self, flow: LogicFlow) -> StrategyValidationResponse:
        """
        Run all validation checks

        Args:
            flow: Logic flow to validate

        Returns:
            Comprehensive validation response
        """
        all_errors: List[ValidationError] = []
        all_warnings: List[ValidationError] = []

        # Run all validation checks
        checks = [
            self.validate_logic_flow(flow),
            self.check_signals(flow),
            self.check_positions(flow),
            self.check_stop_loss(flow)
        ]

        for result in checks:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)

        is_valid = len(all_errors) == 0
        return StrategyValidationResponse(
            is_valid=is_valid,
            errors=all_errors,
            warnings=all_warnings
        )

    def _has_cycle(self, flow: LogicFlow) -> bool:
        """
        Check if logic flow contains cycles (circular dependencies)

        Uses DFS to detect cycles in the directed graph.

        Args:
            flow: Logic flow to check

        Returns:
            True if cycle exists, False otherwise
        """
        # Build adjacency list
        graph = defaultdict(list)
        for edge in flow.edges:
            graph[edge.from_].append(edge.to)

        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        # Check all nodes
        for node in flow.nodes:
            if node.id not in visited:
                if dfs(node.id):
                    return True

        return False
