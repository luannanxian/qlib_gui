"""Tests for Dataset API endpoints.

Following TDD approach - these tests are written BEFORE implementation.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


class TestDatasetAPI:
    """Test Dataset API endpoints."""

    def test_list_datasets_endpoint_exists(self, client):
        """Test that list datasets endpoint exists."""
        response = client.get("/api/datasets")
        # Should not return 404
        assert response.status_code != 404

    def test_list_datasets_returns_list(self, client):
        """Test list datasets returns a list response."""
        response = client.get("/api/datasets")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_get_dataset_endpoint_exists(self, client):
        """Test that get dataset endpoint exists."""
        response = client.get("/api/datasets/test-id")
        # Should not return 404 for route not found
        # May return 404 for dataset not found, which is OK
        assert response.status_code in [200, 404]

    def test_create_dataset_endpoint_exists(self, client):
        """Test that create dataset endpoint exists."""
        response = client.post("/api/datasets", json={
            "name": "Test",
            "source": "local",
            "file_path": "/test.csv"
        })
        # Should not return 404 for route not found
        assert response.status_code != 404

    def test_update_dataset_endpoint_exists(self, client):
        """Test that update dataset endpoint exists."""
        response = client.put("/api/datasets/test-id", json={
            "name": "Updated"
        })
        # Should not return 404 for route not found
        assert response.status_code in [200, 404]

    def test_delete_dataset_endpoint_exists(self, client):
        """Test that delete dataset endpoint exists."""
        response = client.delete("/api/datasets/test-id")
        # Should not return 404 for route not found
        assert response.status_code in [200, 204, 404]

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

    def test_delete_dataset(self, client):
        """Test deleting a dataset."""
        # Create dataset first
        create_response = client.post("/api/datasets", json={
            "name": "To Delete",
            "source": "local",
            "file_path": "/data/delete.csv"
        })
        dataset_id = create_response.json()["id"]

        # Delete dataset
        delete_response = client.delete(f"/api/datasets/{dataset_id}")
        assert delete_response.status_code == 204

        # Verify it's deleted
        get_response = client.get(f"/api/datasets/{dataset_id}")
        assert get_response.status_code == 404

    def test_get_nonexistent_dataset(self, client):
        """Test getting a dataset that doesn't exist."""
        response = client.get("/api/datasets/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_update_nonexistent_dataset(self, client):
        """Test updating a dataset that doesn't exist."""
        response = client.put("/api/datasets/nonexistent-id", json={
            "name": "Updated"
        })
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_delete_nonexistent_dataset(self, client):
        """Test deleting a dataset that doesn't exist."""
        response = client.delete("/api/datasets/nonexistent-id")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
