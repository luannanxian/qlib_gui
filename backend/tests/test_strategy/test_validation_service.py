"""
TDD Tests for ValidationService

Validates strategy logic flow structure and constraints.

Test Coverage:
- Logic flow structure validation
- Signal node validation (buy/sell required)
- Position node validation (total <= 100%)
- Stop loss validation
- Node connectivity validation
- Complete validation pipeline
"""

import pytest

from app.modules.strategy.services.validation_service import ValidationService
from app.modules.strategy.schemas.strategy import (
    LogicFlow,
    LogicNode,
    LogicEdge,
    ValidationError
)
from app.database.models.strategy import NodeType, SignalType, PositionType


class TestValidationServiceLogicFlow:
    """Test logic flow structure validation"""

    def test_validate_empty_logic_flow(self):
        """Test validation fails for empty logic flow"""
        service = ValidationService()

        flow = LogicFlow(nodes=[], edges=[])
        result = service.validate_logic_flow(flow)

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("empty" in err.message.lower() for err in result.errors)

    def test_validate_disconnected_nodes(self):
        """Test validation warns about disconnected nodes"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.INDICATOR),
                LogicNode(id="2", type=NodeType.SIGNAL, signal_type=SignalType.BUY),
                LogicNode(id="3", type=NodeType.INDICATOR)  # Disconnected
            ],
            edges=[
                LogicEdge(**{"from": "1", "to": "2"})
            ]
        )

        result = service.validate_logic_flow(flow)

        # Should have warnings about disconnected node
        assert any("disconnected" in warn.message.lower() for warn in result.warnings)

    def test_validate_circular_dependency(self):
        """Test validation detects circular dependencies"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.INDICATOR),
                LogicNode(id="2", type=NodeType.CONDITION),
                LogicNode(id="3", type=NodeType.SIGNAL, signal_type=SignalType.BUY)
            ],
            edges=[
                LogicEdge(**{"from": "1", "to": "2"}),
                LogicEdge(**{"from": "2", "to": "3"}),
                LogicEdge(**{"from": "3", "to": "1"})  # Creates cycle
            ]
        )

        result = service.validate_logic_flow(flow)

        # Circular dependencies are warnings, not errors (allowed for feedback loops)
        assert any("circular" in warn.message.lower() for warn in result.warnings)


class TestValidationServiceSignals:
    """Test signal node validation"""

    def test_validate_missing_buy_signal(self):
        """Test validation fails when buy signal is missing"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.INDICATOR),
                LogicNode(id="2", type=NodeType.SIGNAL, signal_type=SignalType.SELL)
            ],
            edges=[
                LogicEdge(**{"from": "1", "to": "2"})
            ]
        )

        result = service.check_signals(flow)

        assert result.is_valid is False
        assert any("buy" in err.message.lower() for err in result.errors)

    def test_validate_missing_sell_signal(self):
        """Test validation fails when sell signal is missing"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.INDICATOR),
                LogicNode(id="2", type=NodeType.SIGNAL, signal_type=SignalType.BUY)
            ],
            edges=[
                LogicEdge(**{"from": "1", "to": "2"})
            ]
        )

        result = service.check_signals(flow)

        assert result.is_valid is False
        assert any("sell" in err.message.lower() for err in result.errors)

    def test_validate_both_signals_present(self):
        """Test validation passes with both buy and sell signals"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.INDICATOR),
                LogicNode(id="2", type=NodeType.SIGNAL, signal_type=SignalType.BUY),
                LogicNode(id="3", type=NodeType.SIGNAL, signal_type=SignalType.SELL)
            ],
            edges=[
                LogicEdge(**{"from": "1", "to": "2"}),
                LogicEdge(**{"from": "1", "to": "3"})
            ]
        )

        result = service.check_signals(flow)

        assert result.is_valid is True
        assert len(result.errors) == 0


class TestValidationServicePositions:
    """Test position node validation"""

    def test_validate_position_total_exceeds_100(self):
        """Test validation fails when total position > 100%"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.INDICATOR),
                LogicNode(id="2", type=NodeType.POSITION, position_value=60.0),
                LogicNode(id="3", type=NodeType.POSITION, position_value=50.0)
            ],
            edges=[
                LogicEdge(**{"from": "1", "to": "2"}),
                LogicEdge(**{"from": "1", "to": "3"})
            ]
        )

        result = service.check_positions(flow)

        assert result.is_valid is False
        assert any("100" in err.message for err in result.errors)

    def test_validate_position_total_valid(self):
        """Test validation passes when total position <= 100%"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.INDICATOR),
                LogicNode(id="2", type=NodeType.POSITION, position_value=40.0),
                LogicNode(id="3", type=NodeType.POSITION, position_value=60.0)
            ],
            edges=[
                LogicEdge(**{"from": "1", "to": "2"}),
                LogicEdge(**{"from": "1", "to": "3"})
            ]
        )

        result = service.check_positions(flow)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_position_node_missing_value(self):
        """Test validation fails when position node has no value"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.INDICATOR),
                LogicNode(id="2", type=NodeType.POSITION)  # No position_value
            ],
            edges=[
                LogicEdge(**{"from": "1", "to": "2"})
            ]
        )

        result = service.check_positions(flow)

        assert result.is_valid is False
        assert any("position_value" in err.message.lower() for err in result.errors)


