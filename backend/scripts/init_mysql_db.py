"""
Initialize MySQL Database for Qlib-UI

This script:
1. Tests MySQL connection
2. Creates the qlib_ui database if it doesn't exist
3. Creates all tables using SQLAlchemy
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy.ext.asyncio import create_async_engine
from app.config import settings
from app.database.base import Base
from app.database.models import Dataset, ChartConfig, UserPreferences
from app.modules.common.logging import get_logger

logger = get_logger(__name__)


async def test_connection():
    """Test MySQL connection"""
    logger.info("Testing MySQL connection...")

    # Create connection without database name to test server
    base_url = settings.DATABASE_URL.rsplit('/', 1)[0]
    engine = create_async_engine(base_url + "/mysql", echo=False)

    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT VERSION()"))
            version = result.scalar()
            logger.info(f"✅ MySQL connection successful! Version: {version}")
            return True
    except Exception as e:
        logger.error(f"❌ MySQL connection failed: {e}")
        return False
    finally:
        await engine.dispose()


async def create_database():
    """Create qlib_ui database if it doesn't exist"""
    logger.info("Creating database...")

    # Connect to MySQL server (not to specific database)
    base_url = settings.DATABASE_URL.rsplit('/', 1)[0]
    engine = create_async_engine(base_url + "/mysql", echo=False)

    try:
        async with engine.begin() as conn:
            # Import text for raw SQL
            from sqlalchemy import text

            # Create database if not exists
            await conn.execute(
                text("CREATE DATABASE IF NOT EXISTS qlib_ui CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            )
            logger.info("✅ Database 'qlib_ui' created or already exists")

            # Verify database was created
            result = await conn.execute(text("SHOW DATABASES LIKE 'qlib_ui'"))
            if result.scalar():
                logger.info("✅ Database verified")
                return True
            else:
                logger.error("❌ Database not found after creation")
                return False

    except Exception as e:
        logger.error(f"❌ Failed to create database: {e}")
        return False
    finally:
        await engine.dispose()


async def create_tables():
    """Create all tables using SQLAlchemy"""
    logger.info("Creating tables...")

    # Connect to qlib_ui database
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    try:
        async with engine.begin() as conn:
            # Drop all tables (for clean slate in development)
            logger.warning("Dropping all existing tables...")
            await conn.run_sync(Base.metadata.drop_all)

            # Create all tables
            logger.info("Creating all tables...")
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ All tables created successfully!")

        # Verify tables
        async with engine.begin() as conn:
            from sqlalchemy import text
            result = await conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            logger.info(f"✅ Tables created: {tables}")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()


async def main():
    """Main initialization routine"""
    logger.info("=" * 60)
    logger.info("MySQL Database Initialization for Qlib-UI")
    logger.info("=" * 60)

    # Step 1: Test connection
    if not await test_connection():
        logger.error("Cannot proceed without MySQL connection")
        sys.exit(1)

    # Step 2: Create database
    if not await create_database():
        logger.error("Cannot proceed without database")
        sys.exit(1)

    # Step 3: Create tables
    if not await create_tables():
        logger.error("Failed to create tables")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("✅ Database initialization complete!")
    logger.info("=" * 60)
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    logger.info("You can now start the FastAPI application")


if __name__ == "__main__":
    asyncio.run(main())
