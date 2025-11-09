"""
Tests for Mode API endpoints with Database Persistence
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
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

    async def test_update_preferences_no_changes(self, db_session: AsyncSession):
        """Test update with no actual changes (all fields same as current)"""
        user_id = "user-666"
        repo = UserPreferencesRepository(db_session)

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(repo)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # Get initial preferences
                get_response = await client.get("/api/user/preferences")
                initial_data = get_response.json()["data"]

                # Update with same values
                update_response = await client.put(
                    "/api/user/preferences",
                    json={
                        "language": initial_data["language"],
                        "show_tooltips": initial_data["show_tooltips"],
                        "completed_guides": initial_data["completed_guides"]
                    }
                )

                assert update_response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    async def test_update_all_preferences_at_once(self, db_session: AsyncSession, mock_audit_logger):
        """Test updating all preferences in a single request"""
        user_id = "user-777"
        repo = UserPreferencesRepository(db_session)

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(repo)

        with patch('app.modules.user_onboarding.api.mode_api.audit_logger', mock_audit_logger):
            try:
                async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                    response = await client.put(
                        "/api/user/preferences",
                        json={
                            "language": "es-ES",
                            "show_tooltips": False,
                            "completed_guides": ["guide-a", "guide-b", "guide-c"]
                        }
                    )

                    assert response.status_code == 200
                    data = response.json()["data"]
                    assert data["language"] == "es-ES"
                    assert data["show_tooltips"] is False
                    assert len(data["completed_guides"]) == 3
            finally:
                app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestModeAPIErrorHandling:
    """Test error handling in mode API endpoints"""

    async def test_get_mode_database_error(self, db_session: AsyncSession, mock_audit_logger):
        """Test error handling when database fails"""
        user_id = "user-error-1"

        # Mock repository to raise exception
        mock_repo = MagicMock()
        mock_repo.get_or_create = AsyncMock(side_effect=Exception("Database error"))

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(mock_repo)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/user/mode")

                assert response.status_code == 500
                assert "Failed to get user mode" in response.json()["detail"]
        finally:
            app.dependency_overrides.clear()

    async def test_update_mode_database_error(self, mock_audit_logger):
        """Test error handling when database fails during mode update"""
        user_id = "user-error-2"

        # Mock repository to raise exception
        mock_repo = MagicMock()
        mock_repo.get_or_create = AsyncMock(return_value=(MagicMock(mode="beginner"), False))
        mock_repo.update_mode = AsyncMock(return_value=None)

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(mock_repo)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/user/mode",
                    json={"mode": "expert"}
                )

                assert response.status_code == 500
        finally:
            app.dependency_overrides.clear()

    async def test_get_preferences_database_error(self):
        """Test error handling when database fails during preferences get"""
        user_id = "user-error-3"

        # Mock repository to raise exception
        mock_repo = MagicMock()
        mock_repo.get_or_create = AsyncMock(side_effect=Exception("Database error"))

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(mock_repo)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/user/preferences")

                assert response.status_code == 500
        finally:
            app.dependency_overrides.clear()

    async def test_update_preferences_database_error(self, mock_audit_logger):
        """Test error handling when database fails during preferences update"""
        user_id = "user-error-4"

        # Mock repository to raise exception
        mock_repo = MagicMock()
        prefs = MagicMock()
        prefs.user_id = user_id
        prefs.mode = "beginner"
        prefs.completed_guides = []
        prefs.show_tooltips = True
        prefs.language = "en"
        prefs.created_at = None
        prefs.updated_at = None

        mock_repo.get_or_create = AsyncMock(return_value=(prefs, False))
        mock_repo.session = MagicMock()
        mock_repo.session.commit = AsyncMock(side_effect=Exception("Database error"))

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(mock_repo)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.put(
                    "/api/user/preferences",
                    json={"language": "zh-CN"}
                )

                assert response.status_code == 500
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestModeAPIEdgeCases:
    """Test edge cases and boundary conditions"""

    async def test_update_mode_same_as_current(self, db_session: AsyncSession):
        """Test updating mode to the same value as current"""
        user_id = "user-888"
        repo = UserPreferencesRepository(db_session)

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(repo)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # Get current mode
                get_response = await client.get("/api/user/mode")
                current_mode = get_response.json()["data"]["mode"]

                # Update to same mode
                update_response = await client.post(
                    "/api/user/mode",
                    json={"mode": current_mode}
                )

                assert update_response.status_code == 200
                assert update_response.json()["data"]["mode"] == current_mode
        finally:
            app.dependency_overrides.clear()

    async def test_multiple_consecutive_updates(self, db_session: AsyncSession):
        """Test multiple consecutive preference updates"""
        user_id = "user-999"
        repo = UserPreferencesRepository(db_session)

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(repo)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                # First update
                response1 = await client.put(
                    "/api/user/preferences",
                    json={"language": "en-US"}
                )
                assert response1.status_code == 200
                assert response1.json()["data"]["language"] == "en-US"

                # Second update
                response2 = await client.put(
                    "/api/user/preferences",
                    json={"show_tooltips": False}
                )
                assert response2.status_code == 200
                assert response2.json()["data"]["show_tooltips"] is False

                # Verify both changes persisted
                get_response = await client.get("/api/user/preferences")
                data = get_response.json()["data"]
                assert data["language"] == "en-US"
                assert data["show_tooltips"] is False
        finally:
            app.dependency_overrides.clear()

    async def test_empty_completed_guides_list(self, db_session: AsyncSession):
        """Test setting completed_guides to empty list"""
        user_id = "user-1000"
        repo = UserPreferencesRepository(db_session)

        # Create user with completed guides
        await repo.create({
            "user_id": user_id,
            "mode": "beginner",
            "completed_guides": ["guide-1", "guide-2"]
        })
        await db_session.commit()

        app.dependency_overrides[get_current_user_id] = override_get_current_user_id(user_id)
        app.dependency_overrides[get_user_prefs_repo] = override_get_user_prefs_repo(repo)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.put(
                    "/api/user/preferences",
                    json={"completed_guides": []}
                )

                assert response.status_code == 200
                assert response.json()["data"]["completed_guides"] == []
        finally:
            app.dependency_overrides.clear()
