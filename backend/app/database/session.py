"""
Database Session Management

This module provides async database session management with connection pooling,
transaction handling, and dependency injection for FastAPI.
"""

import threading
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import settings
from app.database.base import Base


class DatabaseSessionManager:
    """
    Manages database connections and sessions with async support.

    Features:
    - Connection pooling with configurable size
    - Automatic session cleanup
    - Transaction management
    - Health checking with pre-ping
    - Connection recycling for MySQL
    """

    def __init__(self, database_url: str):
        """
        Initialize database session manager.

        Args:
            database_url: Database connection URL (mysql+aiomysql://...)
        """
        self._engine: AsyncEngine | None = None
        self._sessionmaker: async_sessionmaker[AsyncSession] | None = None
        self._database_url = database_url

    def init(self) -> None:
        """
        Initialize database engine and session factory.

        This should be called during application startup.
        """
        if self._engine is not None:
            logger.warning("Database engine already initialized")
            return

        # Sanitize database URL for logging
        from urllib.parse import urlparse, urlunparse
        parsed_url = urlparse(self._database_url)
        sanitized_url = parsed_url._replace(netloc=f"***:***@{parsed_url.hostname}:{parsed_url.port}")
        logger.info(f"Initializing database engine: {urlunparse(sanitized_url)}")

        # Create async engine with connection pooling
        self._engine = create_async_engine(
            self._database_url,
            echo=settings.DATABASE_ECHO,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_recycle=settings.DATABASE_POOL_RECYCLE,
            pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
            # Use NullPool for testing environments to avoid connection issues
            poolclass=NullPool if settings.APP_ENV == "test" else None,
        )

        # Create session factory
        self._sessionmaker = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        logger.info("Database engine initialized successfully")

    async def close(self) -> None:
        """
        Close database engine and cleanup resources.

        This should be called during application shutdown.
        """
        if self._engine is None:
            logger.warning("Database engine not initialized")
            return

        logger.info("Closing database engine")
        await self._engine.dispose()
        self._engine = None
        self._sessionmaker = None
        logger.info("Database engine closed successfully")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Create a new database session with automatic cleanup.

        Usage:
            async with db_manager.session() as session:
                result = await session.execute(select(Dataset))
                ...

        Yields:
            AsyncSession: Database session

        Raises:
            RuntimeError: If engine is not initialized
        """
        if self._sessionmaker is None:
            raise RuntimeError(
                "Database session manager not initialized. Call init() first."
            )

        async with self._sessionmaker() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Session error, rolling back: {e}")
                raise
            finally:
                await session.close()

    async def create_all(self) -> None:
        """
        Create all database tables.

        This should be used with caution in production environments.
        Consider using Alembic migrations instead.
        """
        if self._engine is None:
            raise RuntimeError(
                "Database engine not initialized. Call init() first."
            )

        logger.info("Creating all database tables")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")

    async def drop_all(self) -> None:
        """
        Drop all database tables.

        WARNING: This will delete all data! Use only in development/testing.
        """
        if self._engine is None:
            raise RuntimeError(
                "Database engine not initialized. Call init() first."
            )

        logger.warning("Dropping all database tables")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("Database tables dropped successfully")

    @property
    def engine(self) -> AsyncEngine:
        """Get the database engine."""
        if self._engine is None:
            raise RuntimeError(
                "Database engine not initialized. Call init() first."
            )
        return self._engine


# Global database session manager instance
db_manager = DatabaseSessionManager(settings.DATABASE_URL)


# Create a session maker for use in Celery tasks and other contexts
_session_maker_lock = threading.Lock()
async_session_maker = None


def init_session_maker() -> async_sessionmaker[AsyncSession]:
    """
    Initialize and return the async session maker.
    Thread-safe implementation using double-check locking pattern.

    This is used by Celery tasks and other contexts that need
    to create database sessions outside of FastAPI dependency injection.

    Returns:
        async_sessionmaker: Session maker instance
    """
    global async_session_maker

    if async_session_maker is None:
        with _session_maker_lock:
            # Double-check locking pattern for thread safety
            if async_session_maker is None:
                if db_manager._sessionmaker is None:
                    db_manager.init()
                async_session_maker = db_manager._sessionmaker

    return async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database session injection.

    Usage:
        @app.get("/datasets")
        async def get_datasets(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Dataset))
            ...

    Yields:
        AsyncSession: Database session
    """
    async with db_manager.session() as session:
        yield session
