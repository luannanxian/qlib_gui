"""Tests for Dataset API endpoints.

Following TDD approach - these tests are written BEFORE implementation.
Uses proper async database fixtures and DatasetRepository.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession


class TestDatasetAPI:
    """Test Dataset API endpoints with proper database fixtures."""

    def test_list_datasets_empty(self, client):
        """Test listing datasets when none exist."""
        response = client.get("/api/datasets")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)
        assert data["total"] == 0
        assert len(data["items"]) == 0

    def test_list_datasets_returns_list(self, client):
        """Test list datasets returns a list response."""
        response = client.get("/api/datasets")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_get_nonexistent_dataset(self, client):
        """Test getting a dataset that doesn't exist."""
        response = client.get("/api/datasets/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_create_dataset(self, client):
        """Test creating a dataset."""
        response = client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Dataset"
        assert data["source"] == "local"
        assert data["file_path"] == "/data/test.csv"
        assert data["status"] == "pending"
        assert "id" in data

    def test_create_dataset_missing_required_fields(self, client):
        """Test creating a dataset with missing required fields."""
        response = client.post("/api/datasets", json={
            "name": "Test"
        })
        assert response.status_code == 422

    def test_create_and_get_dataset(self, client):
        """Test creating a dataset and retrieving it."""
        # Create dataset
        create_response = client.post("/api/datasets", json={
            "name": "Test Dataset",
            "source": "local",
            "file_path": "/data/test.csv"
        })
        assert create_response.status_code == 201
        created = create_response.json()
        dataset_id = created["id"]

        # Get the created dataset
        get_response = client.get(f"/api/datasets/{dataset_id}")
        assert get_response.status_code == 200
        retrieved = get_response.json()
        assert retrieved["id"] == dataset_id
        assert retrieved["name"] == "Test Dataset"
        assert retrieved["source"] == "local"
        assert retrieved["file_path"] == "/data/test.csv"
        assert retrieved["status"] == "pending"

    def test_update_dataset(self, client):
        """Test updating a dataset."""
        # Create dataset first
        create_response = client.post("/api/datasets", json={
            "name": "Original",
            "source": "local",
            "file_path": "/data/original.csv"
        })
        assert create_response.status_code == 201
        dataset_id = create_response.json()["id"]

        # Update dataset
        update_response = client.put(f"/api/datasets/{dataset_id}", json={
            "name": "Updated",
            "status": "valid",
            "row_count": 100,
            "columns": ["col1", "col2"],
            "metadata": {"version": "1.0"}
        })
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["name"] == "Updated"
        assert updated["status"] == "valid"
        assert updated["row_count"] == 100
        assert updated["columns"] == ["col1", "col2"]
        assert updated["metadata"] == {"version": "1.0"}

    def test_update_nonexistent_dataset(self, client):
        """Test updating a dataset that doesn't exist."""
        response = client.put("/api/datasets/nonexistent-id", json={
            "name": "Updated"
        })
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_delete_dataset(self, client):
        """Test deleting a dataset."""
        # Create dataset first
        create_response = client.post("/api/datasets", json={
            "name": "To Delete",
            "source": "local",
            "file_path": "/data/delete.csv"
        })
        assert create_response.status_code == 201
        dataset_id = create_response.json()["id"]

        # Delete dataset
        delete_response = client.delete(f"/api/datasets/{dataset_id}")
        assert delete_response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/api/datasets/{dataset_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_dataset(self, client):
        """Test deleting a dataset that doesn't exist."""
        response = client.delete("/api/datasets/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_duplicate_dataset_name(self, client):
        """Test that creating a dataset with duplicate name fails."""
        # Create first dataset
        create_response1 = client.post("/api/datasets", json={
            "name": "Unique Name",
            "source": "local",
            "file_path": "/data/first.csv"
        })
        assert create_response1.status_code == 201

        # Try to create dataset with same name
        create_response2 = client.post("/api/datasets", json={
            "name": "Unique Name",
            "source": "local",
            "file_path": "/data/second.csv"
        })
        assert create_response2.status_code == 409
        data = create_response2.json()
        assert "detail" in data

    def test_list_datasets_with_multiple_items(self, client):
        """Test listing datasets with multiple items."""
        # Create multiple datasets
        datasets = []
        for i in range(3):
            response = client.post("/api/datasets", json={
                "name": f"Dataset {i}",
                "source": "local",
                "file_path": f"/data/dataset{i}.csv"
            })
            assert response.status_code == 201
            datasets.append(response.json())

        # List datasets
        list_response = client.get("/api/datasets")
        assert list_response.status_code == 200
        data = list_response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
