"""
Pytest Configuration for Strategy Builder Tests

Provides fixtures for testing strategy builder functionality.
"""

import pytest
import pytest_asyncio
from jinja2 import Environment, FileSystemLoader, DictLoader
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy import StrategyInstance, StrategyTemplate
from app.database.models.strategy_builder import QuickTest, BuilderSession, NodeTemplate, NodeTypeCategory


@pytest_asyncio.fixture
async def sample_strategy_template(db_session: AsyncSession):
    """Create a sample strategy template"""
    template = StrategyTemplate(
        name="test_template",
        description="Test template",
        category="TREND_FOLLOWING",
        logic_flow={"nodes": [], "edges": []},
        parameters={},
        is_system_template=True
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    return template


@pytest_asyncio.fixture
async def sample_strategy_instance(db_session: AsyncSession, sample_strategy_template):
    """Create a sample strategy instance"""
    instance = StrategyInstance(
        template_id=sample_strategy_template.id,
        name="test_instance",
        user_id="user-001",
        logic_flow={"nodes": [], "edges": []},
        parameters={},
        status="DRAFT"
    )
    db_session.add(instance)
    await db_session.commit()
    await db_session.refresh(instance)
    return instance


@pytest_asyncio.fixture
async def sample_quick_test(db_session: AsyncSession, sample_strategy_instance):
    """Create a sample quick test"""
    quick_test = QuickTest(
        instance_id=sample_strategy_instance.id,
        user_id="user-001",
        test_config={"start_date": "2020-01-01", "end_date": "2023-12-31"},
        logic_flow_snapshot={"nodes": [], "edges": []},
        status="PENDING"
    )
    db_session.add(quick_test)
    await db_session.commit()
    await db_session.refresh(quick_test)
    return quick_test


@pytest_asyncio.fixture
async def sample_builder_session(db_session: AsyncSession, sample_strategy_instance):
    """Create a sample builder session"""
    session = BuilderSession(
        instance_id=sample_strategy_instance.id,
        user_id="user-001",
        draft_logic_flow={"nodes": [], "edges": []},
        is_active=True
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


# ==================== CodeGeneratorService Fixtures ====================

@pytest_asyncio.fixture
async def sample_indicator_template(db_session: AsyncSession):
    """Create a sample INDICATOR node template"""
    template = NodeTemplate(
        name="ma_crossover",
        display_name="Moving Average Crossover",
        description="Calculate moving average crossover indicator",
        node_type=NodeTypeCategory.INDICATOR.value,
        category="TREND",
        parameter_schema={
            "type": "object",
            "properties": {
                "short_period": {"type": "integer", "minimum": 1, "default": 5},
                "long_period": {"type": "integer", "minimum": 1, "default": 20}
            },
            "required": ["short_period", "long_period"]
        },
        default_parameters={"short_period": 5, "long_period": 20},
        input_ports=[{"name": "price", "data_type": "DataFrame"}],
        output_ports=[{"name": "signal", "data_type": "Series"}],
        is_system_template=True,
        user_id=None
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    return template


@pytest_asyncio.fixture
async def sample_condition_template(db_session: AsyncSession):
    """Create a sample CONDITION node template"""
    template = NodeTemplate(
        name="threshold_condition",
        display_name="Threshold Condition",
        description="Check if value exceeds threshold",
        node_type=NodeTypeCategory.CONDITION.value,
        category="COMPARISON",
        parameter_schema={
            "type": "object",
            "properties": {
                "threshold": {"type": "number", "default": 0},
                "operator": {"type": "string", "enum": [">", "<", ">=", "<=", "=="], "default": ">"}
            }
        },
        default_parameters={"threshold": 0, "operator": ">"},
        input_ports=[{"name": "value", "data_type": "Series"}],
        output_ports=[{"name": "result", "data_type": "Series"}],
        is_system_template=True,
        user_id=None
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    return template


@pytest_asyncio.fixture
async def sample_signal_template(db_session: AsyncSession):
    """Create a sample SIGNAL node template"""
    template = NodeTemplate(
        name="buy_signal",
        display_name="Buy Signal",
        description="Generate buy signal when condition is met",
        node_type=NodeTypeCategory.SIGNAL.value,
        category="TRADING",
        parameter_schema={
            "type": "object",
            "properties": {
                "signal_type": {"type": "string", "enum": ["BUY", "SELL"], "default": "BUY"}
            }
        },
        default_parameters={"signal_type": "BUY"},
        input_ports=[{"name": "condition", "data_type": "Series"}],
        output_ports=[{"name": "signal", "data_type": "Series"}],
        is_system_template=True,
        user_id=None
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    return template


@pytest.fixture
def sample_logic_flow(sample_indicator_template, sample_condition_template, sample_signal_template):
    """Sample logic flow with INDICATOR + CONDITION + SIGNAL nodes"""
    return {
        "nodes": [
            {
                "id": "node-1",
                "template_id": str(sample_indicator_template.id),
                "type": "INDICATOR",
                "position": {"x": 100, "y": 100}
            },
            {
                "id": "node-2",
                "template_id": str(sample_condition_template.id),
                "type": "CONDITION",
                "position": {"x": 300, "y": 100}
            },
            {
                "id": "node-3",
                "template_id": str(sample_signal_template.id),
                "type": "SIGNAL",
                "position": {"x": 500, "y": 100}
            }
        ],
        "edges": [
            {
                "id": "edge-1",
                "source": "node-1",
                "target": "node-2",
                "sourcePort": "signal",
                "targetPort": "value"
            },
            {
                "id": "edge-2",
                "source": "node-2",
                "target": "node-3",
                "sourcePort": "result",
                "targetPort": "condition"
            }
        ]
    }


@pytest.fixture
def sample_parameters():
    """Sample parameters for logic flow nodes"""
    return {
        "node-1": {
            "short_period": 5,
            "long_period": 20
        },
        "node-2": {
            "threshold": 0,
            "operator": ">"
        },
        "node-3": {
            "signal_type": "BUY"
        }
    }


@pytest.fixture
def sample_qlib_strategy_code():
    """Expected Qlib-compatible strategy code"""
    return '''from qlib.strategy.base import BaseStrategy
from qlib.data import D
import pandas as pd
import talib


class CustomStrategy(BaseStrategy):
    """Auto-generated strategy from Strategy Builder"""

    def __init__(self, short_period=5, long_period=20):
        super().__init__()
        self.short_period = short_period
        self.long_period = long_period

    def generate_trade_decision(self, score, current_temp, pred_score, trade_exchange):
        """Generate trade decision based on logic flow"""
        # INDICATOR: MA Crossover
        ma_short = talib.SMA(score, timeperiod=self.short_period)
        ma_long = talib.SMA(score, timeperiod=self.long_period)
        signal = ma_short - ma_long

        # CONDITION: Threshold check
        condition = signal > 0

        # SIGNAL: Buy signal
        trade_decision = condition.astype(int)

        return trade_decision
'''


@pytest.fixture
def jinja2_test_env():
    """Create test Jinja2 environment with in-memory templates"""
    templates = {
        'indicator_node.py.j2': '''# INDICATOR: {{ node.display_name }}
ma_short = talib.SMA(score, timeperiod={{ params.short_period }})
ma_long = talib.SMA(score, timeperiod={{ params.long_period }})
signal = ma_short - ma_long''',
        'condition_node.py.j2': '''# CONDITION: {{ node.display_name }}
condition = {{ input_var }} {{ params.operator }} {{ params.threshold }}''',
        'signal_node.py.j2': '''# SIGNAL: {{ node.display_name }}
trade_decision = {{ input_var }}.astype(int)''',
        'strategy_class.py.j2': '''from qlib.strategy.base import BaseStrategy
from qlib.data import D
import pandas as pd
import talib


class CustomStrategy(BaseStrategy):
    """Auto-generated strategy from Strategy Builder"""

    def __init__(self, **kwargs):
        super().__init__()
        for key, value in kwargs.items():
            setattr(self, key, value)

    def generate_trade_decision(self, score, current_temp, pred_score, trade_exchange):
        """Generate trade decision based on logic flow"""
{{ code_body | indent(8) }}

        return trade_decision
'''
    }

    return Environment(loader=DictLoader(templates))


# ==================== BuilderService Fixtures ====================

@pytest_asyncio.fixture
async def builder_service(db_session: AsyncSession):
    """Create BuilderService instance"""
    from app.database.repositories.node_template_repository import NodeTemplateRepository
    from app.database.repositories.builder_session_repository import BuilderSessionRepository
    from app.modules.strategy.services.builder_service import BuilderService

    node_template_repo = NodeTemplateRepository(db_session)
    session_repo = BuilderSessionRepository(db_session)

    return BuilderService(
        db=db_session,
        node_template_repo=node_template_repo,
        session_repo=session_repo,
        indicator_service=None
    )


@pytest.fixture
def mock_indicator_service():
    """Mock IndicatorService for testing"""
    from unittest.mock import AsyncMock, MagicMock

    mock_service = MagicMock()

    # Mock list_factors method
    async def mock_list_factors(category=None, skip=0, limit=100):
        factors = [
            {
                "id": "factor-001",
                "name": "ma_5",
                "display_name": "5-Day Moving Average",
                "description": "Simple moving average with 5-day period",
                "category": "technical",
                "parameters": {"period": 5},
                "output_type": "Series"
            },
            {
                "id": "factor-002",
                "name": "rsi_14",
                "display_name": "14-Day RSI",
                "description": "Relative Strength Index with 14-day period",
                "category": "technical",
                "parameters": {"period": 14},
                "output_type": "Series"
            }
        ]

        if category:
            factors = [f for f in factors if f["category"] == category]

        total = len(factors)
        return factors[skip:skip+limit], total

    mock_service.list_factors = AsyncMock(side_effect=mock_list_factors)

    return mock_service


@pytest_asyncio.fixture
async def builder_service_with_indicator(db_session: AsyncSession, mock_indicator_service):
    """Create BuilderService with mocked IndicatorService"""
    from app.database.repositories.node_template_repository import NodeTemplateRepository
    from app.database.repositories.builder_session_repository import BuilderSessionRepository
    from app.modules.strategy.services.builder_service import BuilderService

    node_template_repo = NodeTemplateRepository(db_session)
    session_repo = BuilderSessionRepository(db_session)

    return BuilderService(
        db=db_session,
        node_template_repo=node_template_repo,
        session_repo=session_repo,
        indicator_service=mock_indicator_service
    )


@pytest.fixture
def sample_custom_template_data():
    """Sample custom template data for creation"""
    return {
        "name": "custom_indicator",
        "display_name": "Custom Indicator",
        "node_type": NodeTypeCategory.INDICATOR,
        "parameter_schema": {
            "type": "object",
            "properties": {
                "period": {"type": "integer", "minimum": 1, "default": 10}
            }
        },
        "default_parameters": {"period": 10},
        "input_ports": [{"name": "data", "data_type": "DataFrame"}],
        "output_ports": [{"name": "result", "data_type": "Series"}],
        "description": "A custom indicator template",
        "category": "CUSTOM"
    }


@pytest_asyncio.fixture
async def sample_custom_template(db_session: AsyncSession):
    """Create a custom node template for testing"""
    template = NodeTemplate(
        name="user_custom_indicator",
        display_name="User Custom Indicator",
        description="User's custom indicator",
        node_type=NodeTypeCategory.INDICATOR.value,
        category="CUSTOM",
        parameter_schema={"type": "object", "properties": {}},
        default_parameters={},
        input_ports=[],
        output_ports=[],
        is_system_template=False,
        user_id="user-001"
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    return template


@pytest.fixture
def sample_valid_logic_flow(sample_indicator_template, sample_condition_template, sample_signal_template):
    """Sample valid logic flow for validation testing"""
    return {
        "nodes": [
            {
                "id": "node-1",
                "template_id": str(sample_indicator_template.id),
                "type": "INDICATOR"
            },
            {
                "id": "node-2",
                "template_id": str(sample_condition_template.id),
                "type": "CONDITION"
            },
            {
                "id": "node-3",
                "template_id": str(sample_signal_template.id),
                "type": "SIGNAL"
            }
        ],
        "edges": [
            {"source": "node-1", "target": "node-2"},
            {"source": "node-2", "target": "node-3"}
        ]
    }


@pytest_asyncio.fixture
async def expired_session(db_session: AsyncSession, sample_strategy_instance):
    """Create an expired session for cleanup testing"""
    from datetime import datetime, timedelta

    session = BuilderSession(
        instance_id=sample_strategy_instance.id,
        user_id="user-001",
        draft_logic_flow={"nodes": [], "edges": []},
        draft_parameters={},
        is_active=True,
        last_activity_at=datetime.utcnow() - timedelta(hours=48),  # 48 hours ago
        expires_at=datetime.utcnow() - timedelta(hours=24)  # Expired 24 hours ago
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session
