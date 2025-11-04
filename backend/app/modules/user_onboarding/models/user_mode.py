"""
User Mode and Preferences Models
"""

from enum import Enum
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class UserMode(str, Enum):
    """User mode enum: beginner or expert"""
    BEGINNER = "beginner"
    EXPERT = "expert"


class UserPreferences(BaseModel):
    """User preferences and settings model"""
    user_id: str
    mode: UserMode
    completed_guides: List[str] = Field(default_factory=list)
    show_tooltips: bool = True
    language: str = "zh-CN"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
