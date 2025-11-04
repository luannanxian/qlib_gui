"""Tests for base exception classes.

Following TDD approach - these tests are written BEFORE implementation.
"""

import pytest


class TestQlibUIException:
    """Test QlibUIException base exception."""

    def test_qlib_ui_exception_basic(self):
        """Test basic QlibUIException creation."""
        from app.modules.common.exceptions.base import QlibUIException

        exc = QlibUIException("Test error")
        assert str(exc) == "Test error"
        assert exc.message == "Test error"
        assert exc.code == "INTERNAL_ERROR"
        assert exc.details == {}

    def test_qlib_ui_exception_with_code(self):
        """Test QlibUIException with custom code."""
        from app.modules.common.exceptions.base import QlibUIException

        exc = QlibUIException("Test error", code="CUSTOM_ERROR")
        assert exc.message == "Test error"
        assert exc.code == "CUSTOM_ERROR"

    def test_qlib_ui_exception_with_details(self):
        """Test QlibUIException with details."""
        from app.modules.common.exceptions.base import QlibUIException

        details = {"field": "name", "value": "invalid"}
        exc = QlibUIException("Test error", code="VALIDATION_ERROR", details=details)
        assert exc.message == "Test error"
        assert exc.code == "VALIDATION_ERROR"
        assert exc.details == details

    def test_qlib_ui_exception_is_exception(self):
        """Test that QlibUIException is a proper Exception."""
        from app.modules.common.exceptions.base import QlibUIException

        exc = QlibUIException("Test")
        assert isinstance(exc, Exception)

    def test_qlib_ui_exception_can_be_raised(self):
        """Test that QlibUIException can be raised and caught."""
        from app.modules.common.exceptions.base import QlibUIException

        with pytest.raises(QlibUIException) as exc_info:
            raise QlibUIException("Test error", code="TEST")

        assert exc_info.value.message == "Test error"
        assert exc_info.value.code == "TEST"


class TestValidationError:
    """Test ValidationError exception."""

    def test_validation_error_creation(self):
        """Test ValidationError creation."""
        from app.modules.common.exceptions.base import ValidationError

        exc = ValidationError("Invalid input")
        assert exc.message == "Invalid input"
        assert exc.code == "VALIDATION_ERROR"
        assert exc.details == {}

    def test_validation_error_with_details(self):
        """Test ValidationError with details."""
        from app.modules.common.exceptions.base import ValidationError

        details = {"field": "email", "reason": "invalid format"}
        exc = ValidationError("Email validation failed", details=details)
        assert exc.message == "Email validation failed"
        assert exc.code == "VALIDATION_ERROR"
        assert exc.details == details

    def test_validation_error_inherits_from_qlib_ui_exception(self):
        """Test that ValidationError inherits from QlibUIException."""
        from app.modules.common.exceptions.base import ValidationError, QlibUIException

        exc = ValidationError("Test")
        assert isinstance(exc, QlibUIException)

    def test_validation_error_can_be_caught_as_qlib_ui_exception(self):
        """Test that ValidationError can be caught as QlibUIException."""
        from app.modules.common.exceptions.base import ValidationError, QlibUIException

        with pytest.raises(QlibUIException):
            raise ValidationError("Test error")


class TestNotFoundException:
    """Test NotFoundException exception."""

    def test_not_found_exception_creation(self):
        """Test NotFoundException creation with resource and id."""
        from app.modules.common.exceptions.base import NotFoundException

        exc = NotFoundException("User", "123")
        assert "User" in exc.message
        assert "123" in exc.message
        assert exc.code == "NOT_FOUND"
        assert exc.details["resource"] == "User"
        assert exc.details["id"] == "123"

    def test_not_found_exception_message_format(self):
        """Test NotFoundException message format."""
        from app.modules.common.exceptions.base import NotFoundException

        exc = NotFoundException("Dataset", "abc-def-123")
        expected_message = "Dataset with id abc-def-123 not found"
        assert exc.message == expected_message

    def test_not_found_exception_inherits_from_qlib_ui_exception(self):
        """Test that NotFoundException inherits from QlibUIException."""
        from app.modules.common.exceptions.base import NotFoundException, QlibUIException

        exc = NotFoundException("Resource", "id")
        assert isinstance(exc, QlibUIException)


class TestPermissionDeniedException:
    """Test PermissionDeniedException exception."""

    def test_permission_denied_exception_creation(self):
        """Test PermissionDeniedException creation."""
        from app.modules.common.exceptions.base import PermissionDeniedException

        exc = PermissionDeniedException("delete", "Dataset")
        assert "delete" in exc.message
        assert "Dataset" in exc.message
        assert exc.code == "PERMISSION_DENIED"
        assert exc.details["action"] == "delete"
        assert exc.details["resource"] == "Dataset"

    def test_permission_denied_exception_message_format(self):
        """Test PermissionDeniedException message format."""
        from app.modules.common.exceptions.base import PermissionDeniedException

        exc = PermissionDeniedException("update", "Strategy")
        expected_message = "Permission denied for action 'update' on 'Strategy'"
        assert exc.message == expected_message

    def test_permission_denied_exception_inherits_from_qlib_ui_exception(self):
        """Test that PermissionDeniedException inherits from QlibUIException."""
        from app.modules.common.exceptions.base import PermissionDeniedException, QlibUIException

        exc = PermissionDeniedException("read", "Resource")
        assert isinstance(exc, QlibUIException)
