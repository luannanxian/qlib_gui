"""
Tests for Mode API endpoints with Database Persistence
"""

import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.user_preferences import UserPreferencesRepository
from app.modules.user_onboarding.api.dependencies import get_user_prefs_repo, get_current_user_id
from app.main import app


def override_get_current_user_id(user_id: str):
    """Helper to override get_current_user_id dependency"""
    def _get_user_id():
        return user_id
    return _get_user_id


def override_get_user_prefs_repo(repo: UserPreferencesRepository):
    """Helper to override get_user_prefs_repo dependency"""
    def _get_repo():
        return repo
    return _get_repo


@pytest.mark.asyncio
class TestGetCurrentMode:
    """Test GET /api/user/mode endpoint"""

    async def test_get_current_mode_returns_default_for_new_user(self, db_session: AsyncSession):
        """Test getting mode for new user returns BEGINNER"""
        user_id = "new-user-123"
        repo = UserPreferencesRepository(db_session)

        # Override dependencies
        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(repo)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/user/mode")

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["mode"] == "beginner"
                assert data["data"]["user_id"] == user_id

                # Verify data was saved to database
                saved_prefs = await repo.get_by_user_id(user_id)
                assert saved_prefs is not None
                assert saved_prefs.mode == "beginner"
        finally:
            app.dependency_overrides.clear()

    async def test_get_current_mode_returns_existing_mode(self, db_session: AsyncSession):
        """Test getting mode returns existing user's mode"""
        user_id = "existing-user-456"
        repo = UserPreferencesRepository(db_session)

        # Create user with expert mode
        await repo.create({
            "user_id": user_id,
            "mode": "expert",
            "language": "en",
            "show_tooltips": False
        })
        await db_session.commit()

        # Override dependencies
        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(repo)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/user/mode")

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["mode"] == "expert"
                assert data["data"]["user_id"] == user_id
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestUpdateMode:
    """Test POST /api/user/mode endpoint"""

    async def test_update_mode_to_expert(self, db_session: AsyncSession, mock_audit_logger):
        """Test switching to expert mode"""
        user_id = "user-123"
        repo = UserPreferencesRepository(db_session)

        # Override dependencies
        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(repo)

        # Mock audit logger
        with patch('app.modules.user_onboarding.api.mode_api.audit_logger', mock_audit_logger):
            try:
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.post(
                        "/api/user/mode",
                        json={"mode": "expert"}
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data["data"]["mode"] == "expert"
                    assert data["data"]["user_id"] == user_id

                    # Verify data persisted to database
                    saved_prefs = await repo.get_by_user_id(user_id)
                    assert saved_prefs is not None
                    assert saved_prefs.mode == "expert"

                    # Verify audit log was called
                    mock_audit_logger.log_event.assert_called_once()
            finally:
                app.dependency_overrides.clear()

    async def test_update_mode_to_beginner(self, db_session: AsyncSession):
        """Test switching to beginner mode"""
        user_id = "user-456"
        repo = UserPreferencesRepository(db_session)

        # Override dependencies
        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(repo)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/user/mode",
                    json={"mode": "beginner"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["data"]["mode"] == "beginner"

                # Verify data persisted
                saved_prefs = await repo.get_by_user_id(user_id)
                assert saved_prefs.mode == "beginner"
        finally:
            app.dependency_overrides.clear()

    async def test_update_mode_validates_mode_enum(self, db_session: AsyncSession):
        """Test that invalid mode is rejected"""
        user_id = "user-789"
        repo = UserPreferencesRepository(db_session)

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(repo)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/user/mode",
                    json={"mode": "invalid_mode"}
                )

                assert response.status_code == 422  # Validation error
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestGetPreferences:
    """Test GET /api/user/preferences endpoint"""

    async def test_get_preferences_returns_defaults_for_new_user(self, db_session: AsyncSession):
        """Test getting preferences for new user"""
        user_id = "new-user-999"
        repo = UserPreferencesRepository(db_session)

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(repo)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/user/preferences")

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["data"]["user_id"] == user_id
                assert data["data"]["mode"] == "beginner"
                assert data["data"]["show_tooltips"] is True
                assert data["data"]["language"] == "en"
                assert data["data"]["completed_guides"] == []

                # Verify data was saved
                saved_prefs = await repo.get_by_user_id(user_id)
                assert saved_prefs is not None
        finally:
            app.dependency_overrides.clear()

    async def test_get_preferences_returns_existing(self, db_session: AsyncSession):
        """Test getting existing preferences"""
        user_id = "existing-user-888"
        repo = UserPreferencesRepository(db_session)

        # Create user with custom preferences
        await repo.create({
            "user_id": user_id,
            "mode": "expert",
            "language": "zh-CN",
            "show_tooltips": False,
            "completed_guides": ["guide-1", "guide-2"]
        })
        await db_session.commit()

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(repo)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/user/preferences")

                assert response.status_code == 200
                data = response.json()
                assert data["data"]["mode"] == "expert"
                assert data["data"]["language"] == "zh-CN"
                assert data["data"]["show_tooltips"] is False
                assert len(data["data"]["completed_guides"]) == 2
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestUpdatePreferences:
    """Test PUT /api/user/preferences endpoint"""

    async def test_update_preferences_tooltips(self, db_session: AsyncSession, mock_audit_logger):
        """Test updating show_tooltips preference"""
        user_id = "user-111"
        repo = UserPreferencesRepository(db_session)

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(repo)

        with patch('app.modules.user_onboarding.api.mode_api.audit_logger', mock_audit_logger):
            try:
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.put(
                        "/api/user/preferences",
                        json={"show_tooltips": False}
                    )

                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data["data"]["show_tooltips"] is False

                    # Verify persistence
                    saved_prefs = await repo.get_by_user_id(user_id)
                    assert saved_prefs.show_tooltips is False

                    # Verify audit log
                    mock_audit_logger.log_event.assert_called_once()
            finally:
                app.dependency_overrides.clear()

    async def test_update_preferences_language(self, db_session: AsyncSession):
        """Test updating language preference"""
        user_id = "user-222"
        repo = UserPreferencesRepository(db_session)

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(repo)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.put(
                    "/api/user/preferences",
                    json={"language": "en-US"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["data"]["language"] == "en-US"

                # Verify persistence
                saved_prefs = await repo.get_by_user_id(user_id)
                assert saved_prefs.language == "en-US"
        finally:
            app.dependency_overrides.clear()

    async def test_update_preferences_completed_guides(self, db_session: AsyncSession):
        """Test updating completed guides"""
        user_id = "user-333"
        repo = UserPreferencesRepository(db_session)

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(repo)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.put(
                    "/api/user/preferences",
                    json={"completed_guides": ["guide-1", "guide-2"]}
                )

                assert response.status_code == 200
                data = response.json()
                assert len(data["data"]["completed_guides"]) == 2
                assert "guide-1" in data["data"]["completed_guides"]

                # Verify persistence
                saved_prefs = await repo.get_by_user_id(user_id)
                assert "guide-1" in saved_prefs.completed_guides
                assert "guide-2" in saved_prefs.completed_guides
        finally:
            app.dependency_overrides.clear()

    async def test_update_preferences_partial_update(self, db_session: AsyncSession):
        """Test partial update (only some fields)"""
        user_id = "user-444"
        repo = UserPreferencesRepository(db_session)

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(repo)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # First, get current preferences
                get_response = await client.get("/api/user/preferences")
                original_tooltips = get_response.json()["data"]["show_tooltips"]

                # Update only language
                update_response = await client.put(
                    "/api/user/preferences",
                    json={"language": "ja-JP"}
                )

                assert update_response.status_code == 200
                data = update_response.json()["data"]
                assert data["language"] == "ja-JP"
                assert data["show_tooltips"] == original_tooltips  # Should remain unchanged

                # Verify persistence
                saved_prefs = await repo.get_by_user_id(user_id)
                assert saved_prefs.language == "ja-JP"
                assert saved_prefs.show_tooltips == original_tooltips
        finally:
            app.dependency_overrides.clear()

    async def test_update_preferences_persists_across_restarts(self, db_session: AsyncSession):
        """Test that preferences persist across server restarts (no in-memory storage)"""
        user_id = "user-555"
        repo = UserPreferencesRepository(db_session)

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(repo)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # Set preferences
                await client.put(
                    "/api/user/preferences",
                    json={"language": "fr-FR", "show_tooltips": False}
                )

                # Simulate server restart by creating a new repository instance
                new_repo = UserPreferencesRepository(db_session)
                app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(new_repo)

                # Get preferences again
                response = await client.get("/api/user/preferences")

                assert response.status_code == 200
                data = response.json()["data"]
                assert data["language"] == "fr-FR"
                assert data["show_tooltips"] is False
        finally:
            app.dependency_overrides.clear()
