"""
BuilderSession Repository

Repository for managing builder session operations with specialized
methods for draft auto-save and session lifecycle management.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from loguru import logger
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.strategy_builder import BuilderSession
from app.database.repositories.base import BaseRepository


class BuilderSessionRepository(BaseRepository[BuilderSession]):
    """
    Repository for BuilderSession operations.

    Provides specialized methods for:
    - Upsert (create or update) session by instance_id + user_id
    - Active session management
    - Session expiration and cleanup
    - Auto-save functionality support
    - Collaborative editing session management (future)
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with BuilderSession model"""
        super().__init__(BuilderSession, session)

    async def upsert(
        self,
        session_data: Dict[str, Any],
        commit: bool = True
    ) -> BuilderSession:
        """
        Create or update session based on instance_id + user_id.

        If a session exists for the same instance_id and user_id,
        update it. Otherwise, create a new session.

        Args:
            session_data: Dictionary containing session attributes
                Required: user_id, draft_logic_flow
                Optional: instance_id, draft_parameters, is_active, etc.
            commit: Whether to commit the transaction

        Returns:
            Created or updated session

        Example:
            session = await repo.upsert({
                "instance_id": "inst-001",
                "user_id": "user-001",
                "draft_logic_flow": {"nodes": [], "edges": []},
                "is_active": True
            })
        """
        user_id = session_data.get("user_id")
        instance_id = session_data.get("instance_id")

        if not user_id:
            raise ValueError("user_id is required for upsert")

        # Try to find existing session
        existing = None
        if instance_id:
            # Find by instance_id + user_id
            stmt = select(BuilderSession).where(
                BuilderSession.instance_id == instance_id,
                BuilderSession.user_id == user_id,
                BuilderSession.is_deleted == False
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
        else:
            # For new unsaved strategies (no instance_id yet),
            # find by user_id + no instance_id
            stmt = select(BuilderSession).where(
                BuilderSession.instance_id.is_(None),
                BuilderSession.user_id == user_id,
                BuilderSession.is_deleted == False
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()

        if existing:
            # Update existing session
            updated = await self.update(
                existing.id,
                session_data,
                commit=commit
            )
            logger.debug(
                f"Updated BuilderSession {existing.id} for "
                f"user={user_id}, instance={instance_id}"
            )
            return updated
        else:
            # Create new session
            created = await self.create(session_data, commit=commit)
            logger.debug(
                f"Created BuilderSession {created.id} for "
                f"user={user_id}, instance={instance_id}"
            )
            return created

    async def find_active_sessions(
        self,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[BuilderSession]:
        """
        Find active sessions.

        Args:
            user_id: Optional user filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active sessions
        """
        stmt = select(BuilderSession).where(
            BuilderSession.is_active == True,
            BuilderSession.is_deleted == False
        )

        if user_id:
            stmt = stmt.where(BuilderSession.user_id == user_id)

        stmt = stmt.order_by(BuilderSession.last_activity_at.desc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        sessions = list(result.scalars().all())

        logger.debug(
            f"Found {len(sessions)} active sessions"
            + (f" for user {user_id}" if user_id else "")
        )
        return sessions

    async def expire_session(
        self,
        session_id: str,
        commit: bool = True
    ) -> Optional[BuilderSession]:
        """
        Expire a session (set is_active=False).

        Args:
            session_id: Session ID
            commit: Whether to commit the transaction

        Returns:
            Expired session or None if not found
        """
        updated = await self.update(
            session_id,
            {"is_active": False},
            commit=commit
        )

        if updated:
            logger.debug(f"Expired BuilderSession {session_id}")

        return updated

    async def find_expired_sessions(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[BuilderSession]:
        """
        Find expired sessions (expires_at < now).

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of expired sessions
        """
        now = datetime.utcnow()

        stmt = select(BuilderSession).where(
            BuilderSession.expires_at < now,
            BuilderSession.is_active == True,
            BuilderSession.is_deleted == False
        )

        stmt = stmt.order_by(BuilderSession.expires_at.asc())
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        sessions = list(result.scalars().all())

        logger.debug(f"Found {len(sessions)} expired sessions")
        return sessions

    async def cleanup_expired_sessions(
        self,
        commit: bool = True
    ) -> int:
        """
        Batch cleanup of expired sessions (set is_active=False).

        Args:
            commit: Whether to commit the transaction

        Returns:
            Number of sessions cleaned up
        """
        expired_sessions = await self.find_expired_sessions(limit=1000)

        count = 0
        for session in expired_sessions:
            await self.expire_session(session.id, commit=False)
            count += 1

        if commit and count > 0:
            await self.session.commit()

        logger.info(f"Cleaned up {count} expired sessions")
        return count

    async def find_by_instance(
        self,
        instance_id: str,
        user_id: Optional[str] = None,
        active_only: bool = False
    ) -> List[BuilderSession]:
        """
        Find sessions for a strategy instance.

        Args:
            instance_id: Strategy instance ID
            user_id: Optional user filter
            active_only: Only return active sessions

        Returns:
            List of sessions for the instance
        """
        stmt = select(BuilderSession).where(
            BuilderSession.instance_id == instance_id,
            BuilderSession.is_deleted == False
        )

        if user_id:
            stmt = stmt.where(BuilderSession.user_id == user_id)

        if active_only:
            stmt = stmt.where(BuilderSession.is_active == True)

        stmt = stmt.order_by(BuilderSession.last_activity_at.desc())

        result = await self.session.execute(stmt)
        sessions = list(result.scalars().all())

        logger.debug(
            f"Found {len(sessions)} sessions for instance {instance_id}"
        )
        return sessions

    async def update_last_activity(
        self,
        session_id: str,
        commit: bool = True
    ) -> Optional[BuilderSession]:
        """
        Update session's last activity timestamp.

        Args:
            session_id: Session ID
            commit: Whether to commit the transaction

        Returns:
            Updated session or None if not found
        """
        updated = await self.update(
            session_id,
            {"last_activity_at": datetime.utcnow()},
            commit=commit
        )

        if updated:
            logger.debug(
                f"Updated last_activity_at for session {session_id}"
            )

        return updated
