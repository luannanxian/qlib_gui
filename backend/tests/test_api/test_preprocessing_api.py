"""Tests for Preprocessing API endpoints.

Following TDD approach - these tests are written BEFORE implementation.
Uses proper async database fixtures and AsyncClient for testing.
All tests are async and use pytest.mark.asyncio decorator.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


class TestPreprocessingRuleAPI:
    """Test Preprocessing Rule CRUD API endpoints."""

    # ==================== CREATE Tests ====================

    @pytest.mark.asyncio
    async def test_create_rule_success(self, async_client: AsyncClient):
        """Test creating a preprocessing rule successfully."""
        response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Remove Missing Prices",
            "description": "Delete rows with missing price values",
            "rule_type": "missing_value",
            "configuration": {
                "method": "delete_rows",
                "columns": ["price", "volume"]
            },
            "is_template": True,
            "user_id": "user123"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Remove Missing Prices"
        assert data["description"] == "Delete rows with missing price values"
        assert data["rule_type"] == "missing_value"
        assert data["configuration"]["method"] == "delete_rows"
        assert data["is_template"] is True
        assert data["user_id"] == "user123"
        assert data["usage_count"] == 0
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_rule_missing_required_fields(self, async_client: AsyncClient):
        """Test creating a rule with missing required fields returns 422."""
        response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Test Rule"
        })
        assert response.status_code == 422
        data = response.json()
        # Response can be either standard Pydantic format or custom error format
        assert "detail" in data or "error_code" in data

    @pytest.mark.asyncio
    async def test_create_rule_invalid_rule_type(self, async_client: AsyncClient):
        """Test creating a rule with invalid rule_type returns 422."""
        response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Invalid Rule",
            "rule_type": "invalid_type",
            "configuration": {"method": "test"}
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_rule_empty_configuration(self, async_client: AsyncClient):
        """Test creating a rule with empty configuration returns 422."""
        response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Empty Config",
            "rule_type": "missing_value",
            "configuration": {}
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_rule_whitespace_name(self, async_client: AsyncClient):
        """Test creating a rule with whitespace-only name returns 422."""
        response = await async_client.post("/api/preprocessing/rules", json={
            "name": "   ",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_rule_duplicate_name_same_user(self, async_client: AsyncClient):
        """Test creating a rule with duplicate name for same user returns 409."""
        # Create first rule
        await async_client.post("/api/preprocessing/rules", json={
            "name": "Duplicate Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "user_id": "user123"
        })

        # Try to create duplicate
        response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Duplicate Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "mean_fill"},
            "user_id": "user123"
        })
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_rule_with_metadata(self, async_client: AsyncClient):
        """Test creating a rule with extra metadata."""
        response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Rule with Metadata",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "extra_metadata": {
                "tags": ["cleaning", "finance"],
                "affected_columns": ["price", "volume"]
            }
        })
        assert response.status_code == 201
        data = response.json()
        assert "metadata" in data
        assert data["metadata"]["tags"] == ["cleaning", "finance"]

    # ==================== READ/LIST Tests ====================

    @pytest.mark.asyncio
    async def test_list_rules_empty(self, async_client: AsyncClient):
        """Test listing rules when none exist."""
        response = await async_client.get("/api/preprocessing/rules")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        assert data["total"] == 0
        assert len(data["items"]) == 0

    @pytest.mark.asyncio
    async def test_list_rules_returns_paginated_list(self, async_client: AsyncClient):
        """Test list rules returns paginated response."""
        # Create some rules
        for i in range(3):
            await async_client.post("/api/preprocessing/rules", json={
                "name": f"Rule {i}",
                "rule_type": "missing_value",
                "configuration": {"method": "delete_rows"},
                "user_id": "user123"
            })

        response = await async_client.get("/api/preprocessing/rules")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    @pytest.mark.asyncio
    async def test_list_rules_pagination(self, async_client: AsyncClient):
        """Test pagination parameters work correctly."""
        # Create 5 rules
        for i in range(5):
            await async_client.post("/api/preprocessing/rules", json={
                "name": f"Rule {i}",
                "rule_type": "missing_value",
                "configuration": {"method": "delete_rows"}
            })

        # Test skip and limit
        response = await async_client.get("/api/preprocessing/rules?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_list_rules_filter_by_user(self, async_client: AsyncClient):
        """Test filtering rules by user_id."""
        # Create rules for different users
        await async_client.post("/api/preprocessing/rules", json={
            "name": "User1 Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "user_id": "user1"
        })
        await async_client.post("/api/preprocessing/rules", json={
            "name": "User2 Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "user_id": "user2"
        })

        response = await async_client.get("/api/preprocessing/rules?user_id=user1")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["user_id"] == "user1"

    @pytest.mark.asyncio
    async def test_list_rules_filter_by_type(self, async_client: AsyncClient):
        """Test filtering rules by rule_type."""
        await async_client.post("/api/preprocessing/rules", json={
            "name": "Missing Value Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        await async_client.post("/api/preprocessing/rules", json={
            "name": "Outlier Rule",
            "rule_type": "outlier_detection",
            "configuration": {"detection_method": "std_dev"}
        })

        response = await async_client.get("/api/preprocessing/rules?rule_type=missing_value")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["rule_type"] == "missing_value"

    @pytest.mark.asyncio
    async def test_list_rules_filter_templates_only(self, async_client: AsyncClient):
        """Test filtering to show only templates."""
        await async_client.post("/api/preprocessing/rules", json={
            "name": "Template Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "is_template": True
        })
        await async_client.post("/api/preprocessing/rules", json={
            "name": "Non-Template Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "is_template": False
        })

        response = await async_client.get("/api/preprocessing/rules?is_template=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["is_template"] is True

    @pytest.mark.asyncio
    async def test_get_rule_by_id_success(self, async_client: AsyncClient):
        """Test getting a rule by ID."""
        # Create rule
        create_response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Test Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        rule_id = create_response.json()["id"]

        # Get rule
        response = await async_client.get(f"/api/preprocessing/rules/{rule_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == rule_id
        assert data["name"] == "Test Rule"

    @pytest.mark.asyncio
    async def test_get_rule_not_found(self, async_client: AsyncClient):
        """Test getting a non-existent rule returns 404."""
        response = await async_client.get("/api/preprocessing/rules/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    # ==================== UPDATE Tests ====================

    @pytest.mark.asyncio
    async def test_update_rule_success(self, async_client: AsyncClient):
        """Test updating a rule successfully."""
        # Create rule
        create_response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Original Name",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        rule_id = create_response.json()["id"]

        # Update rule
        response = await async_client.put(f"/api/preprocessing/rules/{rule_id}", json={
            "name": "Updated Name",
            "description": "Updated description"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"
        assert data["rule_type"] == "missing_value"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_rule_not_found(self, async_client: AsyncClient):
        """Test updating a non-existent rule returns 404."""
        response = await async_client.put("/api/preprocessing/rules/nonexistent-id", json={
            "name": "Updated Name"
        })
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_rule_duplicate_name(self, async_client: AsyncClient):
        """Test updating rule to duplicate name returns 409."""
        # Create two rules
        await async_client.post("/api/preprocessing/rules", json={
            "name": "Rule 1",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "user_id": "user123"
        })
        create_response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Rule 2",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "user_id": "user123"
        })
        rule2_id = create_response.json()["id"]

        # Try to update Rule 2 to have Rule 1's name
        response = await async_client.put(f"/api/preprocessing/rules/{rule2_id}", json={
            "name": "Rule 1"
        })
        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_rule_partial_fields(self, async_client: AsyncClient):
        """Test updating only some fields."""
        # Create rule
        create_response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Original",
            "description": "Original description",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        rule_id = create_response.json()["id"]

        # Update only description
        response = await async_client.put(f"/api/preprocessing/rules/{rule_id}", json={
            "description": "New description"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Original"  # Unchanged
        assert data["description"] == "New description"  # Changed

    @pytest.mark.asyncio
    async def test_update_rule_empty_configuration(self, async_client: AsyncClient):
        """Test updating configuration to empty dict returns 422."""
        # Create rule
        create_response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Test Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        rule_id = create_response.json()["id"]

        # Try to update with empty configuration
        response = await async_client.put(f"/api/preprocessing/rules/{rule_id}", json={
            "configuration": {}
        })
        assert response.status_code == 422

    # ==================== DELETE Tests ====================

    @pytest.mark.asyncio
    async def test_delete_rule_success(self, async_client: AsyncClient):
        """Test deleting a rule successfully."""
        # Create rule
        create_response = await async_client.post("/api/preprocessing/rules", json={
            "name": "To Delete",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        rule_id = create_response.json()["id"]

        # Delete rule
        response = await async_client.delete(f"/api/preprocessing/rules/{rule_id}")
        assert response.status_code == 204

        # Verify it's deleted
        get_response = await async_client.get(f"/api/preprocessing/rules/{rule_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_rule_not_found(self, async_client: AsyncClient):
        """Test deleting a non-existent rule returns 404."""
        response = await async_client.delete("/api/preprocessing/rules/nonexistent-id")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_rule_soft_delete_default(self, async_client: AsyncClient):
        """Test soft delete is default behavior."""
        # Create rule
        create_response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Soft Delete",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        rule_id = create_response.json()["id"]

        # Delete without hard_delete flag
        response = await async_client.delete(f"/api/preprocessing/rules/{rule_id}")
        assert response.status_code == 204

        # Rule should not appear in normal list
        list_response = await async_client.get("/api/preprocessing/rules")
        assert list_response.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_delete_rule_hard_delete(self, async_client: AsyncClient):
        """Test hard delete when specified."""
        # Create rule
        create_response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Hard Delete",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        rule_id = create_response.json()["id"]

        # Hard delete
        response = await async_client.delete(f"/api/preprocessing/rules/{rule_id}?hard_delete=true")
        assert response.status_code == 204


class TestPreprocessingExecutionAPI:
    """Test Preprocessing Execution API endpoints."""

    @pytest.mark.asyncio
    async def test_execute_preprocessing_with_rule_id(self, async_client: AsyncClient):
        """Test executing preprocessing using a rule ID."""
        # Create a rule first
        rule_response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Test Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows", "columns": ["price"]}
        })
        rule_id = rule_response.json()["id"]

        # Create a dataset
        dataset_response = await async_client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = dataset_response.json()["id"]

        # Execute preprocessing
        response = await async_client.post("/api/preprocessing/execute", json={
            "dataset_id": dataset_id,
            "rule_id": rule_id,
            "output_dataset_name": "Cleaned Dataset",
            "user_id": "user123"
        })
        assert response.status_code == 201
        data = response.json()
        assert "task_id" in data
        assert data["status"] in ["pending", "running"]
        assert data["dataset_id"] == dataset_id
        assert "message" in data

    @pytest.mark.asyncio
    async def test_execute_preprocessing_with_operations(self, async_client: AsyncClient):
        """Test executing preprocessing with inline operations."""
        # Create a dataset
        dataset_response = await async_client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = dataset_response.json()["id"]

        # Execute with inline operations
        response = await async_client.post("/api/preprocessing/execute", json={
            "dataset_id": dataset_id,
            "operations": [
                {
                    "type": "missing_value",
                    "config": {"method": "delete_rows", "columns": ["price"]}
                }
            ],
            "user_id": "user123"
        })
        assert response.status_code == 201
        data = response.json()
        assert "task_id" in data

    @pytest.mark.asyncio
    async def test_execute_preprocessing_missing_dataset(self, async_client: AsyncClient):
        """Test executing preprocessing with non-existent dataset returns 404."""
        response = await async_client.post("/api/preprocessing/execute", json={
            "dataset_id": "nonexistent-dataset",
            "operations": [
                {"type": "missing_value", "config": {"method": "delete_rows"}}
            ]
        })
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_execute_preprocessing_missing_both_rule_and_operations(self, async_client: AsyncClient):
        """Test executing without rule_id or operations returns 400."""
        dataset_response = await async_client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = dataset_response.json()["id"]

        response = await async_client.post("/api/preprocessing/execute", json={
            "dataset_id": dataset_id
        })
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_execute_preprocessing_empty_operations(self, async_client: AsyncClient):
        """Test executing with empty operations list returns 422."""
        dataset_response = await async_client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = dataset_response.json()["id"]

        response = await async_client.post("/api/preprocessing/execute", json={
            "dataset_id": dataset_id,
            "operations": []
        })
        assert response.status_code == 422


class TestPreprocessingTaskAPI:
    """Test Preprocessing Task Status API endpoints."""

    @pytest.mark.asyncio
    async def test_get_task_status_success(self, async_client: AsyncClient):
        """Test getting task status by ID."""
        # Create dataset and rule
        dataset_response = await async_client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = dataset_response.json()["id"]

        rule_response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Test Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        rule_id = rule_response.json()["id"]

        # Execute preprocessing to create task
        exec_response = await async_client.post("/api/preprocessing/execute", json={
            "dataset_id": dataset_id,
            "rule_id": rule_id
        })
        task_id = exec_response.json()["task_id"]

        # Get task status
        response = await async_client.get(f"/api/preprocessing/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert "status" in data
        assert "progress_percentage" in data
        assert "total_operations" in data
        assert "completed_operations" in data

    @pytest.mark.asyncio
    async def test_get_task_status_not_found(self, async_client: AsyncClient):
        """Test getting non-existent task returns 404."""
        response = await async_client.get("/api/preprocessing/tasks/nonexistent-task")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_get_task_status_includes_error_info(self, async_client: AsyncClient):
        """Test task status includes error information when failed."""
        # This test assumes we can create a task that will fail
        # Implementation will be done in the API endpoint
        # For now, just verify the schema supports error fields
        pass


class TestPreprocessingPreviewAPI:
    """Test Preprocessing Preview API endpoints."""

    @pytest.mark.asyncio
    async def test_preview_preprocessing_success(self, async_client: AsyncClient):
        """Test previewing preprocessing results."""
        # Create a dataset
        dataset_response = await async_client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = dataset_response.json()["id"]

        # Preview preprocessing
        response = await async_client.post("/api/preprocessing/preview", json={
            "dataset_id": dataset_id,
            "operations": [
                {
                    "type": "missing_value",
                    "config": {"method": "delete_rows", "columns": ["price"]}
                }
            ],
            "preview_rows": 50
        })
        assert response.status_code == 200
        data = response.json()
        assert "original_row_count" in data
        assert "preview_row_count" in data
        assert "estimated_output_rows" in data
        assert "preview_data" in data
        assert "columns" in data
        assert "statistics" in data
        assert isinstance(data["preview_data"], list)
        assert len(data["preview_data"]) <= 50

    @pytest.mark.asyncio
    async def test_preview_preprocessing_missing_dataset(self, async_client: AsyncClient):
        """Test preview with non-existent dataset returns 404."""
        response = await async_client.post("/api/preprocessing/preview", json={
            "dataset_id": "nonexistent-dataset",
            "operations": [
                {"type": "missing_value", "config": {"method": "delete_rows"}}
            ]
        })
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_preview_preprocessing_empty_operations(self, async_client: AsyncClient):
        """Test preview with empty operations returns 422."""
        dataset_response = await async_client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = dataset_response.json()["id"]

        response = await async_client.post("/api/preprocessing/preview", json={
            "dataset_id": dataset_id,
            "operations": []
        })
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_preview_preprocessing_custom_row_limit(self, async_client: AsyncClient):
        """Test preview with custom row limit."""
        dataset_response = await async_client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = dataset_response.json()["id"]

        response = await async_client.post("/api/preprocessing/preview", json={
            "dataset_id": dataset_id,
            "operations": [
                {"type": "missing_value", "config": {"method": "delete_rows"}}
            ],
            "preview_rows": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["preview_data"]) <= 10

    @pytest.mark.asyncio
    async def test_preview_preprocessing_max_row_limit(self, async_client: AsyncClient):
        """Test preview enforces maximum row limit."""
        dataset_response = await async_client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = dataset_response.json()["id"]

        # Try to request more than max (1000)
        response = await async_client.post("/api/preprocessing/preview", json={
            "dataset_id": dataset_id,
            "operations": [
                {"type": "missing_value", "config": {"method": "delete_rows"}}
            ],
            "preview_rows": 2000
        })
        assert response.status_code == 422


class TestPreprocessingRuleAdvancedScenarios:
    """Advanced test scenarios for preprocessing rules."""

    @pytest.mark.asyncio
    async def test_create_rule_with_very_long_name(self, async_client: AsyncClient):
        """Test creating a rule with very long name."""
        long_name = "A" * 255  # Max length
        response = await async_client.post("/api/preprocessing/rules", json={
            "name": long_name,
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        assert response.status_code == 201
        assert response.json()["name"] == long_name

    @pytest.mark.asyncio
    async def test_create_rule_with_unicode_characters(self, async_client: AsyncClient):
        """Test creating a rule with Unicode characters."""
        response = await async_client.post("/api/preprocessing/rules", json={
            "name": "规则-缺失值处理-日本語-한글",
            "description": "测试 Unicode 字符 🚀",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        assert response.status_code == 201
        assert "规则" in response.json()["name"]

    @pytest.mark.asyncio
    async def test_create_rule_with_complex_nested_config(self, async_client: AsyncClient):
        """Test creating a rule with complex nested configuration."""
        response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Complex Config Rule",
            "rule_type": "transformation",
            "configuration": {
                "transformations": [
                    {
                        "column": "price",
                        "type": "normalize",
                        "params": {
                            "min": 0,
                            "max": 100,
                            "nested": {
                                "deep": {
                                    "value": "test"
                                }
                            }
                        }
                    }
                ],
                "apply_order": ["normalize", "standardize"],
                "skip_null": True
            }
        })
        assert response.status_code == 201
        config = response.json()["configuration"]
        assert "transformations" in config
        assert config["transformations"][0]["params"]["nested"]["deep"]["value"] == "test"

    @pytest.mark.asyncio
    async def test_list_rules_with_combined_filters(self, async_client: AsyncClient):
        """Test listing rules with multiple filters applied together."""
        # Create diverse rules
        for i in range(3):
            await async_client.post("/api/preprocessing/rules", json={
                "name": f"Template Rule {i}",
                "rule_type": "missing_value",
                "configuration": {"method": "delete_rows"},
                "is_template": True,
                "user_id": "user_templates"
            })
        for i in range(2):
            await async_client.post("/api/preprocessing/rules", json={
                "name": f"User Rule {i}",
                "rule_type": "outlier_detection",
                "configuration": {"detection_method": "std_dev"},
                "is_template": False,
                "user_id": "user1"
            })

        # Test combined filters
        response = await async_client.get(
            "/api/preprocessing/rules?"
            "user_id=user_templates&rule_type=missing_value&is_template=true"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert all(item["is_template"] for item in data["items"])

    @pytest.mark.asyncio
    async def test_update_rule_with_new_configuration(self, async_client: AsyncClient):
        """Test updating a rule's configuration completely."""
        # Create rule
        create_response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Original Config",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows", "columns": ["col1"]}
        })
        rule_id = create_response.json()["id"]

        # Update with new config
        response = await async_client.put(f"/api/preprocessing/rules/{rule_id}", json={
            "configuration": {
                "method": "mean_fill",
                "columns": ["col1", "col2", "col3"],
                "min_values": 0.1
            }
        })
        assert response.status_code == 200
        config = response.json()["configuration"]
        assert config["method"] == "mean_fill"
        assert len(config["columns"]) == 3

    @pytest.mark.asyncio
    async def test_list_rules_pagination_edge_cases(self, async_client: AsyncClient):
        """Test pagination with edge cases."""
        # Create exactly 10 rules
        for i in range(10):
            await async_client.post("/api/preprocessing/rules", json={
                "name": f"Rule {i:02d}",
                "rule_type": "missing_value",
                "configuration": {"method": "delete_rows"}
            })

        # Test skip beyond total count
        response = await async_client.get("/api/preprocessing/rules?skip=20&limit=10")
        assert response.status_code == 200
        assert response.json()["total"] == 10
        assert len(response.json()["items"]) == 0

        # Test with limit=1
        response = await async_client.get("/api/preprocessing/rules?skip=0&limit=1")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1

    @pytest.mark.asyncio
    async def test_rule_soft_delete_persistence(self, async_client: AsyncClient):
        """Test that soft-deleted rules don't appear in list but cannot be accessed."""
        # Create rule
        create_response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Soft Delete Test",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        rule_id = create_response.json()["id"]

        # Soft delete
        await async_client.delete(f"/api/preprocessing/rules/{rule_id}")

        # Verify not in list
        list_response = await async_client.get("/api/preprocessing/rules")
        assert list_response.json()["total"] == 0

        # Verify cannot get by ID
        get_response = await async_client.get(f"/api/preprocessing/rules/{rule_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_multiple_rules_for_same_user_different_names(self, async_client: AsyncClient):
        """Test creating multiple rules for same user with different names."""
        user_id = "multi_rule_user"
        for i in range(5):
            response = await async_client.post("/api/preprocessing/rules", json={
                "name": f"User Rule {i}",
                "rule_type": "missing_value",
                "configuration": {"method": "delete_rows"},
                "user_id": user_id
            })
            assert response.status_code == 201

        # Verify all created
        list_response = await async_client.get(f"/api/preprocessing/rules?user_id={user_id}")
        assert list_response.json()["total"] == 5

    @pytest.mark.asyncio
    async def test_rule_metadata_preservation(self, async_client: AsyncClient):
        """Test that complex metadata is preserved correctly."""
        metadata = {
            "author": "test_user",
            "version": "1.0.0",
            "tags": ["cleaning", "validation", "production"],
            "stats": {
                "rows_affected": 10000,
                "columns_affected": 5,
                "performance": {
                    "duration_ms": 1234.5,
                    "throughput": 8134.7
                }
            }
        }

        response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Metadata Test",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "extra_metadata": metadata
        })
        assert response.status_code == 201
        returned_metadata = response.json()["metadata"]
        assert returned_metadata["author"] == "test_user"
        assert returned_metadata["stats"]["performance"]["throughput"] == 8134.7

    @pytest.mark.asyncio
    async def test_update_rule_preserves_created_at(self, async_client: AsyncClient):
        """Test that updating a rule preserves the original created_at timestamp."""
        create_response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Created At Test",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        rule = create_response.json()
        original_created_at = rule["created_at"]
        rule_id = rule["id"]

        # Wait a moment
        import asyncio
        await asyncio.sleep(0.1)

        # Update rule
        update_response = await async_client.put(f"/api/preprocessing/rules/{rule_id}", json={
            "description": "Updated description"
        })
        assert update_response.status_code == 200
        updated_rule = update_response.json()
        assert updated_rule["created_at"] == original_created_at
        assert updated_rule["updated_at"] >= original_created_at


