"""
Debug test to verify fixture works correctly.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import IndicatorComponent


@pytest.mark.asyncio
async def test_fixture_creates_tables(db_session: AsyncSession):
    """Simple test to verify tables are created."""
    # Try to insert a simple indicator
    indicator = IndicatorComponent(
        code="TEST",
        name_zh="测试",
        name_en="Test",
        category="trend",
        source="qlib",
        is_enabled=True,
        is_deleted=False
    )

    db_session.add(indicator)
    await db_session.commit()
    await db_session.refresh(indicator)

    assert indicator.id is not None
    assert indicator.code == "TEST"
    print(f"✓ Fixture works! Created indicator with ID: {indicator.id}")
