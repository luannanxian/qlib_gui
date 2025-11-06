"""User Library Schemas for Indicator Module"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class UserLibraryItemResponse(BaseModel):
    """
    Schema for user library item response.

    This schema represents a factor in a user's personal library.
    """
    id: str
    user_id: str = Field(..., description="User ID")
    factor_id: str = Field(..., description="Factor ID")
    is_favorite: bool = Field(False, description="Whether item is marked as favorite")
    usage_count: int = Field(0, ge=0, description="Number of times used")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user123",
                "factor_id": "factor_001",
                "is_favorite": True,
                "usage_count": 15,
                "last_used_at": "2024-01-15T10:30:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }
    )


class UserLibraryListResponse(BaseModel):
    """
    Schema for paginated user library list response.

    Attributes:
        total: Total number of library items
        skip: Number of records skipped
        limit: Maximum records returned
        items: List of library items
    """
    total: int = Field(..., ge=0, description="Total number of library items")
    skip: int = Field(0, ge=0, description="Number of records skipped")
    limit: int = Field(100, ge=1, description="Maximum records returned")
    items: List[UserLibraryItemResponse] = Field(..., description="List of library items")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 25,
                "skip": 0,
                "limit": 20,
                "items": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "user_id": "user123",
                        "factor_id": "factor_001",
                        "is_favorite": True,
                        "usage_count": 15,
                        "last_used_at": "2024-01-15T10:30:00Z",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                ]
            }
        }
    )


class AddToLibraryRequest(BaseModel):
    """
    Schema for adding a factor to user's library.

    Attributes:
        factor_id: Factor ID to add to library
    """
    factor_id: str = Field(..., min_length=1, description="Factor ID to add")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "factor_id": "factor_001"
            }
        }
    )


class ToggleFavoriteRequest(BaseModel):
    """
    Schema for toggling favorite status of a library item.

    Attributes:
        is_favorite: New favorite status
    """
    is_favorite: bool = Field(..., description="New favorite status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_favorite": True
            }
        }
    )


class LibraryStatsResponse(BaseModel):
    """
    Schema for user library statistics.

    Attributes:
        user_id: User ID
        total_items: Total number of items in library
        favorite_count: Number of favorite items
        total_usage: Total usage count across all items
    """
    user_id: str = Field(..., description="User ID")
    total_items: int = Field(..., ge=0, description="Total number of items in library")
    favorite_count: int = Field(..., ge=0, description="Number of favorite items")
    total_usage: int = Field(..., ge=0, description="Total usage count")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "user123",
                "total_items": 25,
                "favorite_count": 8,
                "total_usage": 150
            }
        }
    )