class TestPreprocessingAPIErrorHandling:
    """Test error handling in Preprocessing API endpoints."""

    # ==================== Database Error Tests ====================

    @pytest.mark.asyncio
    async def test_create_rule_database_error(self, async_client: AsyncClient):
        """Test database error handling in create rule endpoint."""
        with patch('app.database.repositories.preprocessing.PreprocessingRuleRepository.create') as mock_create:
            mock_create.side_effect = SQLAlchemyError("Database connection error")

            response = await async_client.post("/api/preprocessing/rules", json={
                "name": "Test Rule",
                "description": "Test",
                "rule_type": "missing_value",
                "configuration": {"method": "drop"}
            })
            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_rule_integrity_error(self, async_client: AsyncClient):
        """Test integrity error handling in create rule endpoint."""
        with patch('app.database.repositories.preprocessing.PreprocessingRuleRepository.create') as mock_create:
            mock_create.side_effect = IntegrityError("statement", "params", "orig")

            response = await async_client.post("/api/preprocessing/rules", json={
                "name": "Test Rule",
                "description": "Test",
                "rule_type": "missing_value",
                "configuration": {"method": "drop"}
            })
            assert response.status_code == 409
            assert "already exists" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_rule_unexpected_error(self, async_client: AsyncClient):
        """Test unexpected error handling in create rule endpoint."""
        with patch('app.database.repositories.preprocessing.PreprocessingRuleRepository.create') as mock_create:
            mock_create.side_effect = Exception("Unexpected error")

            response = await async_client.post("/api/preprocessing/rules", json={
                "name": "Test Rule",
                "description": "Test",
                "rule_type": "missing_value",
                "configuration": {"method": "drop"}
            })
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_rules_database_error(self, async_client: AsyncClient):
        """Test database error handling in list rules endpoint."""
        with patch('app.database.repositories.preprocessing.PreprocessingRuleRepository.get_multi') as mock_get:
            mock_get.side_effect = SQLAlchemyError("Database connection error")

            response = await async_client.get("/api/preprocessing/rules")
            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_rules_unexpected_error(self, async_client: AsyncClient):
        """Test unexpected error handling in list rules endpoint."""
        with patch('app.database.repositories.preprocessing.PreprocessingRuleRepository.get_multi') as mock_get:
            mock_get.side_effect = Exception("Unexpected error")

            response = await async_client.get("/api/preprocessing/rules")
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_rule_database_error(self, async_client: AsyncClient):
        """Test database error handling in get rule endpoint."""
        with patch('app.database.repositories.preprocessing.PreprocessingRuleRepository.get') as mock_get:
            mock_get.side_effect = SQLAlchemyError("Database connection error")

            response = await async_client.get("/api/preprocessing/rules/test-id")
            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_rule_unexpected_error(self, async_client: AsyncClient):
        """Test unexpected error handling in get rule endpoint."""
        with patch('app.database.repositories.preprocessing.PreprocessingRuleRepository.get') as mock_get:
            mock_get.side_effect = Exception("Unexpected error")

            response = await async_client.get("/api/preprocessing/rules/test-id")
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_rule_database_error(self, async_client: AsyncClient):
        """Test database error handling in update rule endpoint."""
        # First create a rule
        create_response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Test Rule",
            "description": "Test",
            "rule_type": "missing_value",
            "configuration": {"method": "drop"}
        })
        rule_id = create_response.json()["id"]

        # Mock update to raise error
        with patch('app.database.repositories.preprocessing.PreprocessingRuleRepository.update') as mock_update:
            mock_update.side_effect = SQLAlchemyError("Database connection error")

            response = await async_client.put(f"/api/preprocessing/rules/{rule_id}", json={
                "description": "Updated"
            })
            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_rule_integrity_error(self, async_client: AsyncClient):
        """Test integrity error handling in update rule endpoint."""
        # First create a rule
        create_response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Test Rule",
            "description": "Test",
            "rule_type": "missing_value",
            "configuration": {"method": "drop"}
        })
        rule_id = create_response.json()["id"]

        # Mock update to raise integrity error
        with patch('app.database.repositories.preprocessing.PreprocessingRuleRepository.update') as mock_update:
            mock_update.side_effect = IntegrityError("statement", "params", "orig")

            response = await async_client.put(f"/api/preprocessing/rules/{rule_id}", json={
                "description": "Updated"
            })
            assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_update_rule_unexpected_error(self, async_client: AsyncClient):
        """Test unexpected error handling in update rule endpoint."""
        # First create a rule
        create_response = await async_client.post("/api/preprocessing/rules", json={
            "name": "Test Rule",
            "description": "Test",
            "rule_type": "missing_value",
            "configuration": {"method": "drop"}
        })
        rule_id = create_response.json()["id"]

        # Mock update to raise unexpected error
        with patch('app.database.repositories.preprocessing.PreprocessingRuleRepository.update') as mock_update:
            mock_update.side_effect = Exception("Unexpected error")

            response = await async_client.put(f"/api/preprocessing/rules/{rule_id}", json={
                "description": "Updated"
            })
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_rule_database_error(self, async_client: AsyncClient):
        """Test database error handling in delete rule endpoint."""
        with patch('app.database.repositories.preprocessing.PreprocessingRuleRepository.delete') as mock_delete:
            mock_delete.side_effect = SQLAlchemyError("Database connection error")

            response = await async_client.delete("/api/preprocessing/rules/test-id")
            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_rule_unexpected_error(self, async_client: AsyncClient):
        """Test unexpected error handling in delete rule endpoint."""
        with patch('app.database.repositories.preprocessing.PreprocessingRuleRepository.delete') as mock_delete:
            mock_delete.side_effect = Exception("Unexpected error")

            response = await async_client.delete("/api/preprocessing/rules/test-id")
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    # ==================== Validation Error Tests ====================

    @pytest.mark.asyncio
    async def test_create_rule_value_error(self, async_client: AsyncClient):
        """Test value error handling in create rule endpoint."""
        with patch('app.modules.common.security.InputValidator.sanitize_name') as mock_sanitize:
            mock_sanitize.side_effect = ValueError("Invalid name format")

            response = await async_client.post("/api/preprocessing/rules", json={
                "name": "Test",
                "description": "Test",
                "rule_type": "missing_value",
                "configuration": {"method": "drop"}
            })
            assert response.status_code == 400
            assert "Invalid name format" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_rules_invalid_pagination(self, async_client: AsyncClient):
        """Test invalid pagination parameters."""
        # Test negative skip
        response = await async_client.get("/api/preprocessing/rules?skip=-1")
        assert response.status_code == 422

        # Test limit too high
        response = await async_client.get("/api/preprocessing/rules?limit=10000")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_rules_with_filters_database_error(self, async_client: AsyncClient):
        """Test database error when using filters."""
        with patch('app.database.repositories.preprocessing.PreprocessingRuleRepository.get_with_filters') as mock_get:
            mock_get.side_effect = SQLAlchemyError("Database connection error")

            response = await async_client.get("/api/preprocessing/rules?rule_type=missing_values")
            assert response.status_code == 500
            assert "Database error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_rules_count_error(self, async_client: AsyncClient):
        """Test error handling when count() fails."""
        with patch('app.database.repositories.preprocessing.PreprocessingRuleRepository.count') as mock_count:
            mock_count.side_effect = SQLAlchemyError("Count failed")

            response = await async_client.get("/api/preprocessing/rules")
            assert response.status_code == 500

    # ==================== Edge Cases ====================

    @pytest.mark.asyncio
    async def test_update_nonexistent_rule_get_error(self, async_client: AsyncClient):
        """Test updating rule where get() raises error."""
        with patch('app.database.repositories.preprocessing.PreprocessingRuleRepository.get') as mock_get:
            mock_get.side_effect = SQLAlchemyError("Get failed")

            response = await async_client.put("/api/preprocessing/rules/test-id", json={
                "description": "Updated"
            })
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_create_rule_get_by_user_and_name_error(self, async_client: AsyncClient):
        """Test creating rule when get_by_user_and_name() check fails."""
        with patch('app.database.repositories.preprocessing.PreprocessingRuleRepository.get_by_user_and_name') as mock_get:
            mock_get.side_effect = SQLAlchemyError("Get by user and name failed")

            response = await async_client.post("/api/preprocessing/rules", json={
                "name": "Test",
                "description": "Test",
                "rule_type": "missing_value",
                "configuration": {"method": "drop"},
                "user_id": "user123"
            })
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_execute_preprocessing_dataset_not_found_error(self, async_client: AsyncClient):
        """Test execute preprocessing when dataset lookup fails."""
        with patch('app.database.repositories.dataset.DatasetRepository.get') as mock_get:
            mock_get.side_effect = SQLAlchemyError("Dataset get failed")

            response = await async_client.post("/api/preprocessing/execute", json={
                "dataset_id": "test-dataset-id",
                "rule_id": "rule-id",
                "output_dataset_name": "Output Dataset"
            })
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_get_task_database_error(self, async_client: AsyncClient):
        """Test database error handling in get task endpoint."""
        with patch('app.database.repositories.preprocessing.PreprocessingTaskRepository.get') as mock_get:
            mock_get.side_effect = SQLAlchemyError("Database connection error")

            response = await async_client.get("/api/preprocessing/tasks/test-id")
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_get_task_unexpected_error(self, async_client: AsyncClient):
        """Test unexpected error handling in get task endpoint."""
        with patch('app.database.repositories.preprocessing.PreprocessingTaskRepository.get') as mock_get:
            mock_get.side_effect = Exception("Unexpected error")

            response = await async_client.get("/api/preprocessing/tasks/test-id")
            assert response.status_code == 500
