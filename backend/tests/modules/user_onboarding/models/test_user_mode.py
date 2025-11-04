"""
Tests for UserMode and UserPreferences models (TDD - RED phase)
"""

import pytest
from datetime import datetime


class TestUserMode:
    """Test UserMode enum"""

    def test_user_mode_enum_values(self):
        """Test UserMode has correct enum values"""
        from app.modules.user_onboarding.models.user_mode import UserMode

        assert UserMode.BEGINNER.value == "beginner"
        assert UserMode.EXPERT.value == "expert"

    def test_user_mode_enum_members(self):
        """Test UserMode has exactly two members"""
        from app.modules.user_onboarding.models.user_mode import UserMode

        assert len(UserMode) == 2
        assert "BEGINNER" in UserMode.__members__
        assert "EXPERT" in UserMode.__members__

    def test_user_mode_string_representation(self):
        """Test UserMode string representation"""
        from app.modules.user_onboarding.models.user_mode import UserMode

        # Since UserMode inherits from (str, Enum), accessing .value gives the string
        assert UserMode.BEGINNER == "beginner"
        assert UserMode.EXPERT == "expert"


class TestUserPreferences:
    """Test UserPreferences model"""

    def test_user_preferences_creation(self):
        """Test creating UserPreferences with required fields"""
        from app.modules.user_onboarding.models.user_mode import UserPreferences, UserMode

        prefs = UserPreferences(
            user_id="user-123",
            mode=UserMode.BEGINNER
        )
        
        assert prefs.user_id == "user-123"
        assert prefs.mode == UserMode.BEGINNER
        assert prefs.completed_guides == []
        assert prefs.show_tooltips is True
        assert prefs.language == "zh-CN"
        assert isinstance(prefs.created_at, datetime)
        assert isinstance(prefs.updated_at, datetime)

    def test_user_preferences_with_custom_values(self):
        """Test UserPreferences with custom values"""
        from app.modules.user_onboarding.models.user_mode import UserPreferences, UserMode

        prefs = UserPreferences(
            user_id="user-456",
            mode=UserMode.EXPERT,
            completed_guides=["guide-1", "guide-2"],
            show_tooltips=False,
            language="en-US"
        )
        
        assert prefs.user_id == "user-456"
        assert prefs.mode == UserMode.EXPERT
        assert prefs.completed_guides == ["guide-1", "guide-2"]
        assert prefs.show_tooltips is False
        assert prefs.language == "en-US"

    def test_user_preferences_mode_validation(self):
        """Test UserPreferences validates mode enum"""
        from app.modules.user_onboarding.models.user_mode import UserPreferences
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            UserPreferences(
                user_id="user-123",
                mode="invalid_mode"  # Should fail validation
            )

    def test_user_preferences_serialization(self):
        """Test UserPreferences can be serialized to dict"""
        from app.modules.user_onboarding.models.user_mode import UserPreferences, UserMode

        prefs = UserPreferences(
            user_id="user-789",
            mode=UserMode.BEGINNER,
            completed_guides=["guide-1"]
        )
        
        data = prefs.model_dump()
        assert data["user_id"] == "user-789"
        assert data["mode"] == "beginner"
        assert data["completed_guides"] == ["guide-1"]
        assert "created_at" in data
        assert "updated_at" in data

    def test_user_preferences_json_serialization(self):
        """Test UserPreferences can be serialized to JSON"""
        from app.modules.user_onboarding.models.user_mode import UserPreferences, UserMode
        import json

        prefs = UserPreferences(
            user_id="user-999",
            mode=UserMode.EXPERT
        )
        
        json_str = prefs.model_dump_json()
        data = json.loads(json_str)
        assert data["user_id"] == "user-999"
        assert data["mode"] == "expert"

    def test_user_preferences_completed_guides_default(self):
        """Test completed_guides defaults to empty list"""
        from app.modules.user_onboarding.models.user_mode import UserPreferences, UserMode

        prefs = UserPreferences(user_id="user-111", mode=UserMode.BEGINNER)
        assert prefs.completed_guides == []
        assert isinstance(prefs.completed_guides, list)

    def test_user_preferences_add_completed_guide(self):
        """Test adding guide to completed_guides"""
        from app.modules.user_onboarding.models.user_mode import UserPreferences, UserMode

        prefs = UserPreferences(user_id="user-222", mode=UserMode.BEGINNER)
        prefs.completed_guides.append("guide-1")
        prefs.completed_guides.append("guide-2")
        
        assert len(prefs.completed_guides) == 2
        assert "guide-1" in prefs.completed_guides
        assert "guide-2" in prefs.completed_guides
