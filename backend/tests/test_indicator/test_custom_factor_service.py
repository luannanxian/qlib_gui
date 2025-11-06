"""
Tests for CustomFactorService

Tests business logic for custom factor operations.
"""

import pytest
import pytest_asyncio
from typing import Dict, Any

from app.database.models.indicator import FactorStatus
from app.modules.indicator.exceptions import ValidationError, ConflictError


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
        result = await custom_factor_service.create_factor(
            factor_data=sample_factor_data,
            authenticated_user_id="user123"
        )

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

    async def test_create_factor_missing_required_fields(self, custom_factor_service):
        """测试创建因子缺少必需字段"""
        incomplete_data = {
            "factor_name": "Test Factor"
            # Missing formula and formula_language
        }

        with pytest.raises(ValidationError, match="Missing required fields"):
            await custom_factor_service.create_factor(
                factor_data=incomplete_data,
                authenticated_user_id="user123"
            )

    async def test_create_factor_invalid_language(self, custom_factor_service):
        """测试创建因子使用无效的公式语言"""
        invalid_data = {
            "factor_name": "Test Factor",
            "formula": "close / open",
            "formula_language": "invalid_language"  # Invalid
        }

        with pytest.raises(ValidationError, match="Invalid formula_language"):
            await custom_factor_service.create_factor(
                factor_data=invalid_data,
                authenticated_user_id="user123"
            )

    async def test_create_factor_authorization_enforcement(self, custom_factor_service, sample_factor_data):
        """测试创建因子时强制使用认证用户ID"""
        # Try to create factor with different user_id in data
        sample_factor_data["user_id"] = "hacker_user"

        result = await custom_factor_service.create_factor(
            factor_data=sample_factor_data,
            authenticated_user_id="legitimate_user"
        )

        # Should use authenticated_user_id, not the one from factor_data
        assert result["factor"]["user_id"] == "legitimate_user"
        assert result["factor"]["user_id"] != "hacker_user"

    async def test_create_factor_duplicate_name_conflict(self, custom_factor_service, custom_factor_repo, sample_factor_data, monkeypatch):
        """测试创建重复名称因子引发ConflictError"""
        from sqlalchemy.exc import IntegrityError

        # Mock repository create to raise IntegrityError
        async def mock_create(*args, **kwargs):
            raise IntegrityError("duplicate key", params={}, orig=Exception("UNIQUE constraint"))

        monkeypatch.setattr(custom_factor_repo, "create", mock_create)

        # Try to create factor - should raise ConflictError
        with pytest.raises(ConflictError, match="already exists"):
            await custom_factor_service.create_factor(
                factor_data=sample_factor_data,
                authenticated_user_id="user123"
            )

    async def test_get_user_factors_exception_handling(self, custom_factor_service, custom_factor_repo, monkeypatch):
        """测试get_user_factors异常处理"""
        # Mock repository to raise exception
        async def mock_get_user_factors(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(custom_factor_repo, "get_user_factors", mock_get_user_factors)

        with pytest.raises(RuntimeError, match="Database error"):
            await custom_factor_service.get_user_factors("user123")

    async def test_get_factor_detail_exception_handling(self, custom_factor_service, custom_factor_repo, monkeypatch):
        """测试get_factor_detail异常处理"""
        async def mock_get(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(custom_factor_repo, "get", mock_get)

        with pytest.raises(RuntimeError, match="Database error"):
            await custom_factor_service.get_factor_detail("factor_id")

    async def test_publish_factor_exception_handling(self, custom_factor_service, custom_factor_repo, monkeypatch, sample_factor_data):
        """测试publish_factor异常处理"""
        created = await custom_factor_repo.create(sample_factor_data, commit=True)

        async def mock_get(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(custom_factor_repo, "get", mock_get)

        with pytest.raises(RuntimeError, match="Database error"):
            await custom_factor_service.publish_factor(created.id, "user123")

    async def test_make_public_exception_handling(self, custom_factor_service, custom_factor_repo, monkeypatch):
        """测试make_public异常处理"""
        async def mock_get(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(custom_factor_repo, "get", mock_get)

        with pytest.raises(RuntimeError, match="Database error"):
            await custom_factor_service.make_public("factor_id", "user123")

    async def test_clone_factor_exception_handling(self, custom_factor_service, custom_factor_repo, monkeypatch):
        """测试clone_factor异常处理"""
        async def mock_get(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(custom_factor_repo, "get", mock_get)

        with pytest.raises(RuntimeError, match="Database error"):
            await custom_factor_service.clone_factor("factor_id", "user456")

    async def test_search_public_factors_exception_handling(self, custom_factor_service, custom_factor_repo, monkeypatch):
        """测试search_public_factors异常处理"""
        async def mock_search(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(custom_factor_repo, "search_by_name", mock_search)

        with pytest.raises(RuntimeError, match="Database error"):
            await custom_factor_service.search_public_factors("test")

    async def test_get_popular_factors_exception_handling(self, custom_factor_service, custom_factor_repo, monkeypatch):
        """测试get_popular_factors异常处理"""
        async def mock_get_popular(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(custom_factor_repo, "get_popular_factors", mock_get_popular)

        with pytest.raises(RuntimeError, match="Database error"):
            await custom_factor_service.get_popular_factors()

    async def test_delete_factor_exception_handling(self, custom_factor_service, custom_factor_repo, sample_factor_data, monkeypatch):
        """测试delete_factor异常处理"""
        # Create a factor first
        created = await custom_factor_repo.create(sample_factor_data, commit=True)

        # Mock delete to raise exception
        async def mock_delete(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(custom_factor_repo, "delete", mock_delete)

        # delete_factor catches exceptions and returns False
        result = await custom_factor_service.delete_factor(created.id, "user123")
        assert result is False

    async def test_create_factor_unexpected_exception(self, custom_factor_service, custom_factor_repo, sample_factor_data, monkeypatch):
        """测试create_factor遇到意外异常时的处理"""
        # Mock repository create to raise unexpected exception (not IntegrityError or ValidationError)
        async def mock_create(*args, **kwargs):
            raise IOError("Disk full")

        monkeypatch.setattr(custom_factor_repo, "create", mock_create)

        # Should re-raise the unexpected exception
        with pytest.raises(IOError, match="Disk full"):
            await custom_factor_service.create_factor(
                factor_data=sample_factor_data,
                authenticated_user_id="user123"
            )

    async def test_publish_factor_repo_returns_none(self, custom_factor_service, custom_factor_repo, sample_factor_data, monkeypatch):
        """测试publish_factor当仓库返回None时"""
        created = await custom_factor_repo.create(sample_factor_data, commit=True)

        # Mock publish_factor to return None
        async def mock_publish(*args, **kwargs):
            return None

        monkeypatch.setattr(custom_factor_repo, "publish_factor", mock_publish)

        result = await custom_factor_service.publish_factor(created.id, "user123")
        assert result is None

    async def test_make_public_repo_returns_none(self, custom_factor_service, custom_factor_repo, sample_factor_data, monkeypatch):
        """测试make_public当仓库返回None时"""
        # Create published factor
        published_data = sample_factor_data.copy()
        published_data["status"] = FactorStatus.PUBLISHED.value
        created = await custom_factor_repo.create(published_data, commit=True)

        # Mock make_public to return None
        async def mock_make_public(*args, **kwargs):
            return None

        monkeypatch.setattr(custom_factor_repo, "make_public", mock_make_public)

        result = await custom_factor_service.make_public(created.id, "user123")
        assert result is None

    async def test_clone_factor_repo_returns_none(self, custom_factor_service, custom_factor_repo, sample_factor_data, monkeypatch):
        """测试clone_factor当仓库返回None时"""
        # Create public factor
        public_data = sample_factor_data.copy()
        public_data["is_public"] = True
        public_data["status"] = FactorStatus.PUBLISHED.value
        created = await custom_factor_repo.create(public_data, commit=True)

        # Mock clone_factor to return None
        async def mock_clone(*args, **kwargs):
            return None

        monkeypatch.setattr(custom_factor_repo, "clone_factor", mock_clone)

        result = await custom_factor_service.clone_factor(created.id, "user456")
        assert result is None
