"""Tests for Preprocessing API endpoints.

Following TDD approach - these tests are written BEFORE implementation.
Tests cover all CRUD operations, validation, error handling, and pagination.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestPreprocessingRuleAPI:
    """Test Preprocessing Rule CRUD API endpoints."""

    # ==================== CREATE Tests ====================

    def test_create_rule_success(self, client):
        """Test creating a preprocessing rule successfully."""
        response = client.post("/api/preprocessing/rules", json={
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

    def test_create_rule_missing_required_fields(self, client):
        """Test creating a rule with missing required fields returns 422."""
        response = client.post("/api/preprocessing/rules", json={
            "name": "Test Rule"
        })
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_create_rule_invalid_rule_type(self, client):
        """Test creating a rule with invalid rule_type returns 422."""
        response = client.post("/api/preprocessing/rules", json={
            "name": "Invalid Rule",
            "rule_type": "invalid_type",
            "configuration": {"method": "test"}
        })
        assert response.status_code == 422

    def test_create_rule_empty_configuration(self, client):
        """Test creating a rule with empty configuration returns 422."""
        response = client.post("/api/preprocessing/rules", json={
            "name": "Empty Config",
            "rule_type": "missing_value",
            "configuration": {}
        })
        assert response.status_code == 422

    def test_create_rule_whitespace_name(self, client):
        """Test creating a rule with whitespace-only name returns 422."""
        response = client.post("/api/preprocessing/rules", json={
            "name": "   ",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        assert response.status_code == 422

    def test_create_rule_duplicate_name_same_user(self, client):
        """Test creating a rule with duplicate name for same user returns 409."""
        # Create first rule
        client.post("/api/preprocessing/rules", json={
            "name": "Duplicate Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "user_id": "user123"
        })

        # Try to create duplicate
        response = client.post("/api/preprocessing/rules", json={
            "name": "Duplicate Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "mean_fill"},
            "user_id": "user123"
        })
        assert response.status_code == 409
        data = response.json()
        assert "detail" in data
        assert "already exists" in data["detail"].lower()

    def test_create_rule_with_metadata(self, client):
        """Test creating a rule with extra metadata."""
        response = client.post("/api/preprocessing/rules", json={
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

    def test_list_rules_empty(self, client):
        """Test listing rules when none exist."""
        response = client.get("/api/preprocessing/rules")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_list_rules_returns_paginated_list(self, client):
        """Test list rules returns paginated response."""
        # Create some rules
        for i in range(3):
            client.post("/api/preprocessing/rules", json={
                "name": f"Rule {i}",
                "rule_type": "missing_value",
                "configuration": {"method": "delete_rows"},
                "user_id": "user123"
            })

        response = client.get("/api/preprocessing/rules")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_rules_pagination(self, client):
        """Test pagination parameters work correctly."""
        # Create 5 rules
        for i in range(5):
            client.post("/api/preprocessing/rules", json={
                "name": f"Rule {i}",
                "rule_type": "missing_value",
                "configuration": {"method": "delete_rows"}
            })

        # Test skip and limit
        response = client.get("/api/preprocessing/rules?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

    def test_list_rules_filter_by_user(self, client):
        """Test filtering rules by user_id."""
        # Create rules for different users
        client.post("/api/preprocessing/rules", json={
            "name": "User1 Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "user_id": "user1"
        })
        client.post("/api/preprocessing/rules", json={
            "name": "User2 Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "user_id": "user2"
        })

        response = client.get("/api/preprocessing/rules?user_id=user1")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["user_id"] == "user1"

    def test_list_rules_filter_by_type(self, client):
        """Test filtering rules by rule_type."""
        client.post("/api/preprocessing/rules", json={
            "name": "Missing Value Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        client.post("/api/preprocessing/rules", json={
            "name": "Outlier Rule",
            "rule_type": "outlier_detection",
            "configuration": {"detection_method": "std_dev"}
        })

        response = client.get("/api/preprocessing/rules?rule_type=missing_value")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["rule_type"] == "missing_value"

    def test_list_rules_filter_templates_only(self, client):
        """Test filtering to show only templates."""
        client.post("/api/preprocessing/rules", json={
            "name": "Template Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "is_template": True
        })
        client.post("/api/preprocessing/rules", json={
            "name": "Non-Template Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "is_template": False
        })

        response = client.get("/api/preprocessing/rules?is_template=true")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["is_template"] is True

    def test_get_rule_by_id_success(self, client):
        """Test getting a rule by ID."""
        # Create rule
        create_response = client.post("/api/preprocessing/rules", json={
            "name": "Test Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        rule_id = create_response.json()["id"]

        # Get rule
        response = client.get(f"/api/preprocessing/rules/{rule_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == rule_id
        assert data["name"] == "Test Rule"

    def test_get_rule_not_found(self, client):
        """Test getting a non-existent rule returns 404."""
        response = client.get("/api/preprocessing/rules/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    # ==================== UPDATE Tests ====================

    def test_update_rule_success(self, client):
        """Test updating a rule successfully."""
        # Create rule
        create_response = client.post("/api/preprocessing/rules", json={
            "name": "Original Name",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        rule_id = create_response.json()["id"]

        # Update rule
        response = client.put(f"/api/preprocessing/rules/{rule_id}", json={
            "name": "Updated Name",
            "description": "Updated description"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"
        assert data["rule_type"] == "missing_value"  # Unchanged

    def test_update_rule_not_found(self, client):
        """Test updating a non-existent rule returns 404."""
        response = client.put("/api/preprocessing/rules/nonexistent-id", json={
            "name": "Updated Name"
        })
        assert response.status_code == 404

    def test_update_rule_duplicate_name(self, client):
        """Test updating rule to duplicate name returns 409."""
        # Create two rules
        client.post("/api/preprocessing/rules", json={
            "name": "Rule 1",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "user_id": "user123"
        })
        create_response = client.post("/api/preprocessing/rules", json={
            "name": "Rule 2",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"},
            "user_id": "user123"
        })
        rule2_id = create_response.json()["id"]

        # Try to update Rule 2 to have Rule 1's name
        response = client.put(f"/api/preprocessing/rules/{rule2_id}", json={
            "name": "Rule 1"
        })
        assert response.status_code == 409

    def test_update_rule_partial_fields(self, client):
        """Test updating only some fields."""
        # Create rule
        create_response = client.post("/api/preprocessing/rules", json={
            "name": "Original",
            "description": "Original description",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        rule_id = create_response.json()["id"]

        # Update only description
        response = client.put(f"/api/preprocessing/rules/{rule_id}", json={
            "description": "New description"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Original"  # Unchanged
        assert data["description"] == "New description"  # Changed

    def test_update_rule_empty_configuration(self, client):
        """Test updating configuration to empty dict returns 422."""
        # Create rule
        create_response = client.post("/api/preprocessing/rules", json={
            "name": "Test Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        rule_id = create_response.json()["id"]

        # Try to update with empty configuration
        response = client.put(f"/api/preprocessing/rules/{rule_id}", json={
            "configuration": {}
        })
        assert response.status_code == 422

    # ==================== DELETE Tests ====================

    def test_delete_rule_success(self, client):
        """Test deleting a rule successfully."""
        # Create rule
        create_response = client.post("/api/preprocessing/rules", json={
            "name": "To Delete",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        rule_id = create_response.json()["id"]

        # Delete rule
        response = client.delete(f"/api/preprocessing/rules/{rule_id}")
        assert response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/api/preprocessing/rules/{rule_id}")
        assert get_response.status_code == 404

    def test_delete_rule_not_found(self, client):
        """Test deleting a non-existent rule returns 404."""
        response = client.delete("/api/preprocessing/rules/nonexistent-id")
        assert response.status_code == 404

    def test_delete_rule_soft_delete_default(self, client):
        """Test soft delete is default behavior."""
        # Create rule
        create_response = client.post("/api/preprocessing/rules", json={
            "name": "Soft Delete",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        rule_id = create_response.json()["id"]

        # Delete without hard_delete flag
        response = client.delete(f"/api/preprocessing/rules/{rule_id}")
        assert response.status_code == 204

        # Rule should not appear in normal list
        list_response = client.get("/api/preprocessing/rules")
        assert list_response.json()["total"] == 0

    def test_delete_rule_hard_delete(self, client):
        """Test hard delete when specified."""
        # Create rule
        create_response = client.post("/api/preprocessing/rules", json={
            "name": "Hard Delete",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        rule_id = create_response.json()["id"]

        # Hard delete
        response = client.delete(f"/api/preprocessing/rules/{rule_id}?hard_delete=true")
        assert response.status_code == 204


class TestPreprocessingExecutionAPI:
    """Test Preprocessing Execution API endpoints."""

    def test_execute_preprocessing_with_rule_id(self, client):
        """Test executing preprocessing using a rule ID."""
        # Create a rule first
        rule_response = client.post("/api/preprocessing/rules", json={
            "name": "Test Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows", "columns": ["price"]}
        })
        rule_id = rule_response.json()["id"]

        # Create a dataset
        dataset_response = client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = dataset_response.json()["id"]

        # Execute preprocessing
        response = client.post("/api/preprocessing/execute", json={
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

    def test_execute_preprocessing_with_operations(self, client):
        """Test executing preprocessing with inline operations."""
        # Create a dataset
        dataset_response = client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = dataset_response.json()["id"]

        # Execute with inline operations
        response = client.post("/api/preprocessing/execute", json={
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

    def test_execute_preprocessing_missing_dataset(self, client):
        """Test executing preprocessing with non-existent dataset returns 404."""
        response = client.post("/api/preprocessing/execute", json={
            "dataset_id": "nonexistent-dataset",
            "operations": [
                {"type": "missing_value", "config": {"method": "delete_rows"}}
            ]
        })
        assert response.status_code == 404

    def test_execute_preprocessing_missing_both_rule_and_operations(self, client):
        """Test executing without rule_id or operations returns 400."""
        dataset_response = client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = dataset_response.json()["id"]

        response = client.post("/api/preprocessing/execute", json={
            "dataset_id": dataset_id
        })
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_execute_preprocessing_empty_operations(self, client):
        """Test executing with empty operations list returns 422."""
        dataset_response = client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = dataset_response.json()["id"]

        response = client.post("/api/preprocessing/execute", json={
            "dataset_id": dataset_id,
            "operations": []
        })
        assert response.status_code == 422


class TestPreprocessingTaskAPI:
    """Test Preprocessing Task Status API endpoints."""

    def test_get_task_status_success(self, client):
        """Test getting task status by ID."""
        # Create dataset and rule
        dataset_response = client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = dataset_response.json()["id"]

        rule_response = client.post("/api/preprocessing/rules", json={
            "name": "Test Rule",
            "rule_type": "missing_value",
            "configuration": {"method": "delete_rows"}
        })
        rule_id = rule_response.json()["id"]

        # Execute preprocessing to create task
        exec_response = client.post("/api/preprocessing/execute", json={
            "dataset_id": dataset_id,
            "rule_id": rule_id
        })
        task_id = exec_response.json()["task_id"]

        # Get task status
        response = client.get(f"/api/preprocessing/tasks/{task_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert "status" in data
        assert "progress_percentage" in data
        assert "total_operations" in data
        assert "completed_operations" in data

    def test_get_task_status_not_found(self, client):
        """Test getting non-existent task returns 404."""
        response = client.get("/api/preprocessing/tasks/nonexistent-task")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_get_task_status_includes_error_info(self, client):
        """Test task status includes error information when failed."""
        # This test assumes we can create a task that will fail
        # Implementation will be done in the API endpoint
        # For now, just verify the schema supports error fields
        pass


class TestPreprocessingPreviewAPI:
    """Test Preprocessing Preview API endpoints."""

    def test_preview_preprocessing_success(self, client):
        """Test previewing preprocessing results."""
        # Create a dataset
        dataset_response = client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = dataset_response.json()["id"]

        # Preview preprocessing
        response = client.post("/api/preprocessing/preview", json={
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

    def test_preview_preprocessing_missing_dataset(self, client):
        """Test preview with non-existent dataset returns 404."""
        response = client.post("/api/preprocessing/preview", json={
            "dataset_id": "nonexistent-dataset",
            "operations": [
                {"type": "missing_value", "config": {"method": "delete_rows"}}
            ]
        })
        assert response.status_code == 404

    def test_preview_preprocessing_empty_operations(self, client):
        """Test preview with empty operations returns 422."""
        dataset_response = client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = dataset_response.json()["id"]

        response = client.post("/api/preprocessing/preview", json={
            "dataset_id": dataset_id,
            "operations": []
        })
        assert response.status_code == 422

    def test_preview_preprocessing_custom_row_limit(self, client):
        """Test preview with custom row limit."""
        dataset_response = client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = dataset_response.json()["id"]

        response = client.post("/api/preprocessing/preview", json={
            "dataset_id": dataset_id,
            "operations": [
                {"type": "missing_value", "config": {"method": "delete_rows"}}
            ],
            "preview_rows": 10
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["preview_data"]) <= 10

    def test_preview_preprocessing_max_row_limit(self, client):
        """Test preview enforces maximum row limit."""
        dataset_response = client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        dataset_id = dataset_response.json()["id"]

        # Try to request more than max (1000)
        response = client.post("/api/preprocessing/preview", json={
            "dataset_id": dataset_id,
            "operations": [
                {"type": "missing_value", "config": {"method": "delete_rows"}}
            ],
            "preview_rows": 2000
        })
        assert response.status_code == 422
