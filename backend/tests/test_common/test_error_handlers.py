"""
TDD Tests for Error Handlers

Test coverage for:
- Application exception handler
- Validation exception handler
- Database exception handler
- Generic exception handler
- Exception handler registration
"""

import pytest
from fastapi import FastAPI, Request, status
from fastapi.testclient import TestClient
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError, Field
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from unittest.mock import Mock, patch

from app.modules.common.error_handlers import (
    application_exception_handler,
    validation_exception_handler,
    database_exception_handler,
    generic_exception_handler,
    register_exception_handlers,
)
from app.modules.common.exceptions import ApplicationException
from app.modules.common.schemas.error import ErrorCode


class TestApplicationExceptionHandler:
    """Test application exception handler."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = Mock(spec=Request)
        request.headers.get.return_value = "test-request-id"
        request.url.path = "/test/path"
        return request

    @pytest.mark.asyncio
    async def test_handle_application_exception_with_dict_detail(self, mock_request):
        """Test handling application exception with dict detail."""
        exc = ApplicationException(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            message="Resource not found"
        )

        response = await application_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        body = response.body.decode()
        assert "Resource not found" in body
        assert ErrorCode.RESOURCE_NOT_FOUND in body

    @pytest.mark.asyncio
    async def test_handle_application_exception_with_str_detail(self, mock_request):
        """Test handling application exception with string detail."""
        exc = ApplicationException(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=ErrorCode.VALIDATION_ERROR,
            message="Invalid request"
        )

        response = await application_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        body = response.body.decode()
        assert "Invalid request" in body

    @pytest.mark.asyncio
    async def test_handle_application_exception_with_error_details(self, mock_request):
        """Test handling application exception with error details."""
        exc = ApplicationException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=ErrorCode.VALIDATION_ERROR,
            message="Validation failed",
            details=[
                {"field": "name", "message": "Field required", "code": "REQUIRED"}
            ]
        )

        response = await application_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        body = response.body.decode()
        assert "Validation failed" in body
        assert "name" in body
        assert "Field required" in body

    @pytest.mark.asyncio
    async def test_handle_application_exception_with_custom_headers(self, mock_request):
        """Test handling application exception with custom headers."""
        custom_headers = {"X-Custom-Header": "custom-value"}
        exc = ApplicationException(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=ErrorCode.FORBIDDEN,
            message="Access denied",
            headers=custom_headers
        )

        response = await application_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.headers.get("X-Custom-Header") == "custom-value"

    @pytest.mark.asyncio
    async def test_handle_application_exception_uses_correlation_id(self, mock_request):
        """Test that handler uses X-Correlation-ID from request."""
        mock_request.headers.get.return_value = "correlation-123"

        exc = ApplicationException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Server error"
        )

        response = await application_exception_handler(mock_request, exc)

        body = response.body.decode()
        assert "correlation-123" in body


class TestValidationExceptionHandler:
    """Test validation exception handler."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = Mock(spec=Request)
        request.headers.get.return_value = "test-request-id"
        request.url.path = "/test/path"
        return request

    @pytest.mark.asyncio
    async def test_handle_request_validation_error(self, mock_request):
        """Test handling RequestValidationError."""
        # Create a validation error
        class TestModel(BaseModel):
            name: str
            age: int

        try:
            TestModel(name=123, age="invalid")  # Will raise ValidationError
        except ValidationError as e:
            # Convert to RequestValidationError format
            exc = RequestValidationError(errors=e.errors())

            response = await validation_exception_handler(mock_request, exc)

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            body = response.body.decode()
            assert ErrorCode.VALIDATION_ERROR in body
            assert "Invalid input data" in body

    @pytest.mark.asyncio
    async def test_handle_validation_error_with_multiple_fields(self, mock_request):
        """Test handling validation errors with multiple fields."""
        class TestModel(BaseModel):
            name: str
            email: str = Field(..., pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")
            age: int = Field(..., ge=0, le=150)

        try:
            TestModel(name="", email="invalid-email", age=200)
        except ValidationError as e:
            exc = RequestValidationError(errors=e.errors())

            response = await validation_exception_handler(mock_request, exc)

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            body = response.body.decode()
            # Should contain errors for all invalid fields
            assert "email" in body or "age" in body or "name" in body

    @pytest.mark.asyncio
    async def test_handle_pydantic_validation_error(self, mock_request):
        """Test handling pure Pydantic ValidationError."""
        class TestModel(BaseModel):
            value: int

        try:
            TestModel(value="not_an_int")
        except ValidationError as exc:
            response = await validation_exception_handler(mock_request, exc)

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            body = response.body.decode()
            assert ErrorCode.VALIDATION_ERROR in body


class TestDatabaseExceptionHandler:
    """Test database exception handler."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = Mock(spec=Request)
        request.headers.get.return_value = "test-request-id"
        request.url.path = "/test/path"
        return request

    @pytest.mark.asyncio
    async def test_handle_integrity_error_unique_constraint(self, mock_request):
        """Test handling IntegrityError for unique constraint."""
        # Mock an IntegrityError with unique constraint message
        exc = IntegrityError(
            statement="INSERT INTO users...",
            params={},
            orig=Exception("UNIQUE constraint failed: users.email")
        )

        response = await database_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_409_CONFLICT
        body = response.body.decode()
        assert ErrorCode.DUPLICATE_ENTRY in body
        assert "already exists" in body

    @pytest.mark.asyncio
    async def test_handle_integrity_error_foreign_key(self, mock_request):
        """Test handling IntegrityError for foreign key constraint."""
        exc = IntegrityError(
            statement="INSERT INTO orders...",
            params={},
            orig=Exception("FOREIGN KEY constraint failed")
        )

        response = await database_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_409_CONFLICT
        body = response.body.decode()
        assert ErrorCode.DUPLICATE_ENTRY in body
        assert "does not exist" in body

    @pytest.mark.asyncio
    async def test_handle_integrity_error_duplicate(self, mock_request):
        """Test handling IntegrityError with duplicate entry message."""
        exc = IntegrityError(
            statement="INSERT INTO products...",
            params={},
            orig=Exception("Duplicate entry 'SKU123' for key 'sku'")
        )

        response = await database_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_409_CONFLICT
        body = response.body.decode()
        assert "already exists" in body

    @pytest.mark.asyncio
    async def test_handle_generic_sqlalchemy_error(self, mock_request):
        """Test handling generic SQLAlchemy error."""
        exc = SQLAlchemyError("Database connection failed")

        response = await database_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        body = response.body.decode()
        assert ErrorCode.DATABASE_ERROR in body
        assert "Database operation failed" in body


class TestGenericExceptionHandler:
    """Test generic exception handler."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock request."""
        request = Mock(spec=Request)
        request.headers.get.return_value = "test-request-id"
        request.url.path = "/test/path"
        return request

    @pytest.mark.asyncio
    async def test_handle_generic_exception(self, mock_request):
        """Test handling unexpected exceptions."""
        exc = Exception("Unexpected error occurred")

        response = await generic_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        body = response.body.decode()
        assert ErrorCode.INTERNAL_ERROR in body
        assert "unexpected error" in body.lower()

    @pytest.mark.asyncio
    async def test_handle_runtime_error(self, mock_request):
        """Test handling RuntimeError."""
        exc = RuntimeError("Runtime issue")

        response = await generic_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        body = response.body.decode()
        assert ErrorCode.INTERNAL_ERROR in body

    @pytest.mark.asyncio
    async def test_handle_type_error(self, mock_request):
        """Test handling TypeError."""
        exc = TypeError("Invalid type")

        response = await generic_exception_handler(mock_request, exc)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        body = response.body.decode()
        assert ErrorCode.INTERNAL_ERROR in body

    @pytest.mark.asyncio
    async def test_generic_handler_logs_error_type(self, mock_request):
        """Test that generic handler logs the error type."""
        exc = ValueError("Custom value error")

        with patch('app.modules.common.error_handlers.logger') as mock_logger:
            response = await generic_exception_handler(mock_request, exc)

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            # Verify logger was called
            mock_logger.error.assert_called_once()


class TestExceptionHandlerRegistration:
    """Test exception handler registration."""

    def test_register_all_handlers(self):
        """Test that all exception handlers are registered."""
        app = FastAPI()

        register_exception_handlers(app)

        # Verify handlers are registered by checking exception_handlers dict
        assert ApplicationException in app.exception_handlers
        assert RequestValidationError in app.exception_handlers
        assert ValidationError in app.exception_handlers
        assert SQLAlchemyError in app.exception_handlers
        assert Exception in app.exception_handlers

    def test_registered_handlers_work_in_app(self):
        """Test that registered handlers work in actual FastAPI app."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/test-error")
        async def test_error():
            raise ApplicationException(
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code=ErrorCode.VALIDATION_ERROR,
                message="Test error"
            )

        client = TestClient(app)
        response = client.get("/test-error")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Test error" in response.text

    def test_validation_error_handler_works_in_app(self):
        """Test validation error handler in actual app."""
        app = FastAPI()
        register_exception_handlers(app)

        class TestInput(BaseModel):
            value: int

        @app.post("/test-validation")
        async def test_validation(data: TestInput):
            return {"value": data.value}

        client = TestClient(app)
        response = client.post("/test-validation", json={"value": "not_an_int"})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Invalid input data" in response.text

    def test_database_error_handler_works_in_app(self):
        """Test database error handler in actual app."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/test-db-error")
        async def test_db_error():
            raise IntegrityError(
                statement="INSERT...",
                params={},
                orig=Exception("UNIQUE constraint failed")
            )

        client = TestClient(app)
        response = client.get("/test-db-error")

        assert response.status_code == status.HTTP_409_CONFLICT
        assert ErrorCode.DUPLICATE_ENTRY in response.text

    def test_generic_error_handler_works_in_app(self):
        """Test generic error handler in actual app."""
        app = FastAPI()
        register_exception_handlers(app)

        @app.get("/test-generic-error")
        async def test_generic_error():
            raise RuntimeError("Unexpected issue")

        client = TestClient(app, raise_server_exceptions=False)
        response = client.get("/test-generic-error")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert ErrorCode.INTERNAL_ERROR in response.text
