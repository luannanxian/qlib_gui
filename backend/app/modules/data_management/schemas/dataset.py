"""Dataset Schemas for Data Management Module"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel
from app.modules.data_management.models.dataset import DataSource, DatasetStatus


class DatasetCreate(BaseModel):
    """Schema for creating a new dataset"""
    name: str
    source: DataSource
    file_path: str


class DatasetUpdate(BaseModel):
    """Schema for updating a dataset"""
    name: Optional[str] = None
    status: Optional[DatasetStatus] = None
    row_count: Optional[int] = None
    columns: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class DatasetResponse(BaseModel):
    """Schema for dataset response"""
    id: str
    name: str
    source: DataSource
    file_path: str
    status: DatasetStatus
    row_count: int
    columns: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    """Schema for dataset list response"""
    total: int
    items: List[DatasetResponse]
