"""
Pytest Configuration for Strategy Builder Tests

Provides fixtures for testing strategy builder functionality.
"""

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy import StrategyInstance, StrategyTemplate
from app.database.models.strategy_builder import QuickTest, BuilderSession


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
