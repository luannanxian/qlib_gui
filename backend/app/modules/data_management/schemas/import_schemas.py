"""
Import Schemas for Data Management Module

Defines request and response models for data import operations.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.database.models.import_task import ImportStatus, ImportType


class ImportTaskCreate(BaseModel):
    """
    Schema for creating a new import task.

    Attributes:
        task_name: Human-readable task name
        import_type: File type (csv, excel, qlib, json)
        original_filename: Original uploaded filename
        file_path: Server file path where uploaded file is stored
        file_size: File size in bytes
        import_config: Optional import configuration
        user_id: Optional user ID who initiated the import
    """
    task_name: str = Field(..., min_length=1, max_length=255, description="Human-readable task name")
    import_type: ImportType = Field(..., description="Import file type")
    original_filename: str = Field(..., min_length=1, max_length=255, description="Original filename")
    file_path: str = Field(..., min_length=1, description="Server file path")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    import_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Import configuration (delimiter, encoding, skip rows, etc.)"
    )
    user_id: Optional[str] = Field(None, description="User ID who initiated import")

    @field_validator("task_name")
    @classmethod
    def validate_task_name(cls, v: str) -> str:
        """Validate task name is not just whitespace"""
        if not v or not v.strip():
            raise ValueError("Task name cannot be empty or whitespace")
        return v.strip()

    @field_validator("file_size")
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        """Validate file size is reasonable (max 100MB default)"""
        max_size = 100 * 1024 * 1024  # 100MB in bytes
        if v > max_size:
            raise ValueError(f"File size exceeds maximum allowed size of {max_size} bytes")
        return v


class ImportTaskUpdate(BaseModel):
    """
    Schema for updating an import task.

    All fields are optional - only provided fields will be updated.
    """
    status: Optional[ImportStatus] = Field(None, description="Import task status")
    total_rows: Optional[int] = Field(None, ge=0, description="Total rows to process")
    processed_rows: Optional[int] = Field(None, ge=0, description="Number of rows processed")
    progress_percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Progress percentage")
    error_count: Optional[int] = Field(None, ge=0, description="Number of errors")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    validation_errors: Optional[List[Dict[str, Any]]] = Field(None, description="List of validation errors")
    parsing_metadata: Optional[Dict[str, Any]] = Field(None, description="Parsing metadata")
    dataset_id: Optional[str] = Field(None, description="ID of created/updated dataset")

    @field_validator("processed_rows")
    @classmethod
    def validate_processed_rows(cls, v: Optional[int], info) -> Optional[int]:
        """Validate processed_rows doesn't exceed total_rows"""
        if v is not None and v < 0:
            raise ValueError("Processed rows must be non-negative")
        return v


class ImportTaskResponse(BaseModel):
    """
    Schema for import task response.

    This schema is used for API responses.
    """
    id: str
    task_name: str
    import_type: str
    status: str
    original_filename: str
    file_path: str
    file_size: int
    total_rows: int
    processed_rows: int
    progress_percentage: float
    error_count: int
    error_message: Optional[str] = None
    validation_errors: Optional[List[Dict[str, Any]]] = None
    parsing_metadata: Optional[Dict[str, Any]] = None
    import_config: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    dataset_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "task_name": "Import Stock Data 2024",
                "import_type": "csv",
                "status": "completed",
                "original_filename": "stocks_2024.csv",
                "file_path": "/uploads/stocks_2024_uuid.csv",
                "file_size": 1048576,
                "total_rows": 10000,
                "processed_rows": 10000,
                "progress_percentage": 100.0,
                "error_count": 0,
                "error_message": None,
                "validation_errors": None,
                "parsing_metadata": {
                    "columns": ["date", "open", "high", "low", "close", "volume"],
                    "encoding": "utf-8",
                    "delimiter": ","
                },
                "import_config": {"skip_rows": 0, "header": 0},
                "user_id": "user-123",
                "dataset_id": "dataset-456",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:05:00Z"
            }
        }
    )


class ImportTaskListResponse(BaseModel):
    """
    Schema for paginated import task list response.

    Attributes:
        total: Total number of import tasks
        items: List of import tasks in current page
    """
    total: int = Field(..., ge=0, description="Total number of import tasks")
    items: List[ImportTaskResponse] = Field(..., description="List of import tasks")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 50,
                "items": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "task_name": "Import Stock Data 2024",
                        "import_type": "csv",
                        "status": "completed",
                        "original_filename": "stocks_2024.csv",
                        "file_path": "/uploads/stocks_2024.csv",
                        "file_size": 1048576,
                        "total_rows": 10000,
                        "processed_rows": 10000,
                        "progress_percentage": 100.0,
                        "error_count": 0,
                        "error_message": None,
                        "validation_errors": None,
                        "parsing_metadata": {"columns": ["date", "price"], "encoding": "utf-8"},
                        "import_config": {},
                        "user_id": None,
                        "dataset_id": "dataset-123",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                ]
            }
        }
    )


class FileValidationResult(BaseModel):
    """
    Schema for file validation result.

    Used internally to track validation status.
    """
    is_valid: bool = Field(..., description="Whether file passed validation")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of validation warnings")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Validation metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_valid": True,
                "errors": [],
                "warnings": ["Column 'volume' has 5 missing values"],
                "metadata": {
                    "encoding": "utf-8",
                    "delimiter": ",",
                    "total_rows": 10000,
                    "columns": ["date", "open", "high", "low", "close", "volume"]
                }
            }
        }
    )


class DataProcessingResult(BaseModel):
    """
    Schema for data processing result.

    Used internally to track processing status and results.
    """
    success: bool = Field(..., description="Whether processing succeeded")
    rows_processed: int = Field(..., ge=0, description="Number of rows processed")
    rows_skipped: int = Field(default=0, ge=0, description="Number of rows skipped")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of processing errors")
    dataset_id: Optional[str] = Field(None, description="ID of created dataset")
    dataset_metadata: Dict[str, Any] = Field(default_factory=dict, description="Dataset metadata")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "rows_processed": 9995,
                "rows_skipped": 5,
                "errors": [],
                "dataset_id": "dataset-123",
                "dataset_metadata": {
                    "columns": ["date", "open", "high", "low", "close", "volume"],
                    "row_count": 9995,
                    "data_types": {
                        "date": "datetime",
                        "open": "float64",
                        "high": "float64",
                        "low": "float64",
                        "close": "float64",
                        "volume": "int64"
                    }
                }
            }
        }
    )


class ImportProgressUpdate(BaseModel):
    """
    Schema for import progress update.

    Used for real-time progress tracking.
    """
    task_id: str = Field(..., description="Import task ID")
    status: ImportStatus = Field(..., description="Current status")
    progress_percentage: float = Field(..., ge=0.0, le=100.0, description="Progress percentage")
    processed_rows: int = Field(..., ge=0, description="Rows processed")
    total_rows: int = Field(..., ge=0, description="Total rows")
    current_step: str = Field(..., description="Current processing step")
    message: Optional[str] = Field(None, description="Status message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "task-123",
                "status": "processing",
                "progress_percentage": 45.5,
                "processed_rows": 4550,
                "total_rows": 10000,
                "current_step": "Validating data types",
                "message": "Processing row 4550 of 10000"
            }
        }
    )
