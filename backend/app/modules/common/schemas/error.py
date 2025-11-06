"""Error Response Schemas

Provides structured error responses for API endpoints with error codes and details.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class ErrorDetail(BaseModel):
    """Detailed error information for a specific field or issue."""

    field: Optional[str] = Field(None, description="Field name that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Specific error code for this detail")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "field": "factor_name",
                "message": "Factor name must be between 1 and 255 characters",
                "code": "VALIDATION_ERROR"
            }
        }
    )


class ErrorResponse(BaseModel):
    """Structured error response."""

    error_code: str = Field(..., description="Application error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(
        None,
        description="Additional error details"
    )
    request_id: Optional[str] = Field(
        None,
        description="Request correlation ID for tracking"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "details": [
                    {
                        "field": "factor_name",
                        "message": "Factor name is required",
                        "code": "REQUIRED_FIELD"
                    }
                ],
                "request_id": "req_123abc"
            }
        }
    )


# Error codes enum
class ErrorCode:
    """Standard error codes used across the application."""

    # Validation errors (400)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    REQUIRED_FIELD = "REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"

    # Authentication/Authorization errors (401/403)
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"

    # Not found errors (404)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    INDICATOR_NOT_FOUND = "INDICATOR_NOT_FOUND"
    FACTOR_NOT_FOUND = "FACTOR_NOT_FOUND"
    LIBRARY_ITEM_NOT_FOUND = "LIBRARY_ITEM_NOT_FOUND"

    # Conflict errors (409)
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"

    # Business logic errors (422)
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    INVALID_STATUS_TRANSITION = "INVALID_STATUS_TRANSITION"
    FACTOR_NOT_PUBLISHED = "FACTOR_NOT_PUBLISHED"

    # Server errors (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
