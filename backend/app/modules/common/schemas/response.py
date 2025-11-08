"""
Response Schemas for Common Module
"""

from datetime import datetime
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Error detail information"""

    code: str
    message: str
    details: Optional[dict] = None


T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Generic API response wrapper"""

    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class SuccessResponse(BaseModel):
    """Simple success response with message"""

    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Simple error response with detail"""

    detail: str
    timestamp: datetime = Field(default_factory=datetime.now)


# Helper functions
def success_response(data: T) -> APIResponse[T]:
    """Create a successful API response"""
    return APIResponse(success=True, data=data, error=None)


def error_response(
    code: str, message: str, details: Optional[dict] = None
) -> APIResponse:
    """Create an error API response"""
    return APIResponse(
        success=False, data=None, error=ErrorDetail(code=code, message=message, details=details)
    )
