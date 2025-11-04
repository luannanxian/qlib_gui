"""
Tests for Mode API endpoints (TDD - RED phase)
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client"""
    from app.main import app
    return TestClient(app)


class TestGetCurrentMode:
    """Test GET /api/user/mode endpoint"""

    def test_get_current_mode_returns_default_for_new_user(self, client):
        """Test getting mode for new user returns BEGINNER"""
        response = client.get("/api/user/mode", params={"user_id": "new-user-123"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["mode"] == "beginner"
        assert data["data"]["user_id"] == "new-user-123"

    def test_get_current_mode_requires_user_id(self, client):
        """Test that user_id parameter is required"""
        response = client.get("/api/user/mode")
        
        assert response.status_code == 422  # Validation error


class TestUpdateMode:
    """Test POST /api/user/mode endpoint"""

    def test_update_mode_to_expert(self, client):
        """Test switching to expert mode"""
        response = client.post(
            "/api/user/mode",
            params={"user_id": "user-123"},
            json={"mode": "expert"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["mode"] == "expert"
        assert data["data"]["user_id"] == "user-123"

    def test_update_mode_to_beginner(self, client):
        """Test switching to beginner mode"""
        response = client.post(
            "/api/user/mode",
            params={"user_id": "user-456"},
            json={"mode": "beginner"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["mode"] == "beginner"

    def test_update_mode_validates_mode_enum(self, client):
        """Test that invalid mode is rejected"""
        response = client.post(
            "/api/user/mode",
            params={"user_id": "user-789"},
            json={"mode": "invalid_mode"}
        )
        
        assert response.status_code == 422  # Validation error

    def test_update_mode_requires_user_id(self, client):
        """Test that user_id is required"""
        response = client.post(
            "/api/user/mode",
            json={"mode": "expert"}
        )
        
        assert response.status_code == 422


class TestGetPreferences:
    """Test GET /api/user/preferences endpoint"""

    def test_get_preferences_returns_defaults_for_new_user(self, client):
        """Test getting preferences for new user"""
        response = client.get("/api/user/preferences", params={"user_id": "new-user-999"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["user_id"] == "new-user-999"
        assert data["data"]["mode"] == "beginner"
        assert data["data"]["show_tooltips"] is True
        assert data["data"]["language"] == "zh-CN"
        assert data["data"]["completed_guides"] == []

    def test_get_preferences_requires_user_id(self, client):
        """Test that user_id is required"""
        response = client.get("/api/user/preferences")
        
        assert response.status_code == 422


class TestUpdatePreferences:
    """Test PUT /api/user/preferences endpoint"""

    def test_update_preferences_tooltips(self, client):
        """Test updating show_tooltips preference"""
        response = client.put(
            "/api/user/preferences",
            params={"user_id": "user-111"},
            json={"show_tooltips": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["show_tooltips"] is False

    def test_update_preferences_language(self, client):
        """Test updating language preference"""
        response = client.put(
            "/api/user/preferences",
            params={"user_id": "user-222"},
            json={"language": "en-US"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["language"] == "en-US"

    def test_update_preferences_completed_guides(self, client):
        """Test updating completed guides"""
        response = client.put(
            "/api/user/preferences",
            params={"user_id": "user-333"},
            json={"completed_guides": ["guide-1", "guide-2"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["completed_guides"]) == 2
        assert "guide-1" in data["data"]["completed_guides"]

    def test_update_preferences_partial_update(self, client):
        """Test partial update (only some fields)"""
        # First, get current preferences
        get_response = client.get("/api/user/preferences", params={"user_id": "user-444"})
        original_tooltips = get_response.json()["data"]["show_tooltips"]
        
        # Update only language
        update_response = client.put(
            "/api/user/preferences",
            params={"user_id": "user-444"},
            json={"language": "ja-JP"}
        )
        
        assert update_response.status_code == 200
        data = update_response.json()["data"]
        assert data["language"] == "ja-JP"
        assert data["show_tooltips"] == original_tooltips  # Should remain unchanged

    def test_update_preferences_requires_user_id(self, client):
        """Test that user_id is required"""
        response = client.put(
            "/api/user/preferences",
            json={"language": "en-US"}
        )
        
        assert response.status_code == 422
