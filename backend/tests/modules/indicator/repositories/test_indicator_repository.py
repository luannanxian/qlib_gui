"""
TDD Tests for IndicatorRepository

Following Test-Driven Development:
1. RED: Write failing tests first
2. GREEN: Implement minimum code to pass
3. REFACTOR: Improve code quality

Tests cover the new count methods and search functionality.
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import IndicatorComponent
from app.database.repositories.indicator_repository import IndicatorRepository


@pytest.mark.asyncio
class TestIndicatorRepositoryCount:
    """Test count methods for pagination support."""

    async def test_count_all_enabled_indicators(self, db_session: AsyncSession):
        """Test counting all enabled indicators."""
        # ARRANGE: Create test data
        repo = IndicatorRepository(db_session)

        # Add some indicators
        indicators = [
            IndicatorComponent(
                code=f"IND_{i}",
                name_zh=f"指标{i}",
                name_en=f"Indicator {i}",
                category="trend",
                source="qlib",
                is_enabled=True,
                is_deleted=False
            )
            for i in range(5)
        ]

        for ind in indicators:
            db_session.add(ind)
        await db_session.commit()

        # ACT: Count indicators
        count = await repo.count(is_enabled=True)

        # ASSERT: Should count all 5 indicators
        assert count == 5

    async def test_count_excludes_disabled_indicators(self, db_session: AsyncSession):
        """Test that count excludes disabled indicators."""
        # ARRANGE
        repo = IndicatorRepository(db_session)

        # Add enabled and disabled indicators
        enabled = [
            IndicatorComponent(
                code=f"ENABLED_{i}",
                name_zh=f"启用{i}",
                name_en=f"Enabled {i}",
                category="trend",
                source="qlib",
                is_enabled=True,
                is_deleted=False
            )
            for i in range(3)
        ]

        disabled = [
            IndicatorComponent(
                code=f"DISABLED_{i}",
                name_zh=f"禁用{i}",
                name_en=f"Disabled {i}",
                category="trend",
                source="qlib",
                is_enabled=False,
                is_deleted=False
            )
            for i in range(2)
        ]

        for ind in enabled + disabled:
            db_session.add(ind)
        await db_session.commit()

        # ACT
        count = await repo.count(is_enabled=True)

        # ASSERT: Should only count enabled
        assert count == 3

    async def test_count_excludes_deleted_indicators(self, db_session: AsyncSession):
        """Test that count excludes soft-deleted indicators."""
        # ARRANGE
        repo = IndicatorRepository(db_session)

        # Add active and deleted indicators
        active = IndicatorComponent(
            code="ACTIVE",
            name_zh="活跃",
            name_en="Active",
            category="trend",
            source="qlib",
            is_enabled=True,
            is_deleted=False
        )

        deleted = IndicatorComponent(
            code="DELETED",
            name_zh="已删除",
            name_en="Deleted",
            category="trend",
            source="qlib",
            is_enabled=True,
            is_deleted=True
        )

        db_session.add(active)
        db_session.add(deleted)
        await db_session.commit()

        # ACT
        count = await repo.count(is_enabled=True)

        # ASSERT: Should exclude deleted
        assert count == 1

    async def test_count_search_results_by_name_zh(self, db_session: AsyncSession):
        """Test counting search results matching Chinese name."""
        # ARRANGE
        repo = IndicatorRepository(db_session)

        indicators = [
            IndicatorComponent(
                code="SMA",
                name_zh="简单移动平均",
                name_en="Simple Moving Average",
                category="trend",
                source="qlib",
                is_enabled=True,
                is_deleted=False
            ),
            IndicatorComponent(
                code="EMA",
                name_zh="指数移动平均",
                name_en="Exponential Moving Average",
                category="trend",
                source="qlib",
                is_enabled=True,
                is_deleted=False
            ),
            IndicatorComponent(
                code="RSI",
                name_zh="相对强弱指标",
                name_en="Relative Strength Index",
                category="momentum",
                source="qlib",
                is_enabled=True,
                is_deleted=False
            ),
        ]

        for ind in indicators:
            db_session.add(ind)
        await db_session.commit()

        # ACT: Search for "移动"
        count = await repo.count_search_results("移动")

        # ASSERT: Should find 2 indicators with "移动" in name_zh
        assert count == 2

    async def test_count_search_results_by_name_en(self, db_session: AsyncSession):
        """Test counting search results matching English name."""
        # ARRANGE
        repo = IndicatorRepository(db_session)

        indicators = [
            IndicatorComponent(
                code="SMA",
                name_zh="简单移动平均",
                name_en="Simple Moving Average",
                category="trend",
                source="qlib",
                is_enabled=True,
                is_deleted=False
            ),
            IndicatorComponent(
                code="EMA",
                name_zh="指数移动平均",
                name_en="Exponential Moving Average",
                category="trend",
                source="qlib",
                is_enabled=True,
                is_deleted=False
            ),
            IndicatorComponent(
                code="RSI",
                name_zh="相对强弱指标",
                name_en="Relative Strength Index",
                category="momentum",
                source="qlib",
                is_enabled=True,
                is_deleted=False
            ),
        ]

        for ind in indicators:
            db_session.add(ind)
        await db_session.commit()

        # ACT: Search for "Moving"
        count = await repo.count_search_results("Moving")

        # ASSERT: Should find 2 indicators with "Moving" in name_en
        assert count == 2

    async def test_count_search_results_by_code(self, db_session: AsyncSession):
        """Test counting search results matching indicator code."""
        # ARRANGE
        repo = IndicatorRepository(db_session)

        indicators = [
            IndicatorComponent(
                code="SMA_20",
                name_zh="简单移动平均20",
                name_en="SMA 20",
                category="trend",
                source="qlib",
                is_enabled=True,
                is_deleted=False
            ),
            IndicatorComponent(
                code="SMA_50",
                name_zh="简单移动平均50",
                name_en="SMA 50",
                category="trend",
                source="qlib",
                is_enabled=True,
                is_deleted=False
            ),
            IndicatorComponent(
                code="RSI",
                name_zh="相对强弱指标",
                name_en="Relative Strength Index",
                category="momentum",
                source="qlib",
                is_enabled=True,
                is_deleted=False
            ),
        ]

        for ind in indicators:
            db_session.add(ind)
        await db_session.commit()

        # ACT: Search for "SMA"
        count = await repo.count_search_results("SMA")

        # ASSERT: Should find 2 indicators with "SMA" in code
        assert count == 2

    async def test_count_search_results_case_insensitive(self, db_session: AsyncSession):
        """Test that search is case-insensitive."""
        # ARRANGE
        repo = IndicatorRepository(db_session)

        indicator = IndicatorComponent(
            code="SMA",
            name_zh="简单移动平均",
            name_en="Simple Moving Average",
            category="trend",
            source="qlib",
            is_enabled=True,
            is_deleted=False
        )

        db_session.add(indicator)
        await db_session.commit()

        # ACT: Search with different cases
        count_lower = await repo.count_search_results("sma")
        count_upper = await repo.count_search_results("SMA")
        count_mixed = await repo.count_search_results("Sma")

        # ASSERT: All should find the indicator
        assert count_lower == 1
        assert count_upper == 1
        assert count_mixed == 1

    async def test_count_search_results_no_matches(self, db_session: AsyncSession):
        """Test counting search results with no matches."""
        # ARRANGE
        repo = IndicatorRepository(db_session)

        indicator = IndicatorComponent(
            code="RSI",
            name_zh="相对强弱指标",
            name_en="Relative Strength Index",
            category="momentum",
            source="qlib",
            is_enabled=True,
            is_deleted=False
        )

        db_session.add(indicator)
        await db_session.commit()

        # ACT: Search for non-existent keyword
        count = await repo.count_search_results("nonexistent")

        # ASSERT: Should return 0
        assert count == 0

    async def test_count_search_results_empty_database(self, db_session: AsyncSession):
        """Test counting search results in empty database."""
        # ARRANGE
        repo = IndicatorRepository(db_session)

        # ACT: Search in empty database
        count = await repo.count_search_results("anything")

        # ASSERT: Should return 0
        assert count == 0


@pytest.mark.asyncio
class TestIndicatorRepositorySearch:
    """Test search functionality."""

    async def test_search_by_name_returns_results(self, db_session: AsyncSession):
        """Test that search returns matching indicators."""
        # ARRANGE
        repo = IndicatorRepository(db_session)

        indicators = [
            IndicatorComponent(
                code="SMA",
                name_zh="简单移动平均",
                name_en="Simple Moving Average",
                category="trend",
                source="qlib",
                is_enabled=True,
                is_deleted=False
            ),
            IndicatorComponent(
                code="EMA",
                name_zh="指数移动平均",
                name_en="Exponential Moving Average",
                category="trend",
                source="qlib",
                is_enabled=True,
                is_deleted=False
            ),
        ]

        for ind in indicators:
            db_session.add(ind)
        await db_session.commit()

        # ACT: Search for "移动"
        results = await repo.search_by_name(keyword="移动", skip=0, limit=10)

        # ASSERT: Should return 2 results
        assert len(results) == 2
        assert all("移动" in ind.name_zh for ind in results)

    async def test_search_pagination(self, db_session: AsyncSession):
        """Test search with pagination."""
        # ARRANGE
        repo = IndicatorRepository(db_session)

        indicators = [
            IndicatorComponent(
                code=f"IND_{i}",
                name_zh=f"测试指标{i}",
                name_en=f"Test Indicator {i}",
                category="trend",
                source="qlib",
                is_enabled=True,
                is_deleted=False
            )
            for i in range(10)
        ]

        for ind in indicators:
            db_session.add(ind)
        await db_session.commit()

        # ACT: Get first page
        page1 = await repo.search_by_name(keyword="测试", skip=0, limit=5)
        page2 = await repo.search_by_name(keyword="测试", skip=5, limit=5)

        # ASSERT: Each page should have 5 items
        assert len(page1) == 5
        assert len(page2) == 5

        # Results should be different
        page1_codes = {ind.code for ind in page1}
        page2_codes = {ind.code for ind in page2}
        assert page1_codes.isdisjoint(page2_codes)
