"""
Business Exceptions for Qlib-UI
"""

from .base import QlibUIException


class ValidationError(QlibUIException):
    """Validation error exception"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", details)


class NotFoundException(QlibUIException):
    """Resource not found exception"""

    def __init__(self, resource: str, resource_id: str):
        message = f"{resource} with id {resource_id} not found"
        details = {"resource": resource, "id": resource_id}
        super().__init__(message, "NOT_FOUND", details)


class PermissionDeniedException(QlibUIException):
    """Permission denied exception"""

    def __init__(self, action: str, resource: str):
        message = f"Permission denied for action '{action}' on '{resource}'"
        details = {"action": action, "resource": resource}
        super().__init__(message, "PERMISSION_DENIED", details)


class DataImportException(QlibUIException):
    """Data import error exception"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "DATA_IMPORT_ERROR", details)


class BacktestException(QlibUIException):
    """Backtest execution error exception"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "BACKTEST_ERROR", details)


class CodeExecutionException(QlibUIException):
    """Code execution error exception"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "CODE_EXECUTION_ERROR", details)
