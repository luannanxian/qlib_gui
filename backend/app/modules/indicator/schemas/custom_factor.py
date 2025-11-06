"""Custom Factor Schemas for Indicator Module"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class CustomFactorCreate(BaseModel):
    """
    Schema for creating a new custom factor.

    Attributes:
        factor_name: Factor name (required)
        formula: Factor calculation formula (required)
        formula_language: Formula language (qlib_alpha, python, pandas)
        description: Factor description (optional)
        base_indicator_id: Base indicator ID (optional)
        is_public: Whether factor is publicly visible (default: False)
    """
    factor_name: str = Field(..., min_length=1, max_length=255, description="Factor name")
    formula: str = Field(..., min_length=1, description="Factor calculation formula")
    formula_language: str = Field(..., description="Formula language (qlib_alpha, python, pandas)")
    description: Optional[str] = Field(None, max_length=1000, description="Factor description")
    base_indicator_id: Optional[str] = Field(None, description="Base indicator ID")
    is_public: bool = Field(False, description="Whether factor is publicly visible")

    @field_validator("factor_name")
    @classmethod
    def validate_factor_name(cls, v: str) -> str:
        """Validate factor name is not just whitespace"""
        if not v or not v.strip():
            raise ValueError("Factor name cannot be empty or whitespace")
        return v.strip()

    @field_validator("formula")
    @classmethod
    def validate_formula(cls, v: str) -> str:
        """Validate formula is not empty"""
        if not v or not v.strip():
            raise ValueError("Formula cannot be empty or whitespace")
        return v.strip()

    @field_validator("formula_language")
    @classmethod
    def validate_formula_language(cls, v: str) -> str:
        """Validate formula language is supported"""
        # Remove client-side validation to allow service layer to handle it with proper error code
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "factor_name": "My Custom Factor",
                "formula": "close / open - 1",
                "formula_language": "qlib_alpha",
                "description": "Daily return based on close/open ratio",
                "tags": ["return", "daily"],
                "is_public": False
            }
        }
    )


class CustomFactorUpdate(BaseModel):
    """
    Schema for updating a custom factor.

    All fields are optional - only provided fields will be updated.
    """
    factor_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Factor name")
    formula: Optional[str] = Field(None, min_length=1, description="Factor calculation formula")
    formula_language: Optional[str] = Field(None, description="Formula language")
    description: Optional[str] = Field(None, max_length=1000, description="Factor description")
    tags: Optional[List[str]] = Field(None, description="Factor tags")
    is_public: Optional[bool] = Field(None, description="Whether factor is publicly visible")

    @field_validator("factor_name")
    @classmethod
    def validate_factor_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate factor name if provided"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Factor name cannot be empty or whitespace")
        return v.strip() if v else None

    @field_validator("formula")
    @classmethod
    def validate_formula(cls, v: Optional[str]) -> Optional[str]:
        """Validate formula if provided"""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Formula cannot be empty or whitespace")
        return v.strip() if v else None

    @field_validator("formula_language")
    @classmethod
    def validate_formula_language(cls, v: Optional[str]) -> Optional[str]:
        """Validate formula language if provided"""
        if v is not None:
            valid_languages = ['qlib_alpha', 'python', 'pandas']
            if v not in valid_languages:
                raise ValueError(f"Invalid formula_language. Must be one of: {', '.join(valid_languages)}")
        return v


class CustomFactorResponse(BaseModel):
    """
    Schema for custom factor response.

    This schema represents a custom factor with all metadata.
    """
    id: str
    factor_name: str = Field(..., description="Factor name")
    user_id: str = Field(..., description="Owner user ID")
    base_indicator_id: Optional[str] = Field(None, description="Base indicator ID")
    formula: str = Field(..., description="Factor calculation formula")
    formula_language: str = Field(..., description="Formula language")
    description: Optional[str] = Field(None, description="Factor description")
    status: str = Field(..., description="Factor status (draft, published, archived)")
    is_public: bool = Field(False, description="Whether factor is publicly visible")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    shared_at: Optional[datetime] = Field(None, description="Public sharing timestamp")
    usage_count: int = Field(0, ge=0, description="Number of times used")
    clone_count: int = Field(0, ge=0, description="Number of times cloned")
    cloned_from_id: Optional[str] = Field(None, description="Source factor ID if cloned")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "factor_name": "My Custom Factor",
                "user_id": "user123",
                "formula": "close / open - 1",
                "formula_language": "qlib_alpha",
                "description": "Daily return based on close/open ratio",
                "tags": ["return", "daily"],
                "status": "published",
                "is_public": True,
                "usage_count": 25,
                "parent_factor_id": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    )


class CustomFactorListResponse(BaseModel):
    """
    Schema for paginated custom factor list response.

    Attributes:
        total: Total number of factors
        skip: Number of records skipped
        limit: Maximum records returned
        factors: List of custom factors
    """
    total: int = Field(..., ge=0, description="Total number of factors")
    skip: int = Field(0, ge=0, description="Number of records skipped")
    limit: int = Field(100, ge=1, description="Maximum records returned")
    factors: List[CustomFactorResponse] = Field(..., description="List of custom factors")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 10,
                "skip": 0,
                "limit": 20,
                "factors": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "factor_name": "My Custom Factor",
                        "user_id": "user123",
                        "formula": "close / open - 1",
                        "formula_language": "qlib_alpha",
                        "status": "published",
                        "is_public": True,
                        "usage_count": 25,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                ]
            }
        }
    )


class PublishFactorRequest(BaseModel):
    """
    Schema for publishing a factor.

    Attributes:
        is_public: Whether to make the factor public (optional)
    """
    is_public: bool = Field(False, description="Whether to make the factor public")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_public": True
            }
        }
    )


class CloneFactorRequest(BaseModel):
    """
    Schema for cloning a factor.

    Attributes:
        new_name: Name for the cloned factor (required)
    """
    new_name: str = Field(..., min_length=1, max_length=255, description="Name for cloned factor")

    @field_validator("new_name")
    @classmethod
    def validate_new_name(cls, v: str) -> str:
        """Validate new name"""
        if not v or not v.strip():
            raise ValueError("New name cannot be empty or whitespace")
        return v.strip()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "new_name": "My Cloned Factor"
            }
        }
    )
