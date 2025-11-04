"""
Schemas for Mode Management API
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.modules.user_onboarding.models.user_mode import UserMode


class ModeUpdateRequest(BaseModel):
    """Request schema for updating user mode"""
    mode: UserMode


class ModeResponse(BaseModel):
    """Response schema for mode operations"""
    user_id: str
    mode: UserMode
    updated_at: datetime = Field(default_factory=datetime.now)


class PreferencesUpdateRequest(BaseModel):
    """Request schema for updating user preferences (partial update support)"""
    show_tooltips: Optional[bool] = None
    language: Optional[str] = None
    completed_guides: Optional[List[str]] = None


class PreferencesResponse(BaseModel):
    """Response schema for user preferences"""
    user_id: str
    mode: UserMode
    completed_guides: List[str]
    show_tooltips: bool
    language: str
    created_at: datetime
    updated_at: datetime
