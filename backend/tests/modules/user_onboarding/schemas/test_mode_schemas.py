"""
Tests for Mode Schemas (TDD - RED phase)
"""

import pytest
from datetime import datetime


class TestModeUpdateRequest:
    """Test ModeUpdateRequest schema"""

    def test_mode_update_request_creation(self):
        """Test creating ModeUpdateRequest"""
        from app.modules.user_onboarding.schemas.mode_schemas import ModeUpdateRequest
        from app.modules.user_onboarding.models.user_mode import UserMode

        request = ModeUpdateRequest(mode=UserMode.EXPERT)
        assert request.mode == UserMode.EXPERT

    def test_mode_update_request_validation(self):
        """Test ModeUpdateRequest validates mode"""
        from app.modules.user_onboarding.schemas.mode_schemas import ModeUpdateRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ModeUpdateRequest(mode="invalid_mode")

    def test_mode_update_request_serialization(self):
        """Test ModeUpdateRequest serialization"""
        from app.modules.user_onboarding.schemas.mode_schemas import ModeUpdateRequest
        from app.modules.user_onboarding.models.user_mode import UserMode

        request = ModeUpdateRequest(mode=UserMode.BEGINNER)
        data = request.model_dump()
        assert data["mode"] == "beginner"


class TestModeResponse:
    """Test ModeResponse schema"""

    def test_mode_response_creation(self):
        """Test creating ModeResponse"""
        from app.modules.user_onboarding.schemas.mode_schemas import ModeResponse
        from app.modules.user_onboarding.models.user_mode import UserMode

        response = ModeResponse(
            user_id="user-123",
            mode=UserMode.EXPERT
        )
        
        assert response.user_id == "user-123"
        assert response.mode == UserMode.EXPERT
        assert isinstance(response.updated_at, datetime)

    def test_mode_response_with_custom_timestamp(self):
        """Test ModeResponse with custom timestamp"""
        from app.modules.user_onboarding.schemas.mode_schemas import ModeResponse
        from app.modules.user_onboarding.models.user_mode import UserMode

        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        response = ModeResponse(
            user_id="user-456",
            mode=UserMode.BEGINNER,
            updated_at=custom_time
        )
        
        assert response.updated_at == custom_time

    def test_mode_response_serialization(self):
        """Test ModeResponse serialization"""
        from app.modules.user_onboarding.schemas.mode_schemas import ModeResponse
        from app.modules.user_onboarding.models.user_mode import UserMode

        response = ModeResponse(
            user_id="user-789",
            mode=UserMode.EXPERT
        )
        
        data = response.model_dump()
        assert data["user_id"] == "user-789"
        assert data["mode"] == "expert"
        assert "updated_at" in data


class TestPreferencesUpdateRequest:
    """Test PreferencesUpdateRequest schema"""

    def test_preferences_update_request_minimal(self):
        """Test PreferencesUpdateRequest with minimal fields"""
        from app.modules.user_onboarding.schemas.mode_schemas import PreferencesUpdateRequest

        request = PreferencesUpdateRequest()
        assert request.show_tooltips is None
        assert request.language is None
        assert request.completed_guides is None

    def test_preferences_update_request_with_values(self):
        """Test PreferencesUpdateRequest with values"""
        from app.modules.user_onboarding.schemas.mode_schemas import PreferencesUpdateRequest

        request = PreferencesUpdateRequest(
            show_tooltips=False,
            language="en-US",
            completed_guides=["guide-1", "guide-2"]
        )
        
        assert request.show_tooltips is False
        assert request.language == "en-US"
        assert request.completed_guides == ["guide-1", "guide-2"]

    def test_preferences_update_request_partial_update(self):
        """Test PreferencesUpdateRequest supports partial updates"""
        from app.modules.user_onboarding.schemas.mode_schemas import PreferencesUpdateRequest

        # Only updating language
        request = PreferencesUpdateRequest(language="ja-JP")
        assert request.language == "ja-JP"
        assert request.show_tooltips is None
        assert request.completed_guides is None


class TestPreferencesResponse:
    """Test PreferencesResponse schema"""

    def test_preferences_response_creation(self):
        """Test creating PreferencesResponse"""
        from app.modules.user_onboarding.schemas.mode_schemas import PreferencesResponse
        from app.modules.user_onboarding.models.user_mode import UserMode

        response = PreferencesResponse(
            user_id="user-123",
            mode=UserMode.BEGINNER,
            completed_guides=[],
            show_tooltips=True,
            language="zh-CN",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert response.user_id == "user-123"
        assert response.mode == UserMode.BEGINNER
        assert response.completed_guides == []
        assert response.show_tooltips is True
        assert response.language == "zh-CN"

    def test_preferences_response_from_model(self):
        """Test creating PreferencesResponse from UserPreferences model"""
        from app.modules.user_onboarding.schemas.mode_schemas import PreferencesResponse
        from app.modules.user_onboarding.models.user_mode import UserPreferences, UserMode

        prefs = UserPreferences(
            user_id="user-456",
            mode=UserMode.EXPERT,
            completed_guides=["guide-1"],
            show_tooltips=False,
            language="en-US"
        )
        
        response = PreferencesResponse(
            user_id=prefs.user_id,
            mode=prefs.mode,
            completed_guides=prefs.completed_guides,
            show_tooltips=prefs.show_tooltips,
            language=prefs.language,
            created_at=prefs.created_at,
            updated_at=prefs.updated_at
        )
        
        assert response.user_id == prefs.user_id
        assert response.mode == prefs.mode
        assert response.completed_guides == prefs.completed_guides

    def test_preferences_response_serialization(self):
        """Test PreferencesResponse serialization"""
        from app.modules.user_onboarding.schemas.mode_schemas import PreferencesResponse
        from app.modules.user_onboarding.models.user_mode import UserMode

        response = PreferencesResponse(
            user_id="user-789",
            mode=UserMode.EXPERT,
            completed_guides=["guide-1", "guide-2"],
            show_tooltips=False,
            language="zh-CN",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        data = response.model_dump()
        assert data["user_id"] == "user-789"
        assert data["mode"] == "expert"
        assert len(data["completed_guides"]) == 2
        assert data["show_tooltips"] is False
