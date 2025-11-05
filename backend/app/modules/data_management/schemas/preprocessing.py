"""Preprocessing Schemas for Data Management Module

This module defines Pydantic schemas for preprocessing API requests and responses.
All schemas follow RESTful API design principles with proper validation.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


# ==================== Preprocessing Rule Schemas ====================

class PreprocessingRuleCreate(BaseModel):
    """
    Schema for creating a new preprocessing rule/template.

    Attributes:
        name: Rule/template name (unique per user)
        description: Optional description of what the rule does
        rule_type: Type of preprocessing (missing_value, outlier_detection, transformation, filtering)
        configuration: Rule configuration (structure depends on rule_type)
        is_template: Whether this is a reusable template
        user_id: User who owns this template (optional)
        dataset_id: Reference dataset ID (optional)
    """
    name: str = Field(..., min_length=1, max_length=255, description="Rule/template name")
    description: Optional[str] = Field(None, description="Rule description")
    rule_type: str = Field(
        ...,
        description="Type of preprocessing rule",
        pattern="^(missing_value|outlier_detection|transformation|filtering)$"
    )
    configuration: Dict[str, Any] = Field(..., description="Rule configuration (JSON object)")
    is_template: bool = Field(default=False, description="Whether this is a reusable template")
    user_id: Optional[str] = Field(None, max_length=255, description="User ID (optional)")
    dataset_id: Optional[str] = Field(None, description="Reference dataset ID (optional)")
    extra_metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata (tags, affected columns, etc.)"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate rule name is not just whitespace"""
        if not v or not v.strip():
            raise ValueError("Rule name cannot be empty or whitespace")
        return v.strip()

    @field_validator("configuration")
    @classmethod
    def validate_configuration(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration is not empty"""
        if not v:
            raise ValueError("Configuration cannot be empty")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Remove Missing Prices",
                "description": "Delete rows with missing price values",
                "rule_type": "missing_value",
                "configuration": {
                    "method": "delete_rows",
                    "columns": ["price", "volume"]
                },
                "is_template": True,
                "user_id": "user123",
                "dataset_id": None,
                "extra_metadata": {
                    "tags": ["cleaning", "finance"],
                    "affected_columns": ["price", "volume"]
                }
            }
        }
    )


class PreprocessingRuleUpdate(BaseModel):
    """
    Schema for updating a preprocessing rule.

    All fields are optional - only provided fields will be updated.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    configuration: Optional[Dict[str, Any]] = Field(None, description="Rule configuration")
    is_template: Optional[bool] = Field(None, description="Template flag")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate rule name if provided"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Rule name cannot be empty or whitespace")
        return v.strip() if v else None

    @field_validator("configuration")
    @classmethod
    def validate_configuration(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate configuration if provided"""
        if v is not None and not v:
            raise ValueError("Configuration cannot be empty")
        return v


class PreprocessingRuleResponse(BaseModel):
    """
    Schema for preprocessing rule response.

    This schema is used for API responses and maps database fields.
    """
    id: str
    name: str
    description: Optional[str]
    rule_type: str
    configuration: Dict[str, Any]
    is_template: bool
    user_id: Optional[str]
    dataset_id: Optional[str]
    usage_count: int
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
                "name": "Remove Missing Prices",
                "description": "Delete rows with missing price values",
                "rule_type": "missing_value",
                "configuration": {
                    "method": "delete_rows",
                    "columns": ["price", "volume"]
                },
                "is_template": True,
                "user_id": "user123",
                "dataset_id": None,
                "usage_count": 5,
                "metadata": {
                    "tags": ["cleaning", "finance"]
                },
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    )


class PreprocessingRuleListResponse(BaseModel):
    """
    Schema for paginated preprocessing rule list response.

    Attributes:
        total: Total number of rules (across all pages)
        items: List of rules in current page
    """
    total: int = Field(..., ge=0, description="Total number of rules")
    items: List[PreprocessingRuleResponse] = Field(..., description="List of rules")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 10,
                "items": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "Remove Missing Prices",
                        "description": "Delete rows with missing price values",
                        "rule_type": "missing_value",
                        "configuration": {"method": "delete_rows", "columns": ["price"]},
                        "is_template": True,
                        "user_id": "user123",
                        "dataset_id": None,
                        "usage_count": 5,
                        "metadata": {},
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                ]
            }
        }
    )


# ==================== Preprocessing Execution Schemas ====================

class PreprocessingExecuteRequest(BaseModel):
    """
    Schema for executing preprocessing on a dataset.

    Attributes:
        dataset_id: Source dataset to preprocess
        rule_id: Optional preprocessing rule to use
        operations: List of preprocessing operations (if not using rule_id)
        output_dataset_name: Name for the output dataset
        user_id: User initiating the task (optional)
    """
    dataset_id: str = Field(..., description="Source dataset ID to preprocess")
    rule_id: Optional[str] = Field(None, description="Preprocessing rule ID to use (optional)")
    operations: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Preprocessing operations (if not using rule_id)"
    )
    output_dataset_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Output dataset name (auto-generated if not provided)"
    )
    user_id: Optional[str] = Field(None, max_length=255, description="User ID (optional)")

    @field_validator("operations")
    @classmethod
    def validate_operations(cls, v: Optional[List[Dict[str, Any]]], info) -> Optional[List[Dict[str, Any]]]:
        """Validate that either rule_id or operations is provided"""
        # Note: Can't access other fields in validator with Pydantic v2
        # This validation will be done in the API endpoint
        if v is not None and len(v) == 0:
            raise ValueError("Operations list cannot be empty")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dataset_id": "dataset-123",
                "rule_id": "rule-456",
                "output_dataset_name": "Cleaned Stock Data",
                "user_id": "user123"
            }
        }
    )


class PreprocessingExecuteResponse(BaseModel):
    """
    Schema for preprocessing execution response.

    Returns the created task ID for status tracking.
    """
    task_id: str = Field(..., description="Preprocessing task ID")
    task_name: str = Field(..., description="Task name")
    status: str = Field(..., description="Initial task status (usually 'pending')")
    dataset_id: str = Field(..., description="Source dataset ID")
    message: str = Field(..., description="Success message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "task-789",
                "task_name": "Preprocess dataset-123",
                "status": "pending",
                "dataset_id": "dataset-123",
                "message": "Preprocessing task created successfully"
            }
        }
    )


# ==================== Preprocessing Task Schemas ====================

class PreprocessingTaskResponse(BaseModel):
    """
    Schema for preprocessing task status response.

    Provides detailed information about task execution progress.
    """
    id: str
    task_name: str
    status: str
    dataset_id: str
    rule_id: Optional[str]
    output_dataset_id: Optional[str]
    execution_config: Dict[str, Any]
    total_operations: int
    completed_operations: int
    progress_percentage: float
    input_row_count: int
    output_row_count: int
    rows_affected: int
    error_count: int
    warning_count: int
    error_message: Optional[str]
    execution_results: Optional[Dict[str, Any]]
    execution_time_seconds: Optional[float]
    user_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "task-789",
                "task_name": "Preprocess Stock Data",
                "status": "completed",
                "dataset_id": "dataset-123",
                "rule_id": "rule-456",
                "output_dataset_id": "dataset-999",
                "execution_config": {
                    "method": "delete_rows",
                    "columns": ["price"]
                },
                "total_operations": 3,
                "completed_operations": 3,
                "progress_percentage": 100.0,
                "input_row_count": 10000,
                "output_row_count": 9500,
                "rows_affected": 500,
                "error_count": 0,
                "warning_count": 2,
                "error_message": None,
                "execution_results": {
                    "operations_applied": ["delete_rows"],
                    "statistics": {"rows_deleted": 500}
                },
                "execution_time_seconds": 2.5,
                "user_id": "user123",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:05Z"
            }
        }
    )


# ==================== Preprocessing Preview Schemas ====================

class PreprocessingPreviewRequest(BaseModel):
    """
    Schema for previewing preprocessing results.

    Attributes:
        dataset_id: Source dataset to preview
        operations: Preprocessing operations to apply
        preview_rows: Number of rows to preview (default: 100, max: 1000)
    """
    dataset_id: str = Field(..., description="Source dataset ID")
    operations: List[Dict[str, Any]] = Field(..., description="Preprocessing operations to apply")
    preview_rows: int = Field(default=100, ge=1, le=1000, description="Number of rows to preview")

    @field_validator("operations")
    @classmethod
    def validate_operations(cls, v: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate operations is not empty"""
        if not v:
            raise ValueError("Operations list cannot be empty")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "dataset_id": "dataset-123",
                "operations": [
                    {
                        "type": "missing_value",
                        "config": {
                            "method": "delete_rows",
                            "columns": ["price"]
                        }
                    }
                ],
                "preview_rows": 100
            }
        }
    )


class PreprocessingPreviewResponse(BaseModel):
    """
    Schema for preprocessing preview response.

    Returns preview of preprocessed data without persisting.
    """
    original_row_count: int = Field(..., description="Original number of rows")
    preview_row_count: int = Field(..., description="Number of rows in preview")
    estimated_output_rows: int = Field(..., description="Estimated total output rows")
    preview_data: List[Dict[str, Any]] = Field(..., description="Preview data (first N rows)")
    columns: List[str] = Field(..., description="Column names")
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Preview statistics (rows affected, etc.)"
    )
    warnings: List[str] = Field(default_factory=list, description="Warnings generated during preview")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "original_row_count": 10000,
                "preview_row_count": 95,
                "estimated_output_rows": 9500,
                "preview_data": [
                    {"date": "2024-01-01", "price": 100.5, "volume": 1000},
                    {"date": "2024-01-02", "price": 101.0, "volume": 1100}
                ],
                "columns": ["date", "price", "volume"],
                "statistics": {
                    "rows_deleted": 5,
                    "missing_values_handled": 5
                },
                "warnings": ["Column 'volume' has 2 missing values"]
            }
        }
    )
