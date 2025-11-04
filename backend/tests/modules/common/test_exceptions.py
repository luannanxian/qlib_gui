"""
Tests for common exceptions (TDD - RED phase)
"""

import pytest


class TestQlibUIException:
    """Test base QlibUIException"""

    def test_qlib_ui_exception_creation(self):
        """Test creating a QlibUIException"""
        from app.modules.common.exceptions.base import QlibUIException

        error = QlibUIException("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.code == "INTERNAL_ERROR"
        assert error.details == {}

    def test_qlib_ui_exception_with_code(self):
        """Test QlibUIException with custom code"""
        from app.modules.common.exceptions.base import QlibUIException

        error = QlibUIException("Error occurred", code="CUSTOM_ERROR")
        assert error.code == "CUSTOM_ERROR"

    def test_qlib_ui_exception_with_details(self):
        """Test QlibUIException with details"""
        from app.modules.common.exceptions.base import QlibUIException

        details = {"field": "email", "reason": "Invalid"}
        error = QlibUIException("Validation failed", details=details)
        assert error.details == details


class TestValidationError:
    """Test ValidationError"""

    def test_validation_error_creation(self):
        """Test creating a ValidationError"""
        from app.modules.common.exceptions.business import ValidationError

        error = ValidationError("Invalid input")
        assert error.message == "Invalid input"
        assert error.code == "VALIDATION_ERROR"

    def test_validation_error_with_details(self):
        """Test ValidationError with field details"""
        from app.modules.common.exceptions.business import ValidationError

        details = {"field": "age", "constraint": "must be >= 0"}
        error = ValidationError("Age validation failed", details=details)
        assert error.details == details


class TestNotFoundException:
    """Test NotFoundException"""

    def test_not_found_exception_creation(self):
        """Test creating a NotFoundException"""
        from app.modules.common.exceptions.business import NotFoundException

        error = NotFoundException("User", "123")
        assert "User" in error.message
        assert "123" in error.message
        assert error.code == "NOT_FOUND"

    def test_not_found_exception_details(self):
        """Test NotFoundException includes resource details"""
        from app.modules.common.exceptions.business import NotFoundException

        error = NotFoundException("Dataset", "abc-123")
        assert error.details["resource"] == "Dataset"
        assert error.details["id"] == "abc-123"


class TestPermissionDeniedException:
    """Test PermissionDeniedException"""

    def test_permission_denied_exception_creation(self):
        """Test creating a PermissionDeniedException"""
        from app.modules.common.exceptions.business import PermissionDeniedException

        error = PermissionDeniedException("delete", "strategy")
        assert "delete" in error.message
        assert "strategy" in error.message
        assert error.code == "PERMISSION_DENIED"

    def test_permission_denied_exception_details(self):
        """Test PermissionDeniedException includes action and resource"""
        from app.modules.common.exceptions.business import PermissionDeniedException

        error = PermissionDeniedException("update", "backtest")
        assert error.details["action"] == "update"
        assert error.details["resource"] == "backtest"


class TestBusinessExceptions:
    """Test business-specific exceptions"""

    def test_data_import_exception(self):
        """Test DataImportException"""
        from app.modules.common.exceptions.business import DataImportException

        error = DataImportException("Failed to import CSV file")
        assert error.message == "Failed to import CSV file"
        assert isinstance(error.code, str)

    def test_backtest_exception(self):
        """Test BacktestException"""
        from app.modules.common.exceptions.business import BacktestException

        error = BacktestException("Backtest execution failed")
        assert error.message == "Backtest execution failed"

    def test_code_execution_exception(self):
        """Test CodeExecutionException"""
        from app.modules.common.exceptions.business import CodeExecutionException

        error = CodeExecutionException("Unsafe code detected")
        assert error.message == "Unsafe code detected"
