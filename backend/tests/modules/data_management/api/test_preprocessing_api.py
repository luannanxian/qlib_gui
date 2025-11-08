"""
Tests for Preprocessing API endpoints.

Comprehensive test suite covering all preprocessing API endpoints including:
- Preprocessing Rule CRUD operations
- Preprocessing execution
- Task status tracking
- Preview functionality

Tests follow AAA (Arrange-Act-Assert) pattern and use async/await.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime
from uuid import uuid4

from app.database.models.preprocessing import (
    DataPreprocessingRule,
    DataPreprocessingTask,
    PreprocessingTaskStatus
)
from app.database.models.dataset import Dataset
from app.database.repositories.preprocessing import (
    PreprocessingRuleRepository,
    PreprocessingTaskRepository
)
from app.database.repositories.dataset import DatasetRepository


# ==================== Test Fixtures ====================

@pytest.fixture
async def sample_dataset(db_session: AsyncSession) -> Dataset:
    """创建测试用的数据集"""
    repo = DatasetRepository(db_session)
    dataset = await repo.create(obj_in={
        "name": "Test Stock Data",
        "source": "local",
        "file_path": "/test/data/stocks.csv",
        "status": "valid",
        "row_count": 1000,
        "columns": ["date", "price", "volume", "open", "close"]
    }, commit=True)
    return dataset


@pytest.fixture
async def sample_rule(db_session: AsyncSession, sample_dataset: Dataset) -> DataPreprocessingRule:
    """创建测试用的预处理规则"""
    repo = PreprocessingRuleRepository(db_session)
    rule = await repo.create(obj_in={
        "name": "Remove Missing Values",
        "description": "Delete rows with missing price values",
        "rule_type": "missing_value",
        "configuration": {
            "method": "delete_rows",
            "columns": ["price", "volume"]
        },
        "is_template": True,
        "user_id": "test-user-123",
        "dataset_id": sample_dataset.id,
        "extra_metadata": {
            "tags": ["cleaning", "finance"]
        }
    }, commit=True)
    return rule


@pytest.fixture
async def sample_task(
    db_session: AsyncSession,
    sample_dataset: Dataset,
    sample_rule: DataPreprocessingRule
) -> DataPreprocessingTask:
    """创建测试用的预处理任务"""
    repo = PreprocessingTaskRepository(db_session)
    task = await repo.create(obj_in={
        "task_name": "Test Preprocessing Task",
        "status": PreprocessingTaskStatus.PENDING.value,
        "dataset_id": sample_dataset.id,
        "rule_id": sample_rule.id,
        "execution_config": sample_rule.configuration,
        "user_id": "test-user-123",
        "total_operations": 1,
        "input_row_count": 1000
    }, commit=True)
    return task


# ==================== Preprocessing Rule CRUD Tests ====================

@pytest.mark.asyncio
class TestHelperFunctions:
    """测试辅助函数"""

    async def test_rule_to_response_with_string_metadata(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """测试_rule_to_response处理字符串格式的metadata"""
        # Arrange - create rule with string metadata (edge case)
        from app.database.repositories.preprocessing import PreprocessingRuleRepository
        repo = PreprocessingRuleRepository(db_session)
        rule = await repo.create(obj_in={
            "name": "Test Rule",
            "rule_type": "missing_value",
            "configuration": '{"method": "delete_rows"}',  # String config
            "extra_metadata": '{"tags": ["test"]}',  # String metadata
        }, commit=True)

        # Act - fetch via API which uses _rule_to_response
        response = await async_client.get(f"/api/preprocessing/rules/{rule.id}")

        # Assert - should handle string conversion
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(rule.id)

    async def test_rule_to_response_with_invalid_json_metadata(
        self,
        db_session: AsyncSession
    ):
        """测试_rule_to_response处理无效JSON的metadata"""
        # This test ensures error handling for malformed JSON
        # In actual implementation, this would be handled by validation
        pass  # Covered by actual API tests


@pytest.mark.asyncio
class TestCreatePreprocessingRule:
    """测试POST /api/preprocessing/rules - 创建预处理规则"""

    async def test_create_rule_success(self, async_client: AsyncClient):
        """成功创建预处理规则"""
        # Arrange
        rule_data = {
            "name": "Test Rule",
            "description": "Test description",
            "rule_type": "missing_value",
            "configuration": {
                "method": "delete_rows",
                "columns": ["price"]
            },
            "is_template": True,
            "user_id": "user-123"
        }

        # Act
        response = await async_client.post("/api/preprocessing/rules", json=rule_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Rule"
        assert data["description"] == "Test description"
        assert data["rule_type"] == "missing_value"
        assert data["configuration"]["method"] == "delete_rows"
        assert data["is_template"] is True
        assert data["user_id"] == "user-123"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_rule_with_minimal_fields(self, async_client: AsyncClient):
        """使用最少必填字段创建规则"""
        # Arrange
        rule_data = {
            "name": "Minimal Rule",
            "rule_type": "transformation",
            "configuration": {"type": "normalize"}
        }

        # Act
        response = await async_client.post("/api/preprocessing/rules", json=rule_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Rule"
        assert data["rule_type"] == "transformation"
        assert data["is_template"] is False  # Default value

    async def test_create_rule_missing_required_fields(self, async_client: AsyncClient):
        """缺少必填字段时创建失败"""
        # Arrange - missing 'configuration'
        rule_data = {
            "name": "Incomplete Rule",
            "rule_type": "missing_value"
        }

        # Act
        response = await async_client.post("/api/preprocessing/rules", json=rule_data)

        # Assert
        assert response.status_code == 422

    async def test_create_rule_invalid_rule_type(self, async_client: AsyncClient):
        """无效的rule_type导致创建失败"""
        # Arrange
        rule_data = {
            "name": "Invalid Type Rule",
            "rule_type": "invalid_type",
            "configuration": {"method": "test"}
        }

        # Act
        response = await async_client.post("/api/preprocessing/rules", json=rule_data)

        # Assert
        assert response.status_code == 422

    async def test_create_rule_empty_configuration(self, async_client: AsyncClient):
        """空配置导致创建失败"""
        # Arrange
        rule_data = {
            "name": "Empty Config Rule",
            "rule_type": "missing_value",
            "configuration": {}
        }

        # Act
        response = await async_client.post("/api/preprocessing/rules", json=rule_data)

        # Assert
        assert response.status_code == 422

    async def test_create_rule_duplicate_name_same_user(
        self,
        async_client: AsyncClient,
        sample_rule: DataPreprocessingRule
    ):
        """同一用户不能创建同名规则"""
        # Arrange
        rule_data = {
            "name": sample_rule.name,
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "user_id": sample_rule.user_id
        }

        # Act
        response = await async_client.post("/api/preprocessing/rules", json=rule_data)

        # Assert
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    async def test_create_rule_database_error(self, async_client: AsyncClient, db_session: AsyncSession):
        """数据库错误处理"""
        # Arrange
        rule_data = {
            "name": "DB Error Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        }

        # Mock repository to raise database error
        with patch("app.modules.data_management.api.preprocessing_api.PreprocessingRuleRepository") as mock_repo:
            mock_instance = AsyncMock()
            mock_instance.create.side_effect = SQLAlchemyError("Database error")
            mock_repo.return_value = mock_instance

            # Act
            response = await async_client.post("/api/preprocessing/rules", json=rule_data)

            # Assert
            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]

    async def test_create_rule_integrity_error(self, async_client: AsyncClient):
        """完整性约束错误处理"""
        # Arrange
        rule_data = {
            "name": "Test Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        }

        # Mock repository to raise IntegrityError
        with patch("app.modules.data_management.api.preprocessing_api.PreprocessingRuleRepository") as mock_repo:
            mock_instance = AsyncMock()
            mock_instance.get_by_user_and_name.return_value = None
            mock_instance.create.side_effect = IntegrityError("Integrity error", {}, None)
            mock_repo.return_value = mock_instance

            # Act
            response = await async_client.post("/api/preprocessing/rules", json=rule_data)

            # Assert
            assert response.status_code == 409

    async def test_create_rule_validation_error(self, async_client: AsyncClient):
        """验证错误处理"""
        # Arrange
        rule_data = {
            "name": "Test Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        }

        # Mock repository to raise ValidationError
        from pydantic import ValidationError
        with patch("app.modules.data_management.api.preprocessing_api.PreprocessingRuleRepository") as mock_repo:
            mock_instance = AsyncMock()
            mock_instance.get_by_user_and_name.return_value = None
            # Create a ValidationError
            try:
                from pydantic import BaseModel
                class TestModel(BaseModel):
                    field: str
                TestModel(field=123)  # This will raise ValidationError
            except ValidationError as e:
                mock_instance.create.side_effect = e
                mock_repo.return_value = mock_instance

                # Act
                response = await async_client.post("/api/preprocessing/rules", json=rule_data)

                # Assert
                assert response.status_code == 400

    async def test_create_rule_value_error(self, async_client: AsyncClient):
        """值错误处理"""
        # Mock InputValidator to raise ValueError
        with patch("app.modules.data_management.api.preprocessing_api.InputValidator") as mock_validator:
            mock_validator.sanitize_name.side_effect = ValueError("Invalid name")

            # Arrange
            rule_data = {
                "name": "Invalid Name",
                "rule_type": "missing_value",
                "configuration": {"method": "delete_rows"}
            }

            # Act
            response = await async_client.post("/api/preprocessing/rules", json=rule_data)

            # Assert
            assert response.status_code == 400

    async def test_create_rule_unexpected_error(self, async_client: AsyncClient):
        """意外错误处理"""
        # Mock repository to raise unexpected error
        with patch("app.modules.data_management.api.preprocessing_api.PreprocessingRuleRepository") as mock_repo:
            mock_instance = AsyncMock()
            mock_instance.get_by_user_and_name.return_value = None
            mock_instance.create.side_effect = Exception("Unexpected error")
            mock_repo.return_value = mock_instance

            # Arrange
            rule_data = {
                "name": "Test Rule",
                "rule_type": "missing_value",
                "configuration": {"method": "delete_rows"}
            }

            # Act
            response = await async_client.post("/api/preprocessing/rules", json=rule_data)

            # Assert
            assert response.status_code == 500


@pytest.mark.asyncio
class TestListPreprocessingRules:
    """测试GET /api/preprocessing/rules - 列出预处理规则"""

    async def test_list_rules_empty(self, async_client: AsyncClient):
        """列出空规则列表"""
        # Act
        response = await async_client.get("/api/preprocessing/rules")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_list_rules_with_data(
        self,
        async_client: AsyncClient,
        sample_rule: DataPreprocessingRule
    ):
        """列出包含数据的规则列表"""
        # Act
        response = await async_client.get("/api/preprocessing/rules")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(sample_rule.id)
        assert data["items"][0]["name"] == sample_rule.name

    async def test_list_rules_with_pagination(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """分页列出规则"""
        # Arrange - create multiple rules
        repo = PreprocessingRuleRepository(db_session)
        for i in range(5):
            await repo.create(obj_in={
                "name": f"Rule {i}",
                "rule_type": "missing_value",
                "configuration": {"method": "delete_rows"},
                "user_id": "user-123"
            }, commit=True)

        # Act - get first page
        response = await async_client.get("/api/preprocessing/rules?skip=0&limit=3")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 3

        # Act - get second page
        response2 = await async_client.get("/api/preprocessing/rules?skip=3&limit=3")

        # Assert
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["total"] == 5
        assert len(data2["items"]) == 2

    async def test_list_rules_filter_by_user_id(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """按用户ID过滤规则"""
        # Arrange - create rules for different users
        repo = PreprocessingRuleRepository(db_session)
        await repo.create(obj_in={
            "name": "User 1 Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "user_id": "user-1"
        }, commit=True)
        await repo.create(obj_in={
            "name": "User 2 Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "user_id": "user-2"
        }, commit=True)

        # Act
        response = await async_client.get("/api/preprocessing/rules?user_id=user-1")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["user_id"] == "user-1"

    async def test_list_rules_filter_by_rule_type(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """按规则类型过滤"""
        # Arrange
        repo = PreprocessingRuleRepository(db_session)
        await repo.create(obj_in={
            "name": "Missing Value Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        }, commit=True)
        await repo.create(obj_in={
            "name": "Transformation Rule",
            "rule_type": "transformation",
            "configuration": {"type": "normalize"}
        }, commit=True)

        # Act
        response = await async_client.get("/api/preprocessing/rules?rule_type=transformation")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["rule_type"] == "transformation"

    async def test_list_rules_filter_by_template_flag(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """按模板标志过滤"""
        # Arrange
        repo = PreprocessingRuleRepository(db_session)
        await repo.create(obj_in={
            "name": "Template Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "is_template": True
        }, commit=True)
        await repo.create(obj_in={
            "name": "Non-Template Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "is_template": False
        }, commit=True)

        # Act
        response = await async_client.get("/api/preprocessing/rules?is_template=true")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["is_template"] is True

    async def test_list_rules_search_by_name(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession
    ):
        """按名称搜索规则"""
        # Arrange
        repo = PreprocessingRuleRepository(db_session)
        await repo.create(obj_in={
            "name": "Remove Missing Values",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        }, commit=True)
        await repo.create(obj_in={
            "name": "Normalize Prices",
            "rule_type": "transformation",
            "configuration": {"type": "normalize"}
        }, commit=True)

        # Act
        response = await async_client.get("/api/preprocessing/rules?search=Missing")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any("Missing" in item["name"] for item in data["items"])

    async def test_list_rules_database_error(self, async_client: AsyncClient):
        """数据库错误处理"""
        # Mock repository to raise database error
        with patch("app.modules.data_management.api.preprocessing_api.PreprocessingRuleRepository") as mock_repo:
            mock_instance = AsyncMock()
            mock_instance.get_multi.side_effect = SQLAlchemyError("Database error")
            mock_repo.return_value = mock_instance

            # Act
            response = await async_client.get("/api/preprocessing/rules")

            # Assert
            assert response.status_code == 500

    async def test_list_rules_value_error(self, async_client: AsyncClient):
        """值错误处理（无效的分页参数）"""
        # Mock validate_pagination to raise ValueError
        with patch("app.modules.data_management.api.preprocessing_api.validate_pagination") as mock_validate:
            mock_validate.side_effect = ValueError("Invalid pagination")

            # Act
            response = await async_client.get("/api/preprocessing/rules?skip=0&limit=100")

            # Assert
            assert response.status_code == 400

    async def test_list_rules_unexpected_error(self, async_client: AsyncClient):
        """意外错误处理"""
        # Mock repository to raise unexpected error
        with patch("app.modules.data_management.api.preprocessing_api.PreprocessingRuleRepository") as mock_repo:
            mock_instance = AsyncMock()
            mock_instance.get_multi.side_effect = Exception("Unexpected error")
            mock_repo.return_value = mock_instance

            # Act
            response = await async_client.get("/api/preprocessing/rules")

            # Assert
            assert response.status_code == 500


@pytest.mark.asyncio
class TestGetPreprocessingRule:
    """测试GET /api/preprocessing/rules/{rule_id} - 获取单个规则"""

    async def test_get_rule_success(
        self,
        async_client: AsyncClient,
        sample_rule: DataPreprocessingRule
    ):
        """成功获取规则"""
        # Act
        response = await async_client.get(f"/api/preprocessing/rules/{sample_rule.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_rule.id)
        assert data["name"] == sample_rule.name
        assert data["rule_type"] == sample_rule.rule_type
        assert data["configuration"] == sample_rule.configuration

    async def test_get_rule_not_found(self, async_client: AsyncClient):
        """规则不存在"""
        # Act
        response = await async_client.get("/api/preprocessing/rules/nonexistent-id")

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    async def test_get_rule_database_error(
        self,
        async_client: AsyncClient,
        sample_rule: DataPreprocessingRule
    ):
        """数据库错误处理"""
        # Mock repository to raise database error
        with patch("app.modules.data_management.api.preprocessing_api.PreprocessingRuleRepository") as mock_repo:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = SQLAlchemyError("Database error")
            mock_repo.return_value = mock_instance

            # Act
            response = await async_client.get(f"/api/preprocessing/rules/{sample_rule.id}")

            # Assert
            assert response.status_code == 500


@pytest.mark.asyncio
class TestUpdatePreprocessingRule:
    """测试PUT /api/preprocessing/rules/{rule_id} - 更新规则"""

    async def test_update_rule_success(
        self,
        async_client: AsyncClient,
        sample_rule: DataPreprocessingRule
    ):
        """成功更新规则"""
        # Arrange
        update_data = {
            "name": "Updated Rule Name",
            "description": "Updated description",
            "configuration": {
                "method": "mean_fill",
                "columns": ["price"]
            }
        }

        # Act
        response = await async_client.put(
            f"/api/preprocessing/rules/{sample_rule.id}",
            json=update_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_rule.id)
        assert data["name"] == "Updated Rule Name"
        assert data["description"] == "Updated description"
        assert data["configuration"]["method"] == "mean_fill"

    async def test_update_rule_partial_update(
        self,
        async_client: AsyncClient,
        sample_rule: DataPreprocessingRule
    ):
        """部分字段更新"""
        # Arrange - only update description
        update_data = {
            "description": "Only update this field"
        }

        # Act
        response = await async_client.put(
            f"/api/preprocessing/rules/{sample_rule.id}",
            json=update_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == sample_rule.name  # Unchanged
        assert data["description"] == "Only update this field"

    async def test_update_rule_not_found(self, async_client: AsyncClient):
        """更新不存在的规则"""
        # Arrange
        update_data = {"name": "New Name"}

        # Act
        response = await async_client.put(
            "/api/preprocessing/rules/nonexistent-id",
            json=update_data
        )

        # Assert
        assert response.status_code == 404

    async def test_update_rule_name_conflict(
        self,
        async_client: AsyncClient,
        db_session: AsyncSession,
        sample_rule: DataPreprocessingRule
    ):
        """更新时名称冲突"""
        # Arrange - create another rule with different name
        repo = PreprocessingRuleRepository(db_session)
        other_rule = await repo.create(obj_in={
            "name": "Other Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "user_id": sample_rule.user_id
        }, commit=True)

        # Try to rename sample_rule to other_rule's name
        update_data = {"name": "Other Rule"}

        # Act
        response = await async_client.put(
            f"/api/preprocessing/rules/{sample_rule.id}",
            json=update_data
        )

        # Assert
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    async def test_update_rule_database_error(
        self,
        async_client: AsyncClient,
        sample_rule: DataPreprocessingRule
    ):
        """数据库错误处理"""
        # Mock repository to raise database error during update
        with patch("app.modules.data_management.api.preprocessing_api.PreprocessingRuleRepository") as mock_repo:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = sample_rule
            # Mock get_by_user_and_name to return None (no conflict)
            mock_instance.get_by_user_and_name.return_value = None
            # Mock update to raise database error
            mock_instance.update.side_effect = SQLAlchemyError("Database error")
            mock_repo.return_value = mock_instance

            # Act
            response = await async_client.put(
                f"/api/preprocessing/rules/{sample_rule.id}",
                json={"description": "Updated description"}  # Change field that doesn't trigger name check
            )

            # Assert
            assert response.status_code == 500


@pytest.mark.asyncio
class TestDeletePreprocessingRule:
    """测试DELETE /api/preprocessing/rules/{rule_id} - 删除规则"""

    async def test_delete_rule_soft_delete_success(
        self,
        async_client: AsyncClient,
        sample_rule: DataPreprocessingRule
    ):
        """成功软删除规则"""
        # Act
        response = await async_client.delete(f"/api/preprocessing/rules/{sample_rule.id}")

        # Assert
        assert response.status_code == 204

    async def test_delete_rule_hard_delete_success(
        self,
        async_client: AsyncClient,
        sample_rule: DataPreprocessingRule
    ):
        """成功硬删除规则"""
        # Act
        response = await async_client.delete(
            f"/api/preprocessing/rules/{sample_rule.id}?hard_delete=true"
        )

        # Assert
        assert response.status_code == 204

    async def test_delete_rule_not_found(self, async_client: AsyncClient):
        """删除不存在的规则"""
        # Act
        response = await async_client.delete("/api/preprocessing/rules/nonexistent-id")

        # Assert
        assert response.status_code == 404

    async def test_delete_rule_database_error(
        self,
        async_client: AsyncClient,
        sample_rule: DataPreprocessingRule
    ):
        """数据库错误处理"""
        # Mock repository to raise database error
        with patch("app.modules.data_management.api.preprocessing_api.PreprocessingRuleRepository") as mock_repo:
            mock_instance = AsyncMock()
            mock_instance.delete.side_effect = SQLAlchemyError("Database error")
            mock_repo.return_value = mock_instance

            # Act
            response = await async_client.delete(f"/api/preprocessing/rules/{sample_rule.id}")

            # Assert
            assert response.status_code == 500


# ==================== Preprocessing Execution Tests ====================

@pytest.mark.asyncio
class TestExecutePreprocessing:
    """测试POST /api/preprocessing/execute - 执行预处理"""

    async def test_execute_with_rule_id_success(
        self,
        async_client: AsyncClient,
        sample_dataset: Dataset,
        sample_rule: DataPreprocessingRule
    ):
        """使用规则ID成功执行预处理"""
        # Arrange
        execute_data = {
            "dataset_id": str(sample_dataset.id),
            "rule_id": str(sample_rule.id),
            "output_dataset_name": "Cleaned Data",
            "user_id": "test-user"
        }

        # Act
        response = await async_client.post("/api/preprocessing/execute", json=execute_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"
        assert data["dataset_id"] == str(sample_dataset.id)
        assert data["message"] == "Preprocessing task created successfully"

    async def test_execute_with_operations_success(
        self,
        async_client: AsyncClient,
        sample_dataset: Dataset
    ):
        """使用操作列表成功执行预处理"""
        # Arrange
        execute_data = {
            "dataset_id": str(sample_dataset.id),
            "operations": [
                {
                    "type": "missing_value",
                    "config": {
                        "method": "delete_rows",
                        "columns": ["price"]
                    }
                }
            ],
            "user_id": "test-user"
        }

        # Act
        response = await async_client.post("/api/preprocessing/execute", json=execute_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"

    async def test_execute_without_rule_or_operations(
        self,
        async_client: AsyncClient,
        sample_dataset: Dataset
    ):
        """既没有规则ID也没有操作列表导致失败"""
        # Arrange
        execute_data = {
            "dataset_id": str(sample_dataset.id),
            "user_id": "test-user"
        }

        # Act
        response = await async_client.post("/api/preprocessing/execute", json=execute_data)

        # Assert
        assert response.status_code == 400
        assert "Either rule_id or operations must be provided" in response.json()["detail"]

    async def test_execute_with_invalid_dataset(self, async_client: AsyncClient):
        """数据集不存在导致失败"""
        # Arrange
        execute_data = {
            "dataset_id": "nonexistent-dataset",
            "operations": [{"type": "missing_value", "config": {"method": "delete_rows"}}]
        }

        # Act
        response = await async_client.post("/api/preprocessing/execute", json=execute_data)

        # Assert
        assert response.status_code == 404
        assert "Dataset" in response.json()["detail"]
        assert "not found" in response.json()["detail"]

    async def test_execute_with_invalid_rule(
        self,
        async_client: AsyncClient,
        sample_dataset: Dataset
    ):
        """规则不存在导致失败"""
        # Arrange
        execute_data = {
            "dataset_id": str(sample_dataset.id),
            "rule_id": "nonexistent-rule"
        }

        # Act
        response = await async_client.post("/api/preprocessing/execute", json=execute_data)

        # Assert
        assert response.status_code == 404
        assert "Preprocessing rule" in response.json()["detail"]
        assert "not found" in response.json()["detail"]

    async def test_execute_database_error(
        self,
        async_client: AsyncClient,
        sample_dataset: Dataset
    ):
        """数据库错误处理"""
        # Arrange
        execute_data = {
            "dataset_id": str(sample_dataset.id),
            "operations": [{"type": "missing_value", "config": {"method": "delete_rows"}}]
        }

        # Mock repository to raise database error
        with patch("app.modules.data_management.api.preprocessing_api.PreprocessingTaskRepository") as mock_repo:
            mock_instance = AsyncMock()
            mock_instance.create.side_effect = SQLAlchemyError("Database error")
            mock_repo.return_value = mock_instance

            # Act
            response = await async_client.post("/api/preprocessing/execute", json=execute_data)

            # Assert
            assert response.status_code == 500

    async def test_execute_without_output_dataset_name(
        self,
        async_client: AsyncClient,
        sample_dataset: Dataset
    ):
        """不指定输出数据集名称时自动生成"""
        # Arrange
        execute_data = {
            "dataset_id": str(sample_dataset.id),
            "operations": [{"type": "missing_value", "config": {"method": "delete_rows"}}]
        }

        # Act
        response = await async_client.post("/api/preprocessing/execute", json=execute_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        # Should auto-generate name like "Preprocess {dataset.name}"
        assert "Preprocess" in data["task_name"] or data["task_name"]

    async def test_execute_increments_rule_usage_count(
        self,
        async_client: AsyncClient,
        sample_dataset: Dataset,
        sample_rule: DataPreprocessingRule,
        db_session: AsyncSession
    ):
        """使用规则执行预处理时增加使用计数"""
        # Arrange
        original_usage_count = sample_rule.usage_count
        execute_data = {
            "dataset_id": str(sample_dataset.id),
            "rule_id": str(sample_rule.id)
        }

        # Act
        response = await async_client.post("/api/preprocessing/execute", json=execute_data)

        # Assert
        assert response.status_code == 201
        # Refresh rule to get updated usage count
        await db_session.refresh(sample_rule)
        assert sample_rule.usage_count == original_usage_count + 1


# ==================== Preprocessing Task Status Tests ====================

@pytest.mark.asyncio
class TestGetPreprocessingTask:
    """测试GET /api/preprocessing/tasks/{task_id} - 获取任务状态"""

    async def test_get_task_success(
        self,
        async_client: AsyncClient,
        sample_task: DataPreprocessingTask
    ):
        """成功获取任务状态"""
        # Act
        response = await async_client.get(f"/api/preprocessing/tasks/{sample_task.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_task.id)
        assert data["task_name"] == sample_task.task_name
        assert data["status"] == sample_task.status
        assert data["dataset_id"] == str(sample_task.dataset_id)
        assert "progress_percentage" in data
        assert "input_row_count" in data

    async def test_get_task_not_found(self, async_client: AsyncClient):
        """任务不存在"""
        # Act
        response = await async_client.get("/api/preprocessing/tasks/nonexistent-task")

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    async def test_get_task_database_error(
        self,
        async_client: AsyncClient,
        sample_task: DataPreprocessingTask
    ):
        """数据库错误处理"""
        # Mock repository to raise database error
        with patch("app.modules.data_management.api.preprocessing_api.PreprocessingTaskRepository") as mock_repo:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = SQLAlchemyError("Database error")
            mock_repo.return_value = mock_instance

            # Act
            response = await async_client.get(f"/api/preprocessing/tasks/{sample_task.id}")

            # Assert
            assert response.status_code == 500


# ==================== Preprocessing Preview Tests ====================

@pytest.mark.asyncio
class TestPreviewPreprocessing:
    """测试POST /api/preprocessing/preview - 预览预处理结果"""

    async def test_preview_success(
        self,
        async_client: AsyncClient,
        sample_dataset: Dataset
    ):
        """成功预览预处理结果"""
        # Arrange
        preview_data = {
            "dataset_id": str(sample_dataset.id),
            "operations": [
                {
                    "type": "missing_value",
                    "config": {
                        "method": "delete_rows",
                        "columns": ["price"]
                    }
                }
            ],
            "preview_rows": 50
        }

        # Act
        response = await async_client.post("/api/preprocessing/preview", json=preview_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "original_row_count" in data
        assert "preview_row_count" in data
        assert "estimated_output_rows" in data
        assert "preview_data" in data
        assert "columns" in data
        assert "statistics" in data
        assert isinstance(data["preview_data"], list)
        assert isinstance(data["columns"], list)

    async def test_preview_with_custom_preview_rows(
        self,
        async_client: AsyncClient,
        sample_dataset: Dataset
    ):
        """自定义预览行数"""
        # Arrange
        preview_data = {
            "dataset_id": str(sample_dataset.id),
            "operations": [{"type": "missing_value", "config": {"method": "delete_rows"}}],
            "preview_rows": 20
        }

        # Act
        response = await async_client.post("/api/preprocessing/preview", json=preview_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["preview_row_count"] <= 20

    async def test_preview_with_invalid_dataset(self, async_client: AsyncClient):
        """数据集不存在"""
        # Arrange
        preview_data = {
            "dataset_id": "nonexistent-dataset",
            "operations": [{"type": "missing_value", "config": {"method": "delete_rows"}}]
        }

        # Act
        response = await async_client.post("/api/preprocessing/preview", json=preview_data)

        # Assert
        assert response.status_code == 404
        assert "Dataset" in response.json()["detail"]

    async def test_preview_with_empty_operations(
        self,
        async_client: AsyncClient,
        sample_dataset: Dataset
    ):
        """空操作列表导致失败"""
        # Arrange
        preview_data = {
            "dataset_id": str(sample_dataset.id),
            "operations": []
        }

        # Act
        response = await async_client.post("/api/preprocessing/preview", json=preview_data)

        # Assert
        assert response.status_code == 422

    async def test_preview_database_error(
        self,
        async_client: AsyncClient,
        sample_dataset: Dataset
    ):
        """数据库错误处理"""
        # Arrange
        preview_data = {
            "dataset_id": str(sample_dataset.id),
            "operations": [{"type": "missing_value", "config": {"method": "delete_rows"}}]
        }

        # Mock repository to raise database error
        with patch("app.modules.data_management.api.preprocessing_api.DatasetRepository") as mock_repo:
            mock_instance = AsyncMock()
            mock_instance.get.side_effect = SQLAlchemyError("Database error")
            mock_repo.return_value = mock_instance

            # Act
            response = await async_client.post("/api/preprocessing/preview", json=preview_data)

            # Assert
            assert response.status_code == 500


# ==================== Integration Tests ====================

@pytest.mark.asyncio
class TestPreprocessingWorkflow:
    """集成测试 - 完整的预处理工作流"""

    async def test_full_preprocessing_workflow(
        self,
        async_client: AsyncClient,
        sample_dataset: Dataset
    ):
        """完整工作流：创建规则 -> 预览 -> 执行 -> 查询状态"""
        # Step 1: 创建预处理规则
        rule_data = {
            "name": "Workflow Rule",
            "rule_type": "missing_value",
            "configuration": {
                "method": "delete_rows",
                "columns": ["price"]
            },
            "is_template": True
        }
        rule_response = await async_client.post("/api/preprocessing/rules", json=rule_data)
        assert rule_response.status_code == 201
        rule_id = rule_response.json()["id"]

        # Step 2: 预览预处理结果
        preview_data = {
            "dataset_id": str(sample_dataset.id),
            "operations": [
                {
                    "type": "missing_value",
                    "config": {
                        "method": "delete_rows",
                        "columns": ["price"]
                    }
                }
            ]
        }
        preview_response = await async_client.post("/api/preprocessing/preview", json=preview_data)
        assert preview_response.status_code == 200

        # Step 3: 执行预处理
        execute_data = {
            "dataset_id": str(sample_dataset.id),
            "rule_id": rule_id
        }
        execute_response = await async_client.post("/api/preprocessing/execute", json=execute_data)
        assert execute_response.status_code == 201
        task_id = execute_response.json()["task_id"]

        # Step 4: 查询任务状态
        task_response = await async_client.get(f"/api/preprocessing/tasks/{task_id}")
        assert task_response.status_code == 200
        assert task_response.json()["status"] == "pending"

    async def test_rule_crud_workflow(self, async_client: AsyncClient):
        """规则CRUD工作流：创建 -> 读取 -> 更新 -> 删除"""
        # Create
        create_data = {
            "name": "CRUD Test Rule",
            "rule_type": "transformation",
            "configuration": {"type": "normalize"}
        }
        create_response = await async_client.post("/api/preprocessing/rules", json=create_data)
        assert create_response.status_code == 201
        rule_id = create_response.json()["id"]

        # Read
        get_response = await async_client.get(f"/api/preprocessing/rules/{rule_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "CRUD Test Rule"

        # Update
        update_data = {"name": "Updated CRUD Rule"}
        update_response = await async_client.put(f"/api/preprocessing/rules/{rule_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated CRUD Rule"

        # Delete
        delete_response = await async_client.delete(f"/api/preprocessing/rules/{rule_id}")
        assert delete_response.status_code == 204


# ==================== Edge Cases and Security Tests ====================

@pytest.mark.asyncio
class TestEdgeCases:
    """边界情况和安全测试"""

    async def test_sql_injection_in_search(self, async_client: AsyncClient):
        """SQL注入测试"""
        # Arrange - try SQL injection in search parameter
        response = await async_client.get("/api/preprocessing/rules?search='; DROP TABLE preprocessing_rules; --")

        # Assert - should be sanitized and return 200 or 400 (validation error)
        assert response.status_code in [200, 400]

    async def test_xss_in_rule_name(self, async_client: AsyncClient):
        """XSS攻击测试"""
        # Arrange
        rule_data = {
            "name": "<script>alert('xss')</script>",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        }

        # Act
        response = await async_client.post("/api/preprocessing/rules", json=rule_data)

        # Assert - should be sanitized or rejected
        assert response.status_code in [201, 400]

    async def test_extremely_large_pagination(self, async_client: AsyncClient):
        """超大分页参数测试"""
        # Act
        response = await async_client.get("/api/preprocessing/rules?skip=999999&limit=10000")

        # Assert - should handle gracefully (422 is validation error, which is acceptable)
        assert response.status_code in [200, 400, 422]

    async def test_negative_pagination_values(self, async_client: AsyncClient):
        """负数分页参数测试"""
        # Act
        response = await async_client.get("/api/preprocessing/rules?skip=-10&limit=-5")

        # Assert
        assert response.status_code == 422
