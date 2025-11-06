"""
IndicatorRepository Tests (TDD)

Comprehensive test suite for IndicatorRepository functionality.
This follows the Red-Green-Refactor TDD cycle.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.indicator import (
    IndicatorComponent, IndicatorCategory, IndicatorSource
)
from app.database.repositories.indicator_repository import IndicatorRepository


class TestIndicatorRepository:
    """Test suite for IndicatorRepository"""

    # ========== CREATE Tests ==========

    @pytest.mark.asyncio
    async def test_create_indicator(
        self,
        indicator_repo: IndicatorRepository,
        db_session: AsyncSession
    ):
        """Test creating a new indicator"""
        # Arrange
        indicator_data = {
            "code": "SMA",
            "name_zh": "简单移动平均",
            "name_en": "Simple Moving Average",
            "category": IndicatorCategory.TREND.value,
            "source": IndicatorSource.TALIB.value,
            "description_zh": "计算指定周期的简单移动平均值",
            "description_en": "Calculate simple moving average over specified period",
            "is_system": True,
            "is_enabled": True,
            "tags": ["trend", "moving_average"],
        }

        # Act
        indicator = await indicator_repo.create(obj_in=indicator_data, commit=True)

        # Assert
        assert indicator.id is not None
        assert indicator.code == "SMA"
        assert indicator.name_zh == "简单移动平均"
        assert indicator.category == IndicatorCategory.TREND.value
        assert indicator.usage_count == 0
        assert indicator.is_system is True

        # Cleanup
        await indicator_repo.delete(indicator.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_create_indicator_with_parameters(
        self,
        indicator_repo: IndicatorRepository
    ):
        """Test creating an indicator with parameter definitions"""
        # Arrange
        indicator_data = {
            "code": "EMA",
            "name_zh": "指数移动平均",
            "name_en": "Exponential Moving Average",
            "category": IndicatorCategory.TREND.value,
            "source": IndicatorSource.TALIB.value,
            "parameters": {
                "timeperiod": {
                    "type": "integer",
                    "min": 2,
                    "max": 100,
                    "description": "Time period"
                }
            },
            "default_params": {"timeperiod": 20},
        }

        # Act
        indicator = await indicator_repo.create(obj_in=indicator_data, commit=True)

        # Assert
        assert indicator.parameters is not None
        assert "timeperiod" in indicator.parameters
        assert indicator.default_params["timeperiod"] == 20

        # Cleanup
        await indicator_repo.delete(indicator.id, soft=False, commit=True)

    # ========== READ Tests ==========

    @pytest.mark.asyncio
    async def test_get_indicator_by_id(
        self,
        indicator_repo: IndicatorRepository
    ):
        """Test retrieving an indicator by ID"""
        # Arrange
        indicator_data = {
            "code": "RSI",
            "name_zh": "相对强弱指标",
            "name_en": "Relative Strength Index",
            "category": IndicatorCategory.MOMENTUM.value,
            "source": IndicatorSource.TALIB.value,
        }
        created = await indicator_repo.create(obj_in=indicator_data, commit=True)

        # Act
        retrieved = await indicator_repo.get(created.id)

        # Assert
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.code == "RSI"

        # Cleanup
        await indicator_repo.delete(created.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_get_by_category(
        self,
        indicator_repo: IndicatorRepository
    ):
        """Test retrieving indicators by category"""
        # Arrange
        indicators_data = [
            {
                "code": "SMA_TEST",
                "name_zh": "测试SMA",
                "name_en": "Test SMA",
                "category": IndicatorCategory.TREND.value,
                "source": IndicatorSource.TALIB.value,
            },
            {
                "code": "RSI_TEST",
                "name_zh": "测试RSI",
                "name_en": "Test RSI",
                "category": IndicatorCategory.MOMENTUM.value,
                "source": IndicatorSource.TALIB.value,
            },
        ]

        created_ids = []
        for data in indicators_data:
            indicator = await indicator_repo.create(obj_in=data, commit=True)
            created_ids.append(indicator.id)

        # Act
        trend_indicators = await indicator_repo.get_by_category(IndicatorCategory.TREND)

        # Assert
        assert len(trend_indicators) >= 1
        assert all(ind.category == IndicatorCategory.TREND.value for ind in trend_indicators)
        assert any(ind.code == "SMA_TEST" for ind in trend_indicators)

        # Cleanup
        for indicator_id in created_ids:
            await indicator_repo.delete(indicator_id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_search_by_name_chinese(
        self,
        indicator_repo: IndicatorRepository
    ):
        """Test searching indicators by Chinese name"""
        # Arrange
        indicator_data = {
            "code": "MACD",
            "name_zh": "平滑异同移动平均线",
            "name_en": "Moving Average Convergence Divergence",
            "category": IndicatorCategory.TREND.value,
            "source": IndicatorSource.TALIB.value,
        }
        created = await indicator_repo.create(obj_in=indicator_data, commit=True)

        # Act
        results = await indicator_repo.search_by_name("移动平均")

        # Assert
        assert len(results) >= 1
        assert any(ind.code == "MACD" for ind in results)

        # Cleanup
        await indicator_repo.delete(created.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_search_by_name_english(
        self,
        indicator_repo: IndicatorRepository
    ):
        """Test searching indicators by English name"""
        # Arrange
        indicator_data = {
            "code": "BBANDS",
            "name_zh": "布林带",
            "name_en": "Bollinger Bands",
            "category": IndicatorCategory.VOLATILITY.value,
            "source": IndicatorSource.TALIB.value,
        }
        created = await indicator_repo.create(obj_in=indicator_data, commit=True)

        # Act
        results = await indicator_repo.search_by_name("Bollinger")

        # Assert
        assert len(results) >= 1
        assert any(ind.code == "BBANDS" for ind in results)

        # Cleanup
        await indicator_repo.delete(created.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_search_by_code(
        self,
        indicator_repo: IndicatorRepository
    ):
        """Test searching indicators by code"""
        # Arrange
        indicator_data = {
            "code": "ATR",
            "name_zh": "平均真实波幅",
            "name_en": "Average True Range",
            "category": IndicatorCategory.VOLATILITY.value,
            "source": IndicatorSource.TALIB.value,
        }
        created = await indicator_repo.create(obj_in=indicator_data, commit=True)

        # Act
        results = await indicator_repo.search_by_name("ATR")

        # Assert
        assert len(results) >= 1
        assert any(ind.code == "ATR" for ind in results)

        # Cleanup
        await indicator_repo.delete(created.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_get_popular_indicators(
        self,
        indicator_repo: IndicatorRepository
    ):
        """Test retrieving popular indicators sorted by usage count"""
        # Arrange
        indicators_data = [
            {
                "code": "POP1",
                "name_zh": "热门1",
                "name_en": "Popular 1",
                "category": IndicatorCategory.TREND.value,
                "source": IndicatorSource.TALIB.value,
                "usage_count": 100,
            },
            {
                "code": "POP2",
                "name_zh": "热门2",
                "name_en": "Popular 2",
                "category": IndicatorCategory.TREND.value,
                "source": IndicatorSource.TALIB.value,
                "usage_count": 50,
            },
            {
                "code": "POP3",
                "name_zh": "热门3",
                "name_en": "Popular 3",
                "category": IndicatorCategory.TREND.value,
                "source": IndicatorSource.TALIB.value,
                "usage_count": 200,
            },
        ]

        created_ids = []
        for data in indicators_data:
            indicator = await indicator_repo.create(obj_in=data, commit=True)
            created_ids.append(indicator.id)

        # Act
        popular = await indicator_repo.get_popular_indicators(limit=2)

        # Assert
        assert len(popular) == 2
        # Should be sorted by usage_count descending
        assert popular[0].usage_count >= popular[1].usage_count

        # Cleanup
        for indicator_id in created_ids:
            await indicator_repo.delete(indicator_id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_get_system_indicators(
        self,
        indicator_repo: IndicatorRepository
    ):
        """Test retrieving system built-in indicators"""
        # Arrange
        indicators_data = [
            {
                "code": "SYS1",
                "name_zh": "系统指标1",
                "name_en": "System 1",
                "category": IndicatorCategory.TREND.value,
                "source": IndicatorSource.TALIB.value,
                "is_system": True,
            },
            {
                "code": "USR1",
                "name_zh": "用户指标1",
                "name_en": "User 1",
                "category": IndicatorCategory.TREND.value,
                "source": IndicatorSource.CUSTOM.value,
                "is_system": False,
            },
        ]

        created_ids = []
        for data in indicators_data:
            indicator = await indicator_repo.create(obj_in=data, commit=True)
            created_ids.append(indicator.id)

        # Act
        system_indicators = await indicator_repo.get_system_indicators()

        # Assert
        assert len(system_indicators) >= 1
        assert all(ind.is_system is True for ind in system_indicators)
        assert any(ind.code == "SYS1" for ind in system_indicators)

        # Cleanup
        for indicator_id in created_ids:
            await indicator_repo.delete(indicator_id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_get_user_indicators(
        self,
        indicator_repo: IndicatorRepository
    ):
        """Test retrieving user-defined indicators"""
        # Arrange
        indicators_data = [
            {
                "code": "USR2",
                "name_zh": "用户指标2",
                "name_en": "User 2",
                "category": IndicatorCategory.CUSTOM.value,
                "source": IndicatorSource.CUSTOM.value,
                "is_system": False,
            },
        ]

        created_ids = []
        for data in indicators_data:
            indicator = await indicator_repo.create(obj_in=data, commit=True)
            created_ids.append(indicator.id)

        # Act
        user_indicators = await indicator_repo.get_user_indicators()

        # Assert
        assert len(user_indicators) >= 1
        assert all(ind.is_system is False for ind in user_indicators)

        # Cleanup
        for indicator_id in created_ids:
            await indicator_repo.delete(indicator_id, soft=False, commit=True)

    # ========== UPDATE Tests ==========

    @pytest.mark.asyncio
    async def test_increment_usage_count(
        self,
        indicator_repo: IndicatorRepository,
        db_session: AsyncSession
    ):
        """Test atomically incrementing usage count"""
        # Arrange
        indicator_data = {
            "code": "USAGE_TEST",
            "name_zh": "使用量测试",
            "name_en": "Usage Test",
            "category": IndicatorCategory.TREND.value,
            "source": IndicatorSource.TALIB.value,
            "usage_count": 10,
        }
        created = await indicator_repo.create(obj_in=indicator_data, commit=True)
        initial_count = created.usage_count

        # Act
        updated = await indicator_repo.increment_usage_count(created.id)

        # Assert
        assert updated is not None
        assert updated.usage_count == initial_count + 1

        # Cleanup
        await indicator_repo.delete(created.id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_update_indicator(
        self,
        indicator_repo: IndicatorRepository
    ):
        """Test updating an indicator"""
        # Arrange
        indicator_data = {
            "code": "UPDATE_TEST",
            "name_zh": "更新测试",
            "name_en": "Update Test",
            "category": IndicatorCategory.TREND.value,
            "source": IndicatorSource.TALIB.value,
            "is_enabled": True,
        }
        created = await indicator_repo.create(obj_in=indicator_data, commit=True)

        # Act
        updated = await indicator_repo.update(
            created.id,
            {"is_enabled": False, "name_zh": "已更新"},
            commit=True
        )

        # Assert
        assert updated is not None
        assert updated.is_enabled is False
        assert updated.name_zh == "已更新"

        # Cleanup
        await indicator_repo.delete(created.id, soft=False, commit=True)

    # ========== DELETE Tests ==========

    @pytest.mark.asyncio
    async def test_soft_delete_indicator(
        self,
        indicator_repo: IndicatorRepository
    ):
        """Test soft deleting an indicator"""
        # Arrange
        indicator_data = {
            "code": "DEL_TEST",
            "name_zh": "删除测试",
            "name_en": "Delete Test",
            "category": IndicatorCategory.TREND.value,
            "source": IndicatorSource.TALIB.value,
        }
        created = await indicator_repo.create(obj_in=indicator_data, commit=True)
        indicator_id = created.id

        # Act
        deleted = await indicator_repo.delete(indicator_id, soft=True, commit=True)

        # Assert
        assert deleted is True
        normal_get = await indicator_repo.get(indicator_id, include_deleted=False)
        assert normal_get is None
        deleted_ind = await indicator_repo.get(indicator_id, include_deleted=True)
        assert deleted_ind is not None
        assert deleted_ind.is_deleted is True

        # Cleanup
        await indicator_repo.delete(indicator_id, soft=False, commit=True)

    # ========== FILTER Tests ==========

    @pytest.mark.asyncio
    async def test_filter_by_source(
        self,
        indicator_repo: IndicatorRepository
    ):
        """Test filtering indicators by source"""
        # Arrange
        indicators_data = [
            {
                "code": "TALIB1",
                "name_zh": "TA-Lib指标1",
                "name_en": "TA-Lib 1",
                "category": IndicatorCategory.TREND.value,
                "source": IndicatorSource.TALIB.value,
            },
            {
                "code": "QLIB1",
                "name_zh": "Qlib指标1",
                "name_en": "Qlib 1",
                "category": IndicatorCategory.TREND.value,
                "source": IndicatorSource.QLIB.value,
            },
        ]

        created_ids = []
        for data in indicators_data:
            indicator = await indicator_repo.create(obj_in=data, commit=True)
            created_ids.append(indicator.id)

        # Act
        talib_indicators = await indicator_repo.get_multi(source=IndicatorSource.TALIB.value)

        # Assert
        assert len(talib_indicators) >= 1
        assert all(ind.source == IndicatorSource.TALIB.value for ind in talib_indicators)

        # Cleanup
        for indicator_id in created_ids:
            await indicator_repo.delete(indicator_id, soft=False, commit=True)

    @pytest.mark.asyncio
    async def test_filter_enabled_only(
        self,
        indicator_repo: IndicatorRepository
    ):
        """Test filtering only enabled indicators"""
        # Arrange
        indicators_data = [
            {
                "code": "ENABLED1",
                "name_zh": "启用指标1",
                "name_en": "Enabled 1",
                "category": IndicatorCategory.TREND.value,
                "source": IndicatorSource.TALIB.value,
                "is_enabled": True,
            },
            {
                "code": "DISABLED1",
                "name_zh": "禁用指标1",
                "name_en": "Disabled 1",
                "category": IndicatorCategory.TREND.value,
                "source": IndicatorSource.TALIB.value,
                "is_enabled": False,
            },
        ]

        created_ids = []
        for data in indicators_data:
            indicator = await indicator_repo.create(obj_in=data, commit=True)
            created_ids.append(indicator.id)

        # Act
        enabled_indicators = await indicator_repo.get_multi(is_enabled=True)

        # Assert
        assert len(enabled_indicators) >= 1
        assert all(ind.is_enabled is True for ind in enabled_indicators)

        # Cleanup
        for indicator_id in created_ids:
            await indicator_repo.delete(indicator_id, soft=False, commit=True)

    # ========== PAGINATION Tests ==========

    @pytest.mark.asyncio
    async def test_pagination(
        self,
        indicator_repo: IndicatorRepository
    ):
        """Test pagination functionality"""
        # Arrange
        indicators_data = [
            {
                "code": f"PAGE{i}",
                "name_zh": f"分页测试{i}",
                "name_en": f"Page Test {i}",
                "category": IndicatorCategory.TREND.value,
                "source": IndicatorSource.TALIB.value,
            }
            for i in range(5)
        ]

        created_ids = []
        for data in indicators_data:
            indicator = await indicator_repo.create(obj_in=data, commit=True)
            created_ids.append(indicator.id)

        # Act
        page1 = await indicator_repo.get_multi(skip=0, limit=2)
        page2 = await indicator_repo.get_multi(skip=2, limit=2)

        # Assert
        assert len(page1) == 2
        assert len(page2) == 2
        # Ensure different results
        assert page1[0].id != page2[0].id

        # Cleanup
        for indicator_id in created_ids:
            await indicator_repo.delete(indicator_id, soft=False, commit=True)

    # ========== COUNT Tests ==========

    @pytest.mark.asyncio
    async def test_count_indicators(
        self,
        indicator_repo: IndicatorRepository
    ):
        """Test counting indicators with filters"""
        # Arrange
        indicators_data = [
            {
                "code": f"COUNT{i}",
                "name_zh": f"计数测试{i}",
                "name_en": f"Count Test {i}",
                "category": IndicatorCategory.MOMENTUM.value,
                "source": IndicatorSource.TALIB.value,
            }
            for i in range(3)
        ]

        created_ids = []
        for data in indicators_data:
            indicator = await indicator_repo.create(obj_in=data, commit=True)
            created_ids.append(indicator.id)

        # Act
        count = await indicator_repo.count(category=IndicatorCategory.MOMENTUM.value)

        # Assert
        assert count >= 3

        # Cleanup
        for indicator_id in created_ids:
            await indicator_repo.delete(indicator_id, soft=False, commit=True)
