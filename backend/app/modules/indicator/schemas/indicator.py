"""Indicator Schemas for Indicator Module"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class IndicatorResponse(BaseModel):
    """
    Schema for indicator response.

    This schema represents a technical indicator component with all metadata.
    """
    id: str
    code: str = Field(..., description="Indicator code (e.g., SMA, RSI)")
    name_zh: str = Field(..., description="Chinese name")
    name_en: str = Field(..., description="English name")
    category: str = Field(..., description="Indicator category")
    source: str = Field(..., description="Indicator source (e.g., talib, custom)")
    description_zh: Optional[str] = Field(None, description="Chinese description")
    description_en: Optional[str] = Field(None, description="English description")
    formula: Optional[str] = Field(None, description="Calculation formula")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parameter definitions")
    default_params: Optional[Dict[str, Any]] = Field(None, description="Default parameter values")
    usage_count: int = Field(0, ge=0, description="Number of times used")
    is_enabled: bool = Field(True, description="Whether indicator is enabled")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "code": "SMA",
                "name_zh": "简单移动平均线",
                "name_en": "Simple Moving Average",
                "category": "trend",
                "source": "talib",
                "description_zh": "简单移动平均线指标",
                "description_en": "Simple Moving Average indicator",
                "formula": "SUM(close, period) / period",
                "parameters": {"period": {"type": "int", "min": 1, "max": 200}},
                "default_params": {"period": 20},
                "usage_count": 150,
                "is_enabled": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    )


class IndicatorListResponse(BaseModel):
    """
    Schema for paginated indicator list response.

    Attributes:
        total: Total number of indicators
        skip: Number of records skipped
        limit: Maximum records returned
        indicators: List of indicators
    """
    total: int = Field(..., ge=0, description="Total number of indicators")
    skip: int = Field(0, ge=0, description="Number of records skipped")
    limit: int = Field(100, ge=1, description="Maximum records returned")
    indicators: List[IndicatorResponse] = Field(..., description="List of indicators")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 50,
                "skip": 0,
                "limit": 20,
                "indicators": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "code": "SMA",
                        "name_zh": "简单移动平均线",
                        "name_en": "Simple Moving Average",
                        "category": "trend",
                        "source": "talib",
                        "usage_count": 150,
                        "is_enabled": True,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                ]
            }
        }
    )


class IndicatorCategoryResponse(BaseModel):
    """
    Schema for indicator category.

    Attributes:
        value: Category enum value
        label: Category display name
    """
    value: str = Field(..., description="Category value")
    label: str = Field(..., description="Category label")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "value": "trend",
                "label": "TREND"
            }
        }
    )


class IndicatorCategoryListResponse(BaseModel):
    """
    Schema for indicator category list response.

    Attributes:
        total: Total number of categories
        categories: List of categories
    """
    total: int = Field(..., ge=0, description="Total number of categories")
    categories: List[IndicatorCategoryResponse] = Field(..., description="List of categories")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 5,
                "categories": [
                    {"value": "trend", "label": "TREND"},
                    {"value": "momentum", "label": "MOMENTUM"},
                    {"value": "volatility", "label": "VOLATILITY"}
                ]
            }
        }
    )
