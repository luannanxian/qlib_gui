"""
Mode Service - Business logic for mode management
"""

from datetime import datetime
from typing import Optional, List

from app.modules.user_onboarding.models.user_mode import UserMode, UserPreferences
from app.modules.user_onboarding.schemas.mode_schemas import ModeResponse


class ModeService:
    """Service for managing user modes and preferences"""

    def get_default_mode(self) -> UserMode:
        """Get the default mode for new users"""
        return UserMode.BEGINNER

    def switch_mode(
        self, 
        user_id: str, 
        current_mode: UserMode, 
        new_mode: UserMode
    ) -> ModeResponse:
        """Switch user mode"""
        return ModeResponse(
            user_id=user_id,
            mode=new_mode,
            updated_at=datetime.now()
        )

    def create_default_preferences(self, user_id: str) -> UserPreferences:
        """Create default preferences for a new user"""
        return UserPreferences(
            user_id=user_id,
            mode=self.get_default_mode()
        )

    def update_preferences(
        self,
        current_prefs: UserPreferences,
        show_tooltips: Optional[bool] = None,
        language: Optional[str] = None,
        completed_guides: Optional[List[str]] = None
    ) -> UserPreferences:
        """Update user preferences (partial update support)"""
        # Create updated preferences with new values
        updated_data = {
            "user_id": current_prefs.user_id,
            "mode": current_prefs.mode,
            "show_tooltips": show_tooltips if show_tooltips is not None else current_prefs.show_tooltips,
            "language": language if language is not None else current_prefs.language,
            "completed_guides": completed_guides if completed_guides is not None else current_prefs.completed_guides,
            "created_at": current_prefs.created_at,
            "updated_at": datetime.now()
        }
        
        return UserPreferences(**updated_data)

    def add_completed_guide(
        self, 
        current_prefs: UserPreferences, 
        guide_id: str
    ) -> UserPreferences:
        """Add a guide to completed guides list (no duplicates)"""
        completed_guides = current_prefs.completed_guides.copy()
        
        if guide_id not in completed_guides:
            completed_guides.append(guide_id)
        
        return self.update_preferences(
            current_prefs=current_prefs,
            completed_guides=completed_guides
        )

    def is_guide_completed(
        self, 
        prefs: UserPreferences, 
        guide_id: str
    ) -> bool:
        """Check if a guide has been completed"""
        return guide_id in prefs.completed_guides
