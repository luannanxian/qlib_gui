"""
TDD Tests for BuilderSessionRepository

Following strict TDD methodology (Red-Green-Refactor):
1. RED: Write failing tests first
2. GREEN: Implement minimal code to pass
3. REFACTOR: Optimize code

Test Coverage:
- Upsert session (create new or update existing)
- Find active sessions
- Expire session
- Find expired sessions
- Cleanup expired sessions in batch
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy_builder import BuilderSession
from app.database.repositories.builder_session_repository import BuilderSessionRepository


@pytest.mark.asyncio
class TestBuilderSessionRepository:
    """Tests for BuilderSessionRepository"""

    async def test_upsert_session_create(self, db_session: AsyncSession, sample_strategy_instance):
        """Test upsert creates new session if not exists"""
        repo = BuilderSessionRepository(db_session)

        session_data = {
            "instance_id": sample_strategy_instance.id,
            "user_id": "user-001",
            "draft_logic_flow": {"nodes": [], "edges": []},
            "is_active": True
        }

        # ACT
        session = await repo.upsert(session_data)

        # ASSERT
        assert session.id is not None
        assert session.instance_id == sample_strategy_instance.id
        assert session.is_active is True

    async def test_upsert_session_update(self, db_session: AsyncSession, sample_builder_session):
        """Test upsert updates existing session"""
        repo = BuilderSessionRepository(db_session)

        update_data = {
            "instance_id": sample_builder_session.instance_id,
            "user_id": sample_builder_session.user_id,
            "draft_logic_flow": {"nodes": [{"id": "n1"}], "edges": []},
            "is_active": True
        }

        # ACT
        updated = await repo.upsert(update_data)

        # ASSERT
        assert updated.id == sample_builder_session.id
        assert len(updated.draft_logic_flow["nodes"]) == 1

    async def test_find_active_sessions(self, db_session: AsyncSession):
        """Test finding active sessions"""
        repo = BuilderSessionRepository(db_session)

        # Create active and inactive sessions
        await repo.create({
            "user_id": "user-001",
            "draft_logic_flow": {},
            "is_active": True
        })
        await repo.create({
            "user_id": "user-002",
            "draft_logic_flow": {},
            "is_active": False
        })

        # ACT
        active = await repo.find_active_sessions()

        # ASSERT
        assert len(active) == 1
        assert active[0].is_active is True

    async def test_expire_session(self, db_session: AsyncSession, sample_builder_session):
        """Test expiring a session"""
        repo = BuilderSessionRepository(db_session)

        # ACT
        expired = await repo.expire_session(sample_builder_session.id)

        # ASSERT
        assert expired.is_active is False

    async def test_find_expired_sessions(self, db_session: AsyncSession):
        """Test finding expired sessions (expires_at < now)"""
        repo = BuilderSessionRepository(db_session)

        # Create expired session
        expired_session = await repo.create({
            "user_id": "user-001",
            "draft_logic_flow": {},
            "is_active": True,
            "expires_at": datetime.utcnow() - timedelta(hours=1)
        })

        # Create valid session
        valid_session = await repo.create({
            "user_id": "user-002",
            "draft_logic_flow": {},
            "is_active": True,
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        })

        # ACT
        expired_list = await repo.find_expired_sessions()

        # ASSERT
        assert len(expired_list) == 1
        assert expired_list[0].id == expired_session.id

    async def test_cleanup_expired_sessions(self, db_session: AsyncSession):
        """Test batch cleanup of expired sessions"""
        repo = BuilderSessionRepository(db_session)

        # Create 5 expired sessions
        for i in range(5):
            await repo.create({
                "user_id": f"user-{i}",
                "draft_logic_flow": {},
                "is_active": True,
                "expires_at": datetime.utcnow() - timedelta(hours=1)
            })

        # ACT
        count = await repo.cleanup_expired_sessions()

        # ASSERT
        assert count == 5

        # Verify all expired
        active = await repo.find_active_sessions()
        assert len(active) == 0
