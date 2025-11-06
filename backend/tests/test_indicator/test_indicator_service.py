"""
Tests for IndicatorService

Tests business logic for indicator operations.
"""

import pytest
import pytest_asyncio
from typing import Dict, Any

from app.database.models.indicator import IndicatorCategory, IndicatorSource


@pytest_asyncio.fixture
async def sample_indicator_data() -> Dict[str, Any]:
    """Sample indicator data for testing"""
    return {
        "code": "SMA",
        "name_zh": "简单移动平均线",
        "name_en": "Simple Moving Average",
        "category": IndicatorCategory.TREND.value,
        "source": IndicatorSource.TALIB.value,
        "description_zh": "简单移动平均线指标",
        "description_en": "Simple Moving Average indicator",
        "is_enabled": True
    }


@pytest.mark.asyncio
class TestIndicatorService:
    """IndicatorService测试套件"""

    async def test_get_indicators_by_category(self, indicator_service, indicator_repo, sample_indicator_data):
        """测试按分类获取指标"""
        # Create indicators in different categories
        trend_data = sample_indicator_data.copy()
        await indicator_repo.create(trend_data, commit=True)

        momentum_data = sample_indicator_data.copy()
        momentum_data["code"] = "RSI"
        momentum_data["name_zh"] = "相对强弱指标"
        momentum_data["name_en"] = "Relative Strength Index"
        momentum_data["category"] = IndicatorCategory.MOMENTUM.value
        await indicator_repo.create(momentum_data, commit=True)

        # Get trend indicators
        result = await indicator_service.get_indicators_by_category(
            category=IndicatorCategory.TREND.value
        )

        assert len(result["indicators"]) == 1
        assert result["indicators"][0]["category"] == IndicatorCategory.TREND.value
        assert result["total"] == 1

    async def test_search_indicators(self, indicator_service, indicator_repo, sample_indicator_data):
        """测试搜索指标"""
        await indicator_repo.create(sample_indicator_data, commit=True)

        # Search by Chinese name
        result = await indicator_service.search_indicators("移动平均")
        assert len(result["indicators"]) == 1
        assert "移动平均" in result["indicators"][0]["name_zh"]

    async def test_get_indicator_detail(self, indicator_service, indicator_repo, sample_indicator_data):
        """测试获取指标详情"""
        created = await indicator_repo.create(sample_indicator_data, commit=True)

        detail = await indicator_service.get_indicator_detail(created.id)

        assert detail is not None
        assert detail["id"] == created.id
        assert detail["code"] == "SMA"
        assert detail["category"] == IndicatorCategory.TREND.value

    async def test_get_indicator_detail_not_found(self, indicator_service):
        """测试获取不存在的指标详情"""
        detail = await indicator_service.get_indicator_detail("nonexistent_id")
        assert detail is None

    async def test_increment_indicator_usage(self, indicator_service, indicator_repo, sample_indicator_data):
        """测试增加指标使用次数"""
        created = await indicator_repo.create(sample_indicator_data, commit=True)
        initial_count = created.usage_count

        success = await indicator_service.increment_usage(created.id)
        assert success is True

        # Verify usage count increased
        updated = await indicator_repo.get(created.id)
        assert updated.usage_count == initial_count + 1

    async def test_get_popular_indicators(self, indicator_service, indicator_repo, sample_indicator_data):
        """测试获取热门指标"""
        # Create indicators with different usage counts
        for i in range(3):
            data = sample_indicator_data.copy()
            data["code"] = f"IND_{i}"
            indicator = await indicator_repo.create(data, commit=True)

            # Increment usage count
            for _ in range(i + 1):
                await indicator_repo.increment_usage_count(indicator.id)

        result = await indicator_service.get_popular_indicators(limit=2)

        assert len(result["indicators"]) == 2
        # Should be ordered by usage_count desc
        assert result["indicators"][0]["usage_count"] >= result["indicators"][1]["usage_count"]

    async def test_validate_indicator_exists(self, indicator_service, indicator_repo, sample_indicator_data):
        """测试验证指标是否存在"""
        created = await indicator_repo.create(sample_indicator_data, commit=True)

        # Valid indicator
        is_valid = await indicator_service.validate_indicator_exists(created.id)
        assert is_valid is True

        # Invalid indicator
        is_valid = await indicator_service.validate_indicator_exists("nonexistent")
        assert is_valid is False

    async def test_get_indicator_categories(self, indicator_service):
        """测试获取所有指标分类"""
        categories = await indicator_service.get_indicator_categories()

        assert "categories" in categories
        assert len(categories["categories"]) > 0
        # Should include all enum values
        assert any(c["value"] == IndicatorCategory.TREND.value for c in categories["categories"])
        assert any(c["value"] == IndicatorCategory.MOMENTUM.value for c in categories["categories"])
