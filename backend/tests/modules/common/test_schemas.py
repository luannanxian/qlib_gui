"""
Tests for common schemas (TDD - RED phase)
"""

import pytest
from datetime import datetime


class TestErrorDetail:
    """Test ErrorDetail schema"""

    def test_error_detail_creation(self):
        """Test creating an ErrorDetail"""
        from app.modules.common.schemas.response import ErrorDetail

        error = ErrorDetail(code="TEST_ERROR", message="Test error message")
        assert error.code == "TEST_ERROR"
        assert error.message == "Test error message"
        assert error.details is None

    def test_error_detail_with_details(self):
        """Test ErrorDetail with additional details"""
        from app.modules.common.schemas.response import ErrorDetail

        details = {"field": "email", "reason": "Invalid format"}
        error = ErrorDetail(
            code="VALIDATION_ERROR", message="Validation failed", details=details
        )
        assert error.details == details


class TestAPIResponse:
    """Test APIResponse schema"""

    def test_api_response_success(self):
        """Test creating a successful API response"""
        from app.modules.common.schemas.response import APIResponse

        data = {"id": 1, "name": "Test"}
        response = APIResponse(success=True, data=data, error=None)

        assert response.success is True
        assert response.data == data
        assert response.error is None
        assert isinstance(response.timestamp, datetime)

    def test_api_response_error(self):
        """Test creating an error API response"""
        from app.modules.common.schemas.response import APIResponse, ErrorDetail

        error = ErrorDetail(code="NOT_FOUND", message="Resource not found")
        response = APIResponse(success=False, data=None, error=error)

        assert response.success is False
        assert response.data is None
        assert response.error == error

    def test_api_response_generic_type(self):
        """Test APIResponse with generic type"""
        from app.modules.common.schemas.response import APIResponse

        data = [1, 2, 3, 4, 5]
        response = APIResponse[list](success=True, data=data)

        assert response.data == data


class TestResponseHelpers:
    """Test response helper functions"""

    def test_success_response_helper(self):
        """Test success_response helper function"""
        from app.modules.common.schemas.response import success_response

        data = {"status": "ok"}
        response = success_response(data)

        assert response.success is True
        assert response.data == data
        assert response.error is None

    def test_error_response_helper(self):
        """Test error_response helper function"""
        from app.modules.common.schemas.response import error_response

        response = error_response("TEST_ERROR", "Something went wrong")

        assert response.success is False
        assert response.data is None
        assert response.error.code == "TEST_ERROR"
        assert response.error.message == "Something went wrong"

    def test_error_response_with_details(self):
        """Test error_response with additional details"""
        from app.modules.common.schemas.response import error_response

        details = {"retry_after": 60}
        response = error_response(
            "RATE_LIMIT", "Too many requests", details=details
        )

        assert response.error.details == details
