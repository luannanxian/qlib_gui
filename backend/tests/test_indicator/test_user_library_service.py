"""
Tests for UserLibraryService

Tests business logic for user factor library operations.
"""

import pytest
import pytest_asyncio
from typing import Dict, Any

from app.database.models.indicator import FactorStatus


@pytest_asyncio.fixture
async def sample_library_data() -> Dict[str, Any]:
    """Sample user library data for testing"""
    return {
        "user_id": "user123",
        "factor_id": "factor_001",
        "is_favorite": False
    }


@pytest.mark.asyncio
class TestUserLibraryService:
    """UserLibraryService测试套件"""

    async def test_get_user_library(self, user_library_service, user_library_repo, sample_library_data):
        """测试获取用户的库项目"""
        # Create library entries
        await user_library_repo.create(sample_library_data, commit=True)

        library_data_2 = sample_library_data.copy()
        library_data_2["factor_id"] = "factor_002"
        await user_library_repo.create(library_data_2, commit=True)

        result = await user_library_service.get_user_library("user123")

        assert len(result["items"]) == 2
        assert result["total"] == 2
        assert all(item["user_id"] == "user123" for item in result["items"])

    async def test_get_user_library_with_pagination(self, user_library_service, user_library_repo, sample_library_data):
        """测试分页获取用户库"""
        # Create 5 library entries
        for i in range(5):
            data = sample_library_data.copy()
            data["factor_id"] = f"factor_{i:03d}"
            await user_library_repo.create(data, commit=True)

        result = await user_library_service.get_user_library(
            "user123",
            skip=2,
            limit=2
        )

        assert len(result["items"]) == 2
        assert result["skip"] == 2
        assert result["limit"] == 2

    async def test_add_to_library(self, user_library_service, custom_factor_repo):
        """测试添加因子到库"""
        # Create a factor first
        factor_data = {
            "factor_name": "Test Factor",
            "user_id": "user123",
            "formula": "close / open",
            "formula_language": "qlib_alpha",
            "status": FactorStatus.PUBLISHED.value,
            "is_public": True
        }
        factor = await custom_factor_repo.create(factor_data, commit=True)

        result = await user_library_service.add_to_library(
            user_id="user456",
            factor_id=factor.id
        )

        assert result is not None
        assert result["item"]["user_id"] == "user456"
        assert result["item"]["factor_id"] == factor.id
        assert result["item"]["is_favorite"] is False

    async def test_add_duplicate_to_library(self, user_library_service, user_library_repo, custom_factor_repo, sample_library_data):
        """测试重复添加因子到库"""
        # Create a factor
        factor_data = {
            "factor_name": "Test Factor",
            "user_id": "user123",
            "formula": "close / open",
            "formula_language": "qlib_alpha",
            "status": FactorStatus.PUBLISHED.value,
            "is_public": True
        }
        factor = await custom_factor_repo.create(factor_data, commit=True)

        # Add to library
        library_data = sample_library_data.copy()
        library_data["factor_id"] = factor.id
        await user_library_repo.create(library_data, commit=True)

        # Try to add again
        result = await user_library_service.add_to_library(
            user_id="user123",
            factor_id=factor.id
        )

        # Should return existing entry
        assert result is not None
        assert result["item"]["user_id"] == "user123"

    async def test_toggle_favorite(self, user_library_service, user_library_repo, sample_library_data):
        """测试切换收藏状态"""
        created = await user_library_repo.create(sample_library_data, commit=True)
        assert created.is_favorite is False

        # Toggle to favorite
        result = await user_library_service.toggle_favorite(
            user_id="user123",
            factor_id="factor_001",
            is_favorite=True
        )

        assert result is not None
        assert result["item"]["is_favorite"] is True

        # Toggle back
        result = await user_library_service.toggle_favorite(
            user_id="user123",
            factor_id="factor_001",
            is_favorite=False
        )

        assert result is not None
        assert result["item"]["is_favorite"] is False

    async def test_toggle_favorite_unauthorized(self, user_library_service, user_library_repo, sample_library_data):
        """测试未授权切换收藏"""
        await user_library_repo.create(sample_library_data, commit=True)

        # Try to toggle with different user
        result = await user_library_service.toggle_favorite(
            user_id="other_user",
            factor_id="factor_001",
            is_favorite=True
        )

        assert result is None

    async def test_increment_library_usage(self, user_library_service, user_library_repo, sample_library_data):
        """测试增加库项目使用次数"""
        created = await user_library_repo.create(sample_library_data, commit=True)
        initial_count = created.usage_count

        success = await user_library_service.increment_usage(
            user_id="user123",
            factor_id="factor_001"
        )

        assert success is True

        # Verify usage count increased
        updated = await user_library_repo.find_library_item("user123", factor_id="factor_001")
        assert updated.usage_count == initial_count + 1

    async def test_get_favorites(self, user_library_service, user_library_repo, sample_library_data):
        """测试获取收藏项"""
        # Create favorite item
        favorite_data = sample_library_data.copy()
        favorite_data["is_favorite"] = True
        await user_library_repo.create(favorite_data, commit=True)

        # Create non-favorite item
        non_favorite_data = sample_library_data.copy()
        non_favorite_data["factor_id"] = "factor_002"
        await user_library_repo.create(non_favorite_data, commit=True)

        result = await user_library_service.get_favorites("user123")

        assert len(result["items"]) == 1
        assert result["items"][0]["is_favorite"] is True
        assert result["items"][0]["factor_id"] == "factor_001"

    async def test_get_most_used(self, user_library_service, user_library_repo, sample_library_data):
        """测试获取最常用项"""
        # Create items with different usage counts
        for i in range(3):
            data = sample_library_data.copy()
            data["factor_id"] = f"factor_{i:03d}"
            item = await user_library_repo.create(data, commit=True)

            # Increment usage count
            for _ in range(i + 1):
                await user_library_repo.increment_usage_count(item.id)

        result = await user_library_service.get_most_used(
            user_id="user123",
            limit=2
        )

        assert len(result["items"]) == 2
        # Should be ordered by usage_count desc
        assert result["items"][0]["usage_count"] >= result["items"][1]["usage_count"]

    async def test_remove_from_library(self, user_library_service, user_library_repo, sample_library_data):
        """测试从库中移除项目"""
        created = await user_library_repo.create(sample_library_data, commit=True)

        success = await user_library_service.remove_from_library(
            user_id="user123",
            factor_id="factor_001"
        )

        assert success is True

        # Verify removed
        removed = await user_library_repo.find_library_item("user123", factor_id="factor_001")
        assert removed is None

    async def test_remove_from_library_unauthorized(self, user_library_service, user_library_repo, sample_library_data):
        """测试未授权移除库项目"""
        await user_library_repo.create(sample_library_data, commit=True)

        success = await user_library_service.remove_from_library(
            user_id="other_user",
            factor_id="factor_001"
        )

        assert success is False

    async def test_get_library_stats(self, user_library_service, user_library_repo, sample_library_data):
        """测试获取库统计信息"""
        # Create library items
        for i in range(5):
            data = sample_library_data.copy()
            data["factor_id"] = f"factor_{i:03d}"
            data["is_favorite"] = i < 2  # First 2 are favorites
            await user_library_repo.create(data, commit=True)

        result = await user_library_service.get_library_stats("user123")

        assert result["total_items"] == 5
        assert result["favorite_count"] == 2
        assert result["user_id"] == "user123"

    async def test_get_user_library_exception_handling(self, user_library_service, user_library_repo, monkeypatch):
        """测试get_user_library异常处理"""
        async def mock_get_user_library(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(user_library_repo, "get_user_library", mock_get_user_library)

        with pytest.raises(RuntimeError, match="Database error"):
            await user_library_service.get_user_library("user123")

    async def test_add_to_library_exception_handling(self, user_library_service, user_library_repo, monkeypatch):
        """测试add_to_library异常处理"""
        async def mock_add_to_library(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(user_library_repo, "add_to_library", mock_add_to_library)

        with pytest.raises(RuntimeError, match="Database error"):
            await user_library_service.add_to_library("user123", "factor_001")

    async def test_add_to_library_returns_none(self, user_library_service, user_library_repo, monkeypatch):
        """测试add_to_library当仓库返回None时"""
        async def mock_add_to_library(*args, **kwargs):
            return None

        monkeypatch.setattr(user_library_repo, "add_to_library", mock_add_to_library)

        with pytest.raises(ValueError, match="Failed to add item to library"):
            await user_library_service.add_to_library("user123", "factor_001")

    async def test_toggle_favorite_exception_handling(self, user_library_service, user_library_repo, monkeypatch):
        """测试toggle_favorite异常处理"""
        async def mock_find(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(user_library_repo, "find_library_item", mock_find)

        with pytest.raises(RuntimeError, match="Database error"):
            await user_library_service.toggle_favorite("user123", "factor_001", True)

    async def test_toggle_favorite_update_returns_none(self, user_library_service, user_library_repo, sample_library_data, monkeypatch):
        """测试toggle_favorite当update返回None时"""
        created = await user_library_repo.create(sample_library_data, commit=True)

        # Mock update to return None
        async def mock_update(*args, **kwargs):
            return None

        monkeypatch.setattr(user_library_repo, "update", mock_update)

        result = await user_library_service.toggle_favorite("user123", "factor_001", True)
        assert result is None

    async def test_increment_usage_item_not_found(self, user_library_service):
        """测试increment_usage当项目不存在时"""
        result = await user_library_service.increment_usage("user123", "nonexistent_factor")
        assert result is False

    async def test_increment_usage_exception_handling(self, user_library_service, user_library_repo, sample_library_data, monkeypatch):
        """测试increment_usage异常处理"""
        await user_library_repo.create(sample_library_data, commit=True)

        async def mock_increment(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(user_library_repo, "increment_usage_count", mock_increment)

        result = await user_library_service.increment_usage("user123", "factor_001")
        assert result is False

    async def test_get_favorites_exception_handling(self, user_library_service, user_library_repo, monkeypatch):
        """测试get_favorites异常处理"""
        async def mock_get_favorites(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(user_library_repo, "get_favorites", mock_get_favorites)

        with pytest.raises(RuntimeError, match="Database error"):
            await user_library_service.get_favorites("user123")

    async def test_get_most_used_exception_handling(self, user_library_service, user_library_repo, monkeypatch):
        """测试get_most_used异常处理"""
        async def mock_get_most_used(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(user_library_repo, "get_most_used", mock_get_most_used)

        with pytest.raises(RuntimeError, match="Database error"):
            await user_library_service.get_most_used("user123")

    async def test_remove_from_library_item_not_found(self, user_library_service):
        """测试remove_from_library当项目不存在时"""
        result = await user_library_service.remove_from_library("user123", "nonexistent_factor")
        assert result is False

    async def test_remove_from_library_exception_handling(self, user_library_service, user_library_repo, sample_library_data, monkeypatch):
        """测试remove_from_library异常处理"""
        await user_library_repo.create(sample_library_data, commit=True)

        async def mock_delete(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(user_library_repo, "delete", mock_delete)

        result = await user_library_service.remove_from_library("user123", "factor_001")
        assert result is False

    async def test_get_library_stats_exception_handling(self, user_library_service, user_library_repo, monkeypatch):
        """测试get_library_stats异常处理"""
        async def mock_get_user_library(*args, **kwargs):
            raise RuntimeError("Database error")

        monkeypatch.setattr(user_library_repo, "get_user_library", mock_get_user_library)

        with pytest.raises(RuntimeError, match="Database error"):
            await user_library_service.get_library_stats("user123")