class TestValidationServiceStopLoss:
    """Test stop loss validation"""

    def test_validate_stop_loss_missing_value(self):
        """Test validation fails when stop loss has no value"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.STOP_LOSS, stop_loss_type="PERCENTAGE")
            ],
            edges=[]
        )

        result = service.check_stop_loss(flow)

        assert result.is_valid is False
        assert any("stop_loss_value" in err.message.lower() for err in result.errors)

    def test_validate_stop_loss_valid(self):
        """Test validation passes with valid stop loss"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(
                    id="1",
                    type=NodeType.STOP_LOSS,
                    stop_loss_type="PERCENTAGE",
                    stop_loss_value=5.0
                )
            ],
            edges=[]
        )

        result = service.check_stop_loss(flow)

        assert result.is_valid is True
        assert len(result.errors) == 0


class TestValidationServiceComplete:
    """Test complete validation pipeline"""

    def test_validate_complete_valid_strategy(self):
        """Test complete validation passes for valid strategy"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.INDICATOR, indicator="MA"),
                LogicNode(id="2", type=NodeType.CONDITION, condition="MA > 100"),
                LogicNode(id="3", type=NodeType.SIGNAL, signal_type=SignalType.BUY),
                LogicNode(id="4", type=NodeType.SIGNAL, signal_type=SignalType.SELL),
                LogicNode(id="5", type=NodeType.POSITION, position_value=50.0),
                LogicNode(id="6", type=NodeType.STOP_LOSS, stop_loss_type="PERCENTAGE", stop_loss_value=5.0)
            ],
            edges=[
                LogicEdge(**{"from": "1", "to": "2"}),
                LogicEdge(**{"from": "2", "to": "3"}),
                LogicEdge(**{"from": "2", "to": "4"}),
                LogicEdge(**{"from": "3", "to": "5"}),
                LogicEdge(**{"from": "3", "to": "6"})
            ]
        )

        result = service.validate(flow)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_complete_invalid_strategy(self):
        """Test complete validation fails with multiple errors"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.INDICATOR),
                # Missing sell signal
                LogicNode(id="2", type=NodeType.SIGNAL, signal_type=SignalType.BUY),
                # Position exceeds 100%
                LogicNode(id="3", type=NodeType.POSITION, position_value=150.0)
            ],
            edges=[
                LogicEdge(**{"from": "1", "to": "2"}),
                LogicEdge(**{"from": "2", "to": "3"})
            ]
        )

        result = service.validate(flow)

        assert result.is_valid is False
        # Should have errors for missing sell signal and position > 100%
        assert len(result.errors) >= 2

    def test_validate_returns_error_locations(self):
        """Test validation returns node IDs where errors occurred"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="pos_node_1", type=NodeType.POSITION)  # Missing value
            ],
            edges=[]
        )

        result = service.validate(flow)

        # Error should include node_id
        assert any(err.node_id == "pos_node_1" for err in result.errors)


class TestValidationServiceEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_invalid_edge_source_and_target(self):
        """Test validation catches invalid edge references"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.INDICATOR),
                LogicNode(id="2", type=NodeType.SIGNAL, signal_type=SignalType.BUY)
            ],
            edges=[
                LogicEdge(**{"from": "99", "to": "1"}),  # Invalid source
                LogicEdge(**{"from": "1", "to": "99"})   # Invalid target
            ]
        )

        result = service.validate_logic_flow(flow)

        assert result.is_valid is False
        assert len(result.errors) == 2

    def test_position_exactly_100_percent(self):
        """Test validation passes when position allocation is exactly 100%"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.POSITION, position_value=50.0),
                LogicNode(id="2", type=NodeType.POSITION, position_value=50.0)
            ],
            edges=[]
        )

        result = service.check_positions(flow)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_single_position_node_100_percent(self):
        """Test validation passes with single position at 100%"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.POSITION, position_value=100.0)
            ],
            edges=[]
        )

        result = service.check_positions(flow)

        assert result.is_valid is True

    def test_no_position_nodes_valid(self):
        """Test validation passes when no position nodes exist"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.INDICATOR)
            ],
            edges=[]
        )

        result = service.check_positions(flow)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_no_stop_loss_nodes_valid(self):
        """Test validation passes when no stop loss nodes exist"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.INDICATOR)
            ],
            edges=[]
        )

        result = service.check_stop_loss(flow)

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_multiple_stop_loss_nodes_with_values(self):
        """Test validation passes with multiple stop loss nodes"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.STOP_LOSS, stop_loss_value=5.0),
                LogicNode(id="2", type=NodeType.STOP_LOSS, stop_loss_value=10.0)
            ],
            edges=[]
        )

        result = service.check_stop_loss(flow)

        assert result.is_valid is True

    def test_complex_cycle_detection(self):
        """Test cycle detection with complex graph"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.INDICATOR),
                LogicNode(id="2", type=NodeType.CONDITION),
                LogicNode(id="3", type=NodeType.CONDITION),
                LogicNode(id="4", type=NodeType.SIGNAL, signal_type=SignalType.BUY)
            ],
            edges=[
                LogicEdge(**{"from": "1", "to": "2"}),
                LogicEdge(**{"from": "2", "to": "3"}),
                LogicEdge(**{"from": "3", "to": "4"}),
                LogicEdge(**{"from": "4", "to": "2"})  # Cycle back
            ]
        )

        result = service.validate_logic_flow(flow)

        # Should have cycle warning
        assert any("circular" in warn.message.lower() for warn in result.warnings)

    def test_self_loop_detection(self):
        """Test detection of self-loops"""
        service = ValidationService()

        flow = LogicFlow(
            nodes=[
                LogicNode(id="1", type=NodeType.INDICATOR)
            ],
            edges=[
                LogicEdge(**{"from": "1", "to": "1"})  # Self loop
            ]
        )

        result = service.validate_logic_flow(flow)

        # Self loop is a cycle
        assert any("circular" in warn.message.lower() for warn in result.warnings)
