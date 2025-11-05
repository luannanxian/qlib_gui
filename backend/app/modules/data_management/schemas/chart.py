"""Chart Schemas for Data Management Module"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from app.modules.data_management.models.chart import ChartType


class ChartConfigCreate(BaseModel):
    """Schema for creating a new chart configuration"""
    name: str
    chart_type: ChartType
    dataset_id: str
    config: Dict[str, Any] = Field(default_factory=dict)


class ChartConfigUpdate(BaseModel):
    """Schema for updating a chart configuration"""
    name: Optional[str] = None
    chart_type: Optional[ChartType] = None
    config: Optional[Dict[str, Any]] = None


class ChartConfigResponse(BaseModel):
    """Schema for chart configuration response"""
    id: str
    name: str
    chart_type: ChartType
    dataset_id: str
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChartConfigListResponse(BaseModel):
    """Schema for chart configuration list response"""
    total: int
    items: List[ChartConfigResponse]
