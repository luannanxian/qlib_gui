"""Dataset Schemas for Data Management Module"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.modules.data_management.models.dataset import DataSource, DatasetStatus


class DatasetCreate(BaseModel):
    """
    Schema for creating a new dataset.

    Attributes:
        name: Dataset name (unique identifier)
        source: Data source type (local, qlib, thirdparty)
        file_path: File path or URI to dataset location
        extra_metadata: Optional additional metadata (JSON object)
    """
    name: str = Field(..., min_length=1, max_length=255, description="Dataset name")
    source: DataSource = Field(..., description="Data source type")
    file_path: str = Field(..., min_length=1, description="File path or URI")
    extra_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata (JSON object)"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate dataset name is not just whitespace"""
        if not v or not v.strip():
            raise ValueError("Dataset name cannot be empty or whitespace")
        return v.strip()


class DatasetUpdate(BaseModel):
    """
    Schema for updating a dataset.

    All fields are optional - only provided fields will be updated.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Dataset name")
    status: Optional[DatasetStatus] = Field(None, description="Dataset validation status")
    row_count: Optional[int] = Field(None, ge=0, description="Number of rows")
    columns: Optional[List[str]] = Field(None, description="List of column names")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate dataset name if provided"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Dataset name cannot be empty or whitespace")
        return v.strip() if v else None

    @field_validator("row_count")
    @classmethod
    def validate_row_count(cls, v: Optional[int]) -> Optional[int]:
        """Validate row count is non-negative"""
        if v is not None and v < 0:
            raise ValueError("Row count must be non-negative")
        return v


class DatasetResponse(BaseModel):
    """
    Schema for dataset response.

    This schema is used for API responses and maps database fields
    to client-friendly names. Note: 'extra_metadata' from DB is exposed
    as 'metadata' in the API for better developer experience.
    """
    id: str
    name: str
    source: str  # Changed from DataSource to str for JSON serialization
    file_path: str
    status: str  # Changed from DatasetStatus to str for JSON serialization
    row_count: int
    columns: List[str]
    extra_metadata: Dict[str, Any] = Field(
        ...,
        alias="metadata",
        serialization_alias="metadata",
        description="Additional metadata (exposed as 'metadata' in API)"
    )
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "Stock Data 2024",
                "source": "local",
                "file_path": "/data/stocks_2024.csv",
                "status": "valid",
                "row_count": 10000,
                "columns": ["date", "symbol", "open", "high", "low", "close", "volume"],
                "metadata": {"description": "Daily stock data for 2024", "format": "csv"},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    )


class DatasetListResponse(BaseModel):
    """
    Schema for paginated dataset list response.

    Attributes:
        total: Total number of datasets (across all pages)
        items: List of datasets in current page
    """
    total: int = Field(..., ge=0, description="Total number of datasets")
    items: List[DatasetResponse] = Field(..., description="List of datasets")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 100,
                "items": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Stock Data 2024",
                        "source": "local",
                        "file_path": "/data/stocks_2024.csv",
                        "status": "valid",
                        "row_count": 10000,
                        "columns": ["date", "symbol", "price"],
                        "metadata": {},
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                ]
            }
        }
    )
