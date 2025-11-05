"""Chart Models for Data Management Module"""

from enum import Enum
from typing import Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid


class ChartType(str, Enum):
    """Chart type enumeration"""
    KLINE = "kline"
    LINE = "line"
    BAR = "bar"
    SCATTER = "scatter"
    HEATMAP = "heatmap"


class ChartConfig(BaseModel):
    """Chart configuration model for data visualization"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    chart_type: ChartType
    dataset_id: str
    config: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  # UTC with timezone
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  # UTC with timezone

    def __str__(self) -> str:
        """String representation of ChartConfig"""
        return f"ChartConfig(name='{self.name}', chart_type='{self.chart_type.value}')"

    class Config:
        use_enum_values = False
