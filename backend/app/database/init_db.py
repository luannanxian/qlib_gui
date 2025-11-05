"""
Database Initialization Script

This script initializes the database schema and creates necessary tables.
Run this before starting the application for the first time.
"""

import asyncio
from loguru import logger

from app.database.session import db_manager


async def init_database() -> None:
    """
    Initialize the database by creating all tables.

    This function:
    1. Initializes the database engine
    2. Creates all tables defined in the models
    3. Logs the operation
    """
    try:
        logger.info("Starting database initialization...")

        # Initialize database engine
        db_manager.init()

        # Create all tables
        await db_manager.create_all()

        logger.info("Database initialization completed successfully!")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    finally:
        await db_manager.close()


async def drop_database() -> None:
    """
    Drop all database tables.

    WARNING: This will delete all data! Use only in development/testing.
    """
    try:
        logger.warning("Starting database drop operation...")

        # Initialize database engine
        db_manager.init()

        # Drop all tables
        await db_manager.drop_all()

        logger.warning("Database drop completed!")

    except Exception as e:
        logger.error(f"Database drop failed: {e}")
        raise
    finally:
        await db_manager.close()


async def reset_database() -> None:
    """
    Reset the database by dropping and recreating all tables.

    WARNING: This will delete all data! Use only in development/testing.
    """
    try:
        logger.warning("Starting database reset...")

        # Initialize database engine
        db_manager.init()

        # Drop all tables
        logger.warning("Dropping all tables...")
        await db_manager.drop_all()

        # Create all tables
        logger.info("Creating all tables...")
        await db_manager.create_all()

        logger.info("Database reset completed successfully!")

    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        raise
    finally:
        await db_manager.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "init":
            asyncio.run(init_database())
        elif command == "drop":
            asyncio.run(drop_database())
        elif command == "reset":
            asyncio.run(reset_database())
        else:
            print(f"Unknown command: {command}")
            print("Available commands: init, drop, reset")
            sys.exit(1)
    else:
        # Default: initialize database
        asyncio.run(init_database())
