"""Tests for response schemas.

Following TDD approach - these tests are written BEFORE implementation.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError


class TestErrorDetail:
    """Test ErrorDetail model."""

    def test_error_detail_creation(self):
        """Test ErrorDetail creation with required fields."""
        from app.modules.common.schemas.response import ErrorDetail

        error = ErrorDetail(code="TEST_ERROR", message="Test error message")
        assert error.code == "TEST_ERROR"
        assert error.message == "Test error message"
        assert error.details is None

    def test_error_detail_with_details(self):
        """Test ErrorDetail with additional details."""
        from app.modules.common.schemas.response import ErrorDetail

        details = {"field": "email", "reason": "invalid format"}
        error = ErrorDetail(code="VALIDATION_ERROR", message="Validation failed", details=details)
        assert error.code == "VALIDATION_ERROR"
        assert error.message == "Validation failed"
        assert error.details == details

    def test_error_detail_requires_code_and_message(self):
        """Test that ErrorDetail requires code and message."""
        from app.modules.common.schemas.response import ErrorDetail

        with pytest.raises(ValidationError):
            ErrorDetail(code="TEST_ERROR")

        with pytest.raises(ValidationError):
            ErrorDetail(message="Test message")

    def test_error_detail_serialization(self):
        """Test ErrorDetail serialization."""
        from app.modules.common.schemas.response import ErrorDetail

        error = ErrorDetail(
            code="NOT_FOUND", message="Resource not found", details={"resource": "User"}
        )
        data = error.model_dump()
        assert data["code"] == "NOT_FOUND"
        assert data["message"] == "Resource not found"
        assert data["details"] == {"resource": "User"}


class TestAPIResponse:
    """Test APIResponse generic model."""

    def test_api_response_success(self):
        """Test successful APIResponse."""
        from app.modules.common.schemas.response import APIResponse

        data = {"id": "123", "name": "Test"}
        response = APIResponse(success=True, data=data)

        assert response.success is True
        assert response.data == data
        assert response.error is None
        assert isinstance(response.timestamp, datetime)

    def test_api_response_error(self):
        """Test error APIResponse."""
        from app.modules.common.schemas.response import APIResponse, ErrorDetail

        error = ErrorDetail(code="ERROR", message="Something went wrong")
        response = APIResponse(success=False, error=error)

        assert response.success is False
        assert response.data is None
        assert response.error == error
        assert isinstance(response.timestamp, datetime)

    def test_api_response_requires_success(self):
        """Test that APIResponse requires success field."""
        from app.modules.common.schemas.response import APIResponse

        with pytest.raises(ValidationError):
            APIResponse(data={"test": "data"})

    def test_api_response_timestamp_auto_generated(self):
        """Test that timestamp is automatically generated."""
        from app.modules.common.schemas.response import APIResponse

        response1 = APIResponse(success=True, data="test")
        response2 = APIResponse(success=True, data="test")

        assert isinstance(response1.timestamp, datetime)
        assert isinstance(response2.timestamp, datetime)
        # Timestamps should be close but might not be exactly equal
        assert abs((response2.timestamp - response1.timestamp).total_seconds()) < 1

    def test_api_response_custom_timestamp(self):
        """Test APIResponse with custom timestamp."""
        from app.modules.common.schemas.response import APIResponse

        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        response = APIResponse(success=True, data="test", timestamp=custom_time)
        assert response.timestamp == custom_time

    def test_api_response_with_typed_data(self):
        """Test APIResponse with typed data."""
        from app.modules.common.schemas.response import APIResponse
        from app.modules.common.models.base import PaginationParams

        pagination = PaginationParams(page=1, page_size=20)
        response = APIResponse(success=True, data=pagination)

        assert response.success is True
        assert response.data.page == 1
        assert response.data.page_size == 20

    def test_api_response_serialization(self):
        """Test APIResponse serialization."""
        from app.modules.common.schemas.response import APIResponse

        response = APIResponse(success=True, data={"key": "value"})
        data = response.model_dump()

        assert "success" in data
        assert "data" in data
        assert "error" in data
        assert "timestamp" in data
        assert data["success"] is True


class TestSuccessResponse:
    """Test success_response helper function."""

    def test_success_response_with_data(self):
        """Test success_response creates correct response."""
        from app.modules.common.schemas.response import success_response

        data = {"id": 1, "name": "Test"}
        response = success_response(data)

        assert response.success is True
        assert response.data == data
        assert response.error is None

    def test_success_response_with_none(self):
        """Test success_response with None data."""
        from app.modules.common.schemas.response import success_response

        response = success_response(None)
        assert response.success is True
        assert response.data is None

    def test_success_response_with_list(self):
        """Test success_response with list data."""
        from app.modules.common.schemas.response import success_response

        data = [1, 2, 3, 4, 5]
        response = success_response(data)

        assert response.success is True
        assert response.data == data

    def test_success_response_with_model(self):
        """Test success_response with Pydantic model."""
        from app.modules.common.schemas.response import success_response
        from app.modules.common.models.base import PaginationParams

        pagination = PaginationParams(page=2, page_size=50)
        response = success_response(pagination)

        assert response.success is True
        assert response.data == pagination


class TestErrorResponse:
    """Test error_response helper function."""

    def test_error_response_basic(self):
        """Test error_response with code and message."""
        from app.modules.common.schemas.response import error_response

        response = error_response("NOT_FOUND", "Resource not found")

        assert response.success is False
        assert response.data is None
        assert response.error is not None
        assert response.error.code == "NOT_FOUND"
        assert response.error.message == "Resource not found"
        assert response.error.details is None

    def test_error_response_with_details(self):
        """Test error_response with details dict."""
        from app.modules.common.schemas.response import error_response

        details = {"field": "email", "value": "invalid@"}
        response = error_response("VALIDATION_ERROR", "Invalid email", details)

        assert response.success is False
        assert response.error.code == "VALIDATION_ERROR"
        assert response.error.message == "Invalid email"
        assert response.error.details == details

    def test_error_response_empty_details(self):
        """Test error_response with empty details dict."""
        from app.modules.common.schemas.response import error_response

        response = error_response("ERROR", "Error occurred", {})

        assert response.error.details == {}

    def test_error_response_serialization(self):
        """Test error_response can be serialized."""
        from app.modules.common.schemas.response import error_response

        response = error_response("TEST_ERROR", "Test message", {"key": "value"})
        data = response.model_dump()

        assert data["success"] is False
        assert data["data"] is None
        assert data["error"]["code"] == "TEST_ERROR"
        assert data["error"]["message"] == "Test message"
        assert data["error"]["details"] == {"key": "value"}
