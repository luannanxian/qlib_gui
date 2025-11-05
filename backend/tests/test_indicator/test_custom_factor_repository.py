"""
Tests for CustomFactorRepository

Tests CustomFactorRepository operations with the actual CustomFactor model.
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
class TestCustomFactorRepository:
    """CustomFactorRepository测试套件"""

    async def test_create_custom_factor(self, custom_factor_repo, sample_factor_data):
        """测试创建自定义因子"""
        factor = await custom_factor_repo.create(sample_factor_data, commit=True)

        assert factor is not None
        assert factor.factor_name == "Custom Momentum"
        assert factor.user_id == "user123"
        assert factor.formula_language == "qlib_alpha"
        assert factor.status == FactorStatus.DRAFT.value
        assert factor.is_public is False

    async def test_get_user_factors(self, custom_factor_repo, sample_factor_data):
        """测试获取用户的所有因子"""
        await custom_factor_repo.create(sample_factor_data, commit=True)

        factor_data_2 = sample_factor_data.copy()
        factor_data_2["factor_name"] = "Custom RSI"
        await custom_factor_repo.create(factor_data_2, commit=True)

        factors = await custom_factor_repo.get_user_factors("user123")
        assert len(factors) == 2
        assert all(f.user_id == "user123" for f in factors)

    async def test_get_user_factors_by_status(self, custom_factor_repo, sample_factor_data):
        """测试按状态获取用户因子"""
        # Create PUBLISHED factor
        published_data = sample_factor_data.copy()
        published_data["status"] = FactorStatus.PUBLISHED.value
        await custom_factor_repo.create(published_data, commit=True)

        # Create DRAFT factor
        await custom_factor_repo.create(sample_factor_data, commit=True)

        # Get published factors
        published_factors = await custom_factor_repo.get_user_factors(
            "user123",
            status=FactorStatus.PUBLISHED.value
        )
        assert len(published_factors) == 1
        assert published_factors[0].status == FactorStatus.PUBLISHED.value

    async def test_get_public_factors(self, custom_factor_repo, sample_factor_data):
        """测试获取公开因子"""
        # Create public factor
        public_data = sample_factor_data.copy()
        public_data["is_public"] = True
        public_data["status"] = FactorStatus.PUBLISHED.value
        await custom_factor_repo.create(public_data, commit=True)

        # Create private factor
        await custom_factor_repo.create(sample_factor_data, commit=True)

        public_factors = await custom_factor_repo.get_public_factors()
        assert len(public_factors) == 1
        assert public_factors[0].is_public is True

    async def test_publish_factor(self, custom_factor_repo, sample_factor_data):
        """测试发布因子"""
        factor = await custom_factor_repo.create(sample_factor_data, commit=True)
        assert factor.status == FactorStatus.DRAFT.value

        # Publish the factor
        published = await custom_factor_repo.publish_factor(factor.id)
        assert published is not None
        assert published.status == FactorStatus.PUBLISHED.value
        assert published.published_at is not None

    async def test_make_factor_public(self, custom_factor_repo, sample_factor_data):
        """测试将因子设为公开"""
        # Must be published first
        published_data = sample_factor_data.copy()
        published_data["status"] = FactorStatus.PUBLISHED.value
        factor = await custom_factor_repo.create(published_data, commit=True)

        assert factor.is_public is False

        # Make public
        public = await custom_factor_repo.make_public(factor.id)
        assert public is not None
        assert public.is_public is True
        assert public.shared_at is not None

    async def test_make_unpublished_factor_public_fails(self, custom_factor_repo, sample_factor_data):
        """测试将未发布的因子设为公开应该失败"""
        factor = await custom_factor_repo.create(sample_factor_data, commit=True)

        # Try to make unpublished factor public (should fail)
        result = await custom_factor_repo.make_public(factor.id)
        assert result is None

    async def test_clone_factor(self, custom_factor_repo, sample_factor_data):
        """测试克隆因子"""
        original = await custom_factor_repo.create(sample_factor_data, commit=True)

        # Clone to another user
        cloned = await custom_factor_repo.clone_factor(
            factor_id=original.id,
            new_user_id="user456",
            new_factor_name="Cloned Momentum"
        )

        assert cloned is not None
        assert cloned.id != original.id
        assert cloned.factor_name == "Cloned Momentum"
        assert cloned.user_id == "user456"
        assert cloned.formula == original.formula
        assert cloned.cloned_from_id == original.id
        # Cloned factor should be draft
        assert cloned.status == FactorStatus.DRAFT.value
        assert cloned.is_public is False

    async def test_increment_usage_count(self, custom_factor_repo, sample_factor_data):
        """测试增加使用次数"""
        factor = await custom_factor_repo.create(sample_factor_data, commit=True)
        initial_count = factor.usage_count

        success = await custom_factor_repo.increment_usage_count(factor.id)
        assert success is True

        updated = await custom_factor_repo.get(factor.id)
        assert updated.usage_count == initial_count + 1

    async def test_search_by_name(self, custom_factor_repo, sample_factor_data):
        """测试按名称搜索因子"""
        await custom_factor_repo.create(sample_factor_data, commit=True)

        rsi_data = sample_factor_data.copy()
        rsi_data["factor_name"] = "Custom RSI"
        rsi_data["description"] = "Relative Strength Index indicator"  # Different description
        await custom_factor_repo.create(rsi_data, commit=True)

        # Search for "Momentum"
        results = await custom_factor_repo.search_by_name("Momentum")
        assert len(results) == 1
        assert "Momentum" in results[0].factor_name

        # Search for "Custom"
        results = await custom_factor_repo.search_by_name("Custom")
        assert len(results) == 2

    async def test_get_popular_factors(self, custom_factor_repo, sample_factor_data):
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

        # Get popular factors
        popular = await custom_factor_repo.get_popular_factors(limit=2)
        assert len(popular) == 2
        # Should be ordered by usage_count desc
        assert popular[0].usage_count >= popular[1].usage_count

    async def test_get_by_base_indicator(self, custom_factor_repo, sample_factor_data):
        """测试按基础指标获取因子"""
        # Create factor with base_indicator_id
        data_with_indicator = sample_factor_data.copy()
        data_with_indicator["base_indicator_id"] = "indicator123"
        await custom_factor_repo.create(data_with_indicator, commit=True)

        # Create factor without base_indicator_id
        await custom_factor_repo.create(sample_factor_data, commit=True)

        # Get factors by base indicator
        factors = await custom_factor_repo.get_by_base_indicator("indicator123")
        assert len(factors) == 1
        assert factors[0].base_indicator_id == "indicator123"

    async def test_soft_delete_factor(self, custom_factor_repo, sample_factor_data):
        """测试软删除因子"""
        factor = await custom_factor_repo.create(sample_factor_data, commit=True)

        # Soft delete
        await custom_factor_repo.delete(factor.id, soft=True)

        # Should not appear in regular queries
        result = await custom_factor_repo.get(factor.id)
        assert result is None

        # Should appear when including deleted
        deleted = await custom_factor_repo.get(factor.id, include_deleted=True)
        assert deleted is not None
        assert deleted.is_deleted is True
