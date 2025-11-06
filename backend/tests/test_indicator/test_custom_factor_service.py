"""
Tests for CustomFactorService

Tests business logic for custom factor operations.
"""

import pytest
import pytest_asyncio
from typing import Dict, Any

from app.database.models.indicator import FactorStatus


@pytest_asyncio.fixture
async def sample_factor_data() -> Dict[str, Any]:
    """Sample custom factor data for testing"""
    return {
        "factor_name": "Custom Momentum",
        "user_id": "user123",
        "formula": "(close - close.shift(5)) / close.shift(5)",
        "formula_language": "qlib_alpha",
        "description": "5-day momentum factor",
        "status": FactorStatus.DRAFT.value,
        "is_public": False
    }


@pytest.mark.asyncio
class TestCustomFactorService:
    """CustomFactorService测试套件"""

    async def test_create_factor(self, custom_factor_service, sample_factor_data):
        """测试创建自定义因子"""
        result = await custom_factor_service.create_factor(sample_factor_data)

        assert result is not None
        assert "factor" in result
        assert result["factor"]["factor_name"] == "Custom Momentum"
        assert result["factor"]["user_id"] == "user123"
        assert result["factor"]["status"] == FactorStatus.DRAFT.value

    async def test_get_user_factors(self, custom_factor_service, custom_factor_repo, sample_factor_data):
        """测试获取用户的所有因子"""
        await custom_factor_repo.create(sample_factor_data, commit=True)

        factor_data_2 = sample_factor_data.copy()
        factor_data_2["factor_name"] = "Custom RSI"
        await custom_factor_repo.create(factor_data_2, commit=True)

        result = await custom_factor_service.get_user_factors("user123")

        assert len(result["factors"]) == 2
        assert result["total"] == 2
        assert all(f["user_id"] == "user123" for f in result["factors"])

    async def test_get_user_factors_by_status(self, custom_factor_service, custom_factor_repo, sample_factor_data):
        """测试按状态获取用户因子"""
        # Create PUBLISHED factor
        published_data = sample_factor_data.copy()
        published_data["status"] = FactorStatus.PUBLISHED.value
        await custom_factor_repo.create(published_data, commit=True)

        # Create DRAFT factor
        await custom_factor_repo.create(sample_factor_data, commit=True)

        # Get published factors
        result = await custom_factor_service.get_user_factors(
            "user123",
            status=FactorStatus.PUBLISHED.value
        )

        assert len(result["factors"]) == 1
        assert result["factors"][0]["status"] == FactorStatus.PUBLISHED.value

    async def test_get_factor_detail(self, custom_factor_service, custom_factor_repo, sample_factor_data):
        """测试获取因子详情"""
        created = await custom_factor_repo.create(sample_factor_data, commit=True)

        detail = await custom_factor_service.get_factor_detail(created.id)

        assert detail is not None
        assert detail["id"] == created.id
        assert detail["factor_name"] == "Custom Momentum"

    async def test_get_factor_detail_not_found(self, custom_factor_service):
        """测试获取不存在的因子详情"""
        detail = await custom_factor_service.get_factor_detail("nonexistent_id")
        assert detail is None

    async def test_publish_factor(self, custom_factor_service, custom_factor_repo, sample_factor_data):
        """测试发布因子"""
        created = await custom_factor_repo.create(sample_factor_data, commit=True)

        result = await custom_factor_service.publish_factor(created.id, "user123")

        assert result is not None
        assert result["factor"]["status"] == FactorStatus.PUBLISHED.value
        assert result["factor"]["published_at"] is not None

    async def test_publish_factor_unauthorized(self, custom_factor_service, custom_factor_repo, sample_factor_data):
        """测试未授权发布因子"""
        created = await custom_factor_repo.create(sample_factor_data, commit=True)

        # Try to publish with different user
        result = await custom_factor_service.publish_factor(created.id, "other_user")

        assert result is None

    async def test_make_factor_public(self, custom_factor_service, custom_factor_repo, sample_factor_data):
        """测试将因子设为公开"""
        # Must be published first
        published_data = sample_factor_data.copy()
        published_data["status"] = FactorStatus.PUBLISHED.value
        created = await custom_factor_repo.create(published_data, commit=True)

        result = await custom_factor_service.make_public(created.id, "user123")

        assert result is not None
        assert result["factor"]["is_public"] is True
        assert result["factor"]["shared_at"] is not None

    async def test_clone_factor(self, custom_factor_service, custom_factor_repo, sample_factor_data):
        """测试克隆因子"""
        # Create public factor
        public_data = sample_factor_data.copy()
        public_data["is_public"] = True
        public_data["status"] = FactorStatus.PUBLISHED.value
        original = await custom_factor_repo.create(public_data, commit=True)

        result = await custom_factor_service.clone_factor(
            factor_id=original.id,
            new_user_id="user456",
            new_factor_name="Cloned Momentum"
        )

        assert result is not None
        assert result["factor"]["id"] != original.id
        assert result["factor"]["factor_name"] == "Cloned Momentum"
        assert result["factor"]["user_id"] == "user456"
        assert result["factor"]["cloned_from_id"] == original.id
        assert result["factor"]["status"] == FactorStatus.DRAFT.value

    async def test_clone_private_factor_fails(self, custom_factor_service, custom_factor_repo, sample_factor_data):
        """测试克隆私有因子失败"""
        original = await custom_factor_repo.create(sample_factor_data, commit=True)

        result = await custom_factor_service.clone_factor(
            factor_id=original.id,
            new_user_id="user456"
        )

        assert result is None

    async def test_search_factors(self, custom_factor_service, custom_factor_repo, sample_factor_data):
        """测试搜索因子"""
        # Create public factor
        public_data = sample_factor_data.copy()
        public_data["is_public"] = True
        public_data["status"] = FactorStatus.PUBLISHED.value
        await custom_factor_repo.create(public_data, commit=True)

        result = await custom_factor_service.search_public_factors("Momentum")

        assert len(result["factors"]) == 1
        assert "Momentum" in result["factors"][0]["factor_name"]

    async def test_get_popular_factors(self, custom_factor_service, custom_factor_repo, sample_factor_data):
        """测试获取热门因子"""
        # Create factors with different usage counts
        for i in range(3):
            data = sample_factor_data.copy()
            data["factor_name"] = f"Factor {i}"
            data["status"] = FactorStatus.PUBLISHED.value
            data["is_public"] = True
            factor = await custom_factor_repo.create(data, commit=True)

            # Increment usage count
            for _ in range(i + 1):
                await custom_factor_repo.increment_usage_count(factor.id)

        result = await custom_factor_service.get_popular_factors(limit=2)

        assert len(result["factors"]) == 2
        # Should be ordered by usage_count desc
        assert result["factors"][0]["usage_count"] >= result["factors"][1]["usage_count"]

    async def test_delete_factor(self, custom_factor_service, custom_factor_repo, sample_factor_data):
        """测试删除因子"""
        created = await custom_factor_repo.create(sample_factor_data, commit=True)

        success = await custom_factor_service.delete_factor(created.id, "user123")

        assert success is True

        # Verify soft delete
        deleted = await custom_factor_repo.get(created.id)
        assert deleted is None

    async def test_delete_factor_unauthorized(self, custom_factor_service, custom_factor_repo, sample_factor_data):
        """测试未授权删除因子"""
        created = await custom_factor_repo.create(sample_factor_data, commit=True)

        success = await custom_factor_service.delete_factor(created.id, "other_user")

        assert success is False
