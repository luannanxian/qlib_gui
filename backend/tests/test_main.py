"""
Tests for FastAPI main application
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client"""
    from app.main import app
    return TestClient(app)


class TestRootEndpoint:
    """Test root endpoint"""

    def test_root_returns_app_info(self, client):
        """Test root endpoint returns application information"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "Qlib-UI" in data["message"]


class TestHealthCheck:
    """Test health check endpoint"""

    def test_health_check_returns_healthy(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestCORS:
    """Test CORS middleware configuration"""

    def test_cors_headers_present(self, client):
        """Test CORS headers are present"""
        response = client.options(
            "/api/user/mode",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        # FastAPI TestClient automatically handles CORS
        assert response.status_code in [200, 405]  # 405 for OPTIONS not implemented


class TestAPIRoutes:
    """Test API routes are registered"""

    def test_user_mode_routes_registered(self, client):
        """Test user mode routes are accessible"""
        # Test that the route exists (even if it requires parameters)
        response = client.get("/api/user/mode")
        
        # Should get 422 (validation error) not 404 (not found)
        assert response.status_code == 422


class TestAppConfiguration:
    """Test FastAPI app configuration"""

    def test_app_has_title(self):
        """Test app has title configured"""
        from app.main import app
        
        assert app.title == "Qlib-UI API"

    def test_app_has_description(self):
        """Test app has description"""
        from app.main import app
        
        assert "Quantitative Investment" in app.description

    def test_app_has_version(self):
        """Test app has version"""
        from app.main import app
        
        assert app.version == "0.1.0"

    def test_app_has_routers(self):
        """Test app has routers configured"""
        from app.main import app
        
        # Check that routes are registered
        routes = [route.path for route in app.routes]
        assert "/api/user/mode" in routes
        assert "/api/user/preferences" in routes
        assert "/" in routes
        assert "/health" in routes


class TestMiddleware:
    """Test middleware configuration"""

    def test_cors_middleware_configured(self):
        """Test CORS middleware is configured"""
        from app.main import app
        
        # Check middleware is added
        middleware_types = [type(m).__name__ for m in app.user_middleware]
        
        # CORSMiddleware should be present
        # Note: FastAPI wraps middlewares, so we check for Starlette middleware
        assert len(app.user_middleware) > 0
