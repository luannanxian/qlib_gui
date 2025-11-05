"""Dataset Models for Data Management Module"""

from enum import Enum
from typing import List, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
import uuid


class DataSource(str, Enum):
    """Data source types"""
    LOCAL = "local"
    QLIB = "qlib"
    THIRDPARTY = "thirdparty"


class DatasetStatus(str, Enum):
    """Dataset status types"""
    VALID = "valid"
    INVALID = "invalid"
    PENDING = "pending"


class Dataset(BaseModel):
    """Dataset model for managing uploaded and imported data"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    source: DataSource
    file_path: str
    status: DatasetStatus = DatasetStatus.PENDING
    row_count: int = 0
    columns: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  # UTC with timezone
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  # UTC with timezone

    @field_validator('row_count')
    @classmethod
    def validate_row_count(cls, v: int) -> int:
        """Validate that row_count is non-negative"""
        if v < 0:
            raise ValueError('row_count must be non-negative')
        return v

    def __str__(self) -> str:
        """String representation of Dataset"""
        return f"Dataset(name='{self.name}', source='{self.source.value}')"

    class Config:
        use_enum_values = False
