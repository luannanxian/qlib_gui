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

    async def test_get_indicators_by_category_exception_handling(self, indicator_service, indicator_repo, monkeypatch):
        """测试get_indicators_by_category异常处理"""
        async def mock_get_by_category(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(indicator_repo, "get_by_category", mock_get_by_category)

        with pytest.raises(RuntimeError, match="Database error"):
            await indicator_service.get_indicators_by_category(IndicatorCategory.TREND.value)

    async def test_search_indicators_exception_handling(self, indicator_service, indicator_repo, monkeypatch):
        """测试search_indicators异常处理"""
        async def mock_search(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(indicator_repo, "search_by_name", mock_search)

        with pytest.raises(RuntimeError, match="Database error"):
            await indicator_service.search_indicators("test")

    async def test_get_indicator_detail_exception_handling(self, indicator_service, indicator_repo, monkeypatch):
        """测试get_indicator_detail异常处理"""
        async def mock_get(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(indicator_repo, "get", mock_get)

        with pytest.raises(RuntimeError, match="Database error"):
            await indicator_service.get_indicator_detail("indicator_id")

    async def test_increment_usage_exception_handling(self, indicator_service, indicator_repo, monkeypatch):
        """测试increment_usage异常处理"""
        async def mock_increment(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(indicator_repo, "increment_usage_count", mock_increment)

        # increment_usage catches exceptions and returns False
        result = await indicator_service.increment_usage("indicator_id")
        assert result is False

    async def test_increment_usage_repo_returns_none(self, indicator_service, indicator_repo, monkeypatch):
        """测试increment_usage当仓库返回None时"""
        async def mock_increment(*args, **kwargs):
            return None

        monkeypatch.setattr(indicator_repo, "increment_usage_count", mock_increment)

        result = await indicator_service.increment_usage("indicator_id")
        assert result is False

    async def test_get_popular_indicators_exception_handling(self, indicator_service, indicator_repo, monkeypatch):
        """测试get_popular_indicators异常处理"""
        async def mock_get_popular(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(indicator_repo, "get_popular_indicators", mock_get_popular)

        with pytest.raises(RuntimeError, match="Database error"):
            await indicator_service.get_popular_indicators()

    async def test_validate_indicator_exists_exception_handling(self, indicator_service, indicator_repo, monkeypatch):
        """测试validate_indicator_exists异常处理"""
        async def mock_get(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(indicator_repo, "get", mock_get)

        # validate_indicator_exists catches exceptions and returns False
        result = await indicator_service.validate_indicator_exists("indicator_id")
        assert result is False

    async def test_validate_indicator_disabled(self, indicator_service, indicator_repo, sample_indicator_data):
        """测试validate_indicator_exists当指标被禁用时"""
        # Create disabled indicator
        disabled_data = sample_indicator_data.copy()
        disabled_data["is_enabled"] = False
        created = await indicator_repo.create(disabled_data, commit=True)

        result = await indicator_service.validate_indicator_exists(created.id)
        assert result is False

    async def test_get_indicator_categories_exception_handling(self, indicator_service, monkeypatch):
        """测试get_indicator_categories异常处理"""
        # Mock the IndicatorCategory enum iteration to raise an exception
        def mock_iter(*args, **kwargs):
            raise RuntimeError("Enum error")

        # This is trickier - we need to mock at module level
        import app.modules.indicator.services.indicator_service as svc_module
        original_category = svc_module.IndicatorCategory

        class MockCategory:
            def __iter__(self):
                raise RuntimeError("Enum error")

        monkeypatch.setattr(svc_module, "IndicatorCategory", MockCategory())

        with pytest.raises(RuntimeError, match="Enum error"):
            await indicator_service.get_indicator_categories()

    async def test_get_all_indicators_pagination(self, indicator_service, indicator_repo, sample_indicator_data):
        """Test pagination in get_all_indicators"""
        # Create multiple indicators
        for i in range(5):
            data = sample_indicator_data.copy()
            data["code"] = f"IND_{i}"
            await indicator_repo.create(data, commit=True)

        # Get with limit
        result = await indicator_service.get_all_indicators(skip=0, limit=2)

        assert len(result["indicators"]) == 2
        assert result["skip"] == 0
        assert result["limit"] == 2
        assert result["total"] == 5

    async def test_get_all_indicators_skip_offset(self, indicator_service, indicator_repo, sample_indicator_data):
        """Test skip parameter in get_all_indicators"""
        # Create multiple indicators
        for i in range(5):
            data = sample_indicator_data.copy()
            data["code"] = f"IND_{i}"
            await indicator_repo.create(data, commit=True)

        # Get with skip
        result = await indicator_service.get_all_indicators(skip=3, limit=100)

        assert len(result["indicators"]) == 2

    async def test_search_indicators_with_pagination(self, indicator_service, indicator_repo, sample_indicator_data):
        """Test pagination in search_indicators"""
        # Create indicators with searchable names
        for i in range(3):
            data = sample_indicator_data.copy()
            data["code"] = f"SEARCH_{i}"
            data["name_zh"] = f"搜索指标_{i}"
            await indicator_repo.create(data, commit=True)

        result = await indicator_service.search_indicators("搜索", skip=0, limit=1)

        assert len(result["indicators"]) <= 1
        assert result["limit"] == 1

    async def test_increment_usage_return_type(self, indicator_service, indicator_repo, sample_indicator_data):
        """Test increment_usage returns correct type"""
        created = await indicator_repo.create(sample_indicator_data, commit=True)

        result = await indicator_service.increment_usage(created.id)

        assert isinstance(result, bool)
        assert result is True

    async def test_get_popular_indicators_with_limit(self, indicator_service, indicator_repo, sample_indicator_data):
        """Test get_popular_indicators respects limit parameter"""
        # Create indicators with different usage counts
        for i in range(5):
            data = sample_indicator_data.copy()
            data["code"] = f"POP_{i}"
            indicator = await indicator_repo.create(data, commit=True)

            # Increment usage
            for _ in range(i + 1):
                await indicator_repo.increment_usage_count(indicator.id)

        result = await indicator_service.get_popular_indicators(limit=3)

        assert len(result["indicators"]) == 3

    async def test_to_dict_includes_all_fields(self, indicator_service, indicator_repo, sample_indicator_data):
        """Test that _to_dict includes all expected fields"""
        created = await indicator_repo.create(sample_indicator_data, commit=True)

        detail = await indicator_service.get_indicator_detail(created.id)

        expected_fields = [
            "id", "code", "name_zh", "name_en", "category", "source",
            "description_zh", "description_en", "formula", "parameters",
            "default_params", "usage_count", "is_enabled", "created_at", "updated_at"
        ]

        for field in expected_fields:
            assert field in detail

    async def test_get_all_indicators_returns_dict_structure(self, indicator_service, indicator_repo, sample_indicator_data):
        """Test that get_all_indicators returns correct dict structure"""
        await indicator_repo.create(sample_indicator_data, commit=True)

        result = await indicator_service.get_all_indicators()

        assert "indicators" in result
        assert "total" in result
        assert "skip" in result
        assert "limit" in result
        assert isinstance(result["indicators"], list)

    async def test_get_indicators_by_category_returns_correct_structure(self, indicator_service, indicator_repo, sample_indicator_data):
        """Test category filtering returns correct structure"""
        await indicator_repo.create(sample_indicator_data, commit=True)

        result = await indicator_service.get_indicators_by_category(IndicatorCategory.TREND.value)

        assert "indicators" in result
        assert "total" in result
        assert "skip" in result
        assert "limit" in result

    async def test_search_indicators_returns_correct_structure(self, indicator_service, indicator_repo, sample_indicator_data):
        """Test search returns correct structure"""
        await indicator_repo.create(sample_indicator_data, commit=True)

        result = await indicator_service.search_indicators("SMA")

        assert "indicators" in result
        assert "total" in result
        assert "keyword" in result
        assert "skip" in result
        assert "limit" in result

    async def test_get_popular_indicators_returns_correct_structure(self, indicator_service, indicator_repo, sample_indicator_data):
        """Test get_popular returns correct structure"""
        await indicator_repo.create(sample_indicator_data, commit=True)

        result = await indicator_service.get_popular_indicators()

        assert "indicators" in result
        assert "total" in result

    async def test_validate_indicator_exists_with_disabled(self, indicator_service, indicator_repo, sample_indicator_data):
        """Test validation correctly handles disabled indicators"""
        disabled_data = sample_indicator_data.copy()
        disabled_data["is_enabled"] = False
        created = await indicator_repo.create(disabled_data, commit=True)

        result = await indicator_service.validate_indicator_exists(created.id)

        assert result is False

    async def test_validate_indicator_exists_with_enabled(self, indicator_service, indicator_repo, sample_indicator_data):
        """Test validation correctly handles enabled indicators"""
        enabled_data = sample_indicator_data.copy()
        enabled_data["is_enabled"] = True
        created = await indicator_repo.create(enabled_data, commit=True)

        result = await indicator_service.validate_indicator_exists(created.id)

        assert result is True

