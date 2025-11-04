"""
Base Models for Common Module
"""

from datetime import datetime
from typing import TypeVar, Generic, List
from pydantic import BaseModel, Field


class TimestampMixin(BaseModel):
    """Mixin for created_at and updated_at timestamps"""

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class BaseDBModel(TimestampMixin):
    """Base model for database entities"""

    id: str
    is_deleted: bool = False


class PaginationParams(BaseModel):
    """Pagination parameters"""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database queries"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Return page_size as limit"""
        return self.page_size


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
