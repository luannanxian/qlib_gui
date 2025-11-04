"""
Tests for ModeService (TDD - RED phase)
"""

import pytest
from datetime import datetime


class TestModeService:
    """Test ModeService for mode management"""

    def test_mode_service_creation(self):
        """Test creating ModeService instance"""
        from app.modules.user_onboarding.services.mode_service import ModeService

        service = ModeService()
        assert service is not None

    def test_get_default_mode(self):
        """Test getting default mode for new user"""
        from app.modules.user_onboarding.services.mode_service import ModeService
        from app.modules.user_onboarding.models.user_mode import UserMode

        service = ModeService()
        mode = service.get_default_mode()
        assert mode == UserMode.BEGINNER

    def test_switch_mode_beginner_to_expert(self):
        """Test switching from beginner to expert mode"""
        from app.modules.user_onboarding.services.mode_service import ModeService
        from app.modules.user_onboarding.models.user_mode import UserMode

        service = ModeService()
        result = service.switch_mode(
            user_id="user-123",
            current_mode=UserMode.BEGINNER,
            new_mode=UserMode.EXPERT
        )
        
        assert result.mode == UserMode.EXPERT
        assert result.user_id == "user-123"
        assert isinstance(result.updated_at, datetime)

    def test_switch_mode_expert_to_beginner(self):
        """Test switching from expert to beginner mode"""
        from app.modules.user_onboarding.services.mode_service import ModeService
        from app.modules.user_onboarding.models.user_mode import UserMode

        service = ModeService()
        result = service.switch_mode(
            user_id="user-456",
            current_mode=UserMode.EXPERT,
            new_mode=UserMode.BEGINNER
        )
        
        assert result.mode == UserMode.BEGINNER

    def test_switch_mode_same_mode_allowed(self):
        """Test that switching to same mode is allowed (idempotent)"""
        from app.modules.user_onboarding.services.mode_service import ModeService
        from app.modules.user_onboarding.models.user_mode import UserMode

        service = ModeService()
        result = service.switch_mode(
            user_id="user-789",
            current_mode=UserMode.BEGINNER,
            new_mode=UserMode.BEGINNER
        )
        
        assert result.mode == UserMode.BEGINNER

    def test_create_default_preferences(self):
        """Test creating default user preferences"""
        from app.modules.user_onboarding.services.mode_service import ModeService
        from app.modules.user_onboarding.models.user_mode import UserMode

        service = ModeService()
        prefs = service.create_default_preferences(user_id="user-111")
        
        assert prefs.user_id == "user-111"
        assert prefs.mode == UserMode.BEGINNER
        assert prefs.completed_guides == []
        assert prefs.show_tooltips is True
        assert prefs.language == "zh-CN"

    def test_update_preferences_show_tooltips(self):
        """Test updating show_tooltips preference"""
        from app.modules.user_onboarding.services.mode_service import ModeService
        from app.modules.user_onboarding.models.user_mode import UserPreferences, UserMode

        service = ModeService()
        current_prefs = UserPreferences(user_id="user-222", mode=UserMode.BEGINNER)
        
        updated_prefs = service.update_preferences(
            current_prefs=current_prefs,
            show_tooltips=False
        )
        
        assert updated_prefs.show_tooltips is False
        assert updated_prefs.user_id == "user-222"

    def test_update_preferences_language(self):
        """Test updating language preference"""
        from app.modules.user_onboarding.services.mode_service import ModeService
        from app.modules.user_onboarding.models.user_mode import UserPreferences, UserMode

        service = ModeService()
        current_prefs = UserPreferences(user_id="user-333", mode=UserMode.EXPERT)
        
        updated_prefs = service.update_preferences(
            current_prefs=current_prefs,
            language="en-US"
        )
        
        assert updated_prefs.language == "en-US"

    def test_update_preferences_completed_guides(self):
        """Test updating completed guides"""
        from app.modules.user_onboarding.services.mode_service import ModeService
        from app.modules.user_onboarding.models.user_mode import UserPreferences, UserMode

        service = ModeService()
        current_prefs = UserPreferences(user_id="user-444", mode=UserMode.BEGINNER)
        
        updated_prefs = service.update_preferences(
            current_prefs=current_prefs,
            completed_guides=["guide-1", "guide-2"]
        )
        
        assert updated_prefs.completed_guides == ["guide-1", "guide-2"]

    def test_update_preferences_partial_update(self):
        """Test partial preferences update (only some fields)"""
        from app.modules.user_onboarding.services.mode_service import ModeService
        from app.modules.user_onboarding.models.user_mode import UserPreferences, UserMode

        service = ModeService()
        current_prefs = UserPreferences(
            user_id="user-555",
            mode=UserMode.EXPERT,
            show_tooltips=True,
            language="zh-CN"
        )
        
        # Only update language, other fields should remain
        updated_prefs = service.update_preferences(
            current_prefs=current_prefs,
            language="ja-JP"
        )
        
        assert updated_prefs.language == "ja-JP"
        assert updated_prefs.show_tooltips is True  # Unchanged
        assert updated_prefs.user_id == "user-555"  # Unchanged

    def test_update_preferences_updates_timestamp(self):
        """Test that updating preferences updates the timestamp"""
        from app.modules.user_onboarding.services.mode_service import ModeService
        from app.modules.user_onboarding.models.user_mode import UserPreferences, UserMode
        import time

        service = ModeService()
        current_prefs = UserPreferences(user_id="user-666", mode=UserMode.BEGINNER)
        original_updated_at = current_prefs.updated_at
        
        time.sleep(0.01)  # Small delay to ensure timestamp difference
        
        updated_prefs = service.update_preferences(
            current_prefs=current_prefs,
            language="en-US"
        )
        
        assert updated_prefs.updated_at > original_updated_at

    def test_add_completed_guide(self):
        """Test adding a guide to completed guides"""
        from app.modules.user_onboarding.services.mode_service import ModeService
        from app.modules.user_onboarding.models.user_mode import UserPreferences, UserMode

        service = ModeService()
        current_prefs = UserPreferences(
            user_id="user-777",
            mode=UserMode.BEGINNER,
            completed_guides=["guide-1"]
        )
        
        updated_prefs = service.add_completed_guide(
            current_prefs=current_prefs,
            guide_id="guide-2"
        )
        
        assert "guide-1" in updated_prefs.completed_guides
        assert "guide-2" in updated_prefs.completed_guides
        assert len(updated_prefs.completed_guides) == 2

    def test_add_completed_guide_no_duplicates(self):
        """Test that adding same guide twice doesn't create duplicates"""
        from app.modules.user_onboarding.services.mode_service import ModeService
        from app.modules.user_onboarding.models.user_mode import UserPreferences, UserMode

        service = ModeService()
        current_prefs = UserPreferences(
            user_id="user-888",
            mode=UserMode.BEGINNER,
            completed_guides=["guide-1"]
        )
        
        updated_prefs = service.add_completed_guide(
            current_prefs=current_prefs,
            guide_id="guide-1"  # Same guide again
        )
        
        assert updated_prefs.completed_guides == ["guide-1"]
        assert len(updated_prefs.completed_guides) == 1

    def test_is_guide_completed(self):
        """Test checking if a guide is completed"""
        from app.modules.user_onboarding.services.mode_service import ModeService
        from app.modules.user_onboarding.models.user_mode import UserPreferences, UserMode

        service = ModeService()
        prefs = UserPreferences(
            user_id="user-999",
            mode=UserMode.BEGINNER,
            completed_guides=["guide-1", "guide-2"]
        )
        
        assert service.is_guide_completed(prefs, "guide-1") is True
        assert service.is_guide_completed(prefs, "guide-2") is True
        assert service.is_guide_completed(prefs, "guide-3") is False
