"""
HTTP Exception Classes for FastAPI Integration

These exceptions extend FastAPI's HTTPException to provide structured error responses
with error codes, detailed messages, and field-level validation information.
"""

from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status


class ApplicationException(HTTPException):
    """
    Base exception for application errors with structured error details.

    This extends FastAPI's HTTPException to include error codes and detailed
    error information for better API error responses.
    """

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[List[Dict[str, Any]]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.error_code = error_code
        self.error_details = details
        super().__init__(
            status_code=status_code,
            detail={"error_code": error_code, "message": message, "details": details},
            headers=headers
        )


class ResourceNotFoundException(ApplicationException):
    """Exception for resource not found errors (404)."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
        message: Optional[str] = None
    ):
        if not message:
            message = f"{resource_type} with id '{resource_id}' not found"

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=f"{resource_type.upper()}_NOT_FOUND",
            message=message,
            details=[{
                "field": "id",
                "message": message,
                "value": resource_id
            }]
        )


class ValidationException(ApplicationException):
    """Exception for validation errors (422)."""

    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            message=message,
            details=details
        )


class ConflictException(ApplicationException):
    """Exception for resource conflicts (409)."""

    def __init__(
        self,
        message: str,
        error_code: str = "CONFLICT",
        details: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code=error_code,
            message=message,
            details=details
        )


class BadRequestException(ApplicationException):
    """Exception for bad requests (400)."""

    def __init__(
        self,
        message: str,
        error_code: str = "BAD_REQUEST",
        details: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
            message=message,
            details=details
        )


class UnauthorizedException(ApplicationException):
    """Exception for authentication errors (401)."""

    def __init__(
        self,
        message: str = "Authentication required",
        error_code: str = "UNAUTHORIZED"
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code,
            message=message,
            headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenException(ApplicationException):
    """Exception for authorization errors (403)."""

    def __init__(
        self,
        message: str = "Access forbidden",
        error_code: str = "FORBIDDEN"
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code,
            message=message
        )
