"""
Database Layer Verification Script

This script verifies that all database components are properly installed and configured.
"""

import asyncio
import sys
from loguru import logger


async def verify_imports():
    """Verify all database imports"""
    logger.info("Verifying database imports...")

    try:
        # Base imports
        from app.database.base import Base, BaseDBModel, TimestampMixin, SoftDeleteMixin
        logger.success("✓ Base models imported")

        # Session imports
        from app.database.session import db_manager, get_db
        logger.success("✓ Session management imported")

        # Model imports
        from app.database.models import (
            Dataset, DataSource, DatasetStatus,
            ChartConfig, ChartType,
            UserPreferences, UserMode
        )
        logger.success("✓ Models imported")

        # Repository imports
        from app.database.repositories import (
            BaseRepository,
            DatasetRepository,
            ChartRepository,
            UserPreferencesRepository
        )
        logger.success("✓ Repositories imported")

        logger.success("All imports verified successfully!")
        return True

    except Exception as e:
        logger.error(f"Import verification failed: {e}")
        return False


async def verify_database_structure():
    """Verify database structure can be created"""
    logger.info("Verifying database structure...")

    try:
        from app.database.session import db_manager
        from app.database.base import Base

        # Initialize engine
        db_manager.init()

        # Get metadata
        tables = Base.metadata.tables.keys()
        logger.info(f"Found {len(tables)} tables: {', '.join(tables)}")

        expected_tables = {"datasets", "chart_configs", "user_preferences"}
        if not expected_tables.issubset(tables):
            missing = expected_tables - set(tables)
            logger.error(f"Missing tables: {missing}")
            return False

        logger.success("✓ All expected tables defined")

        # Close engine
        await db_manager.close()

        logger.success("Database structure verified successfully!")
        return True

    except Exception as e:
        logger.error(f"Database structure verification failed: {e}")
        return False


async def verify_enums():
    """Verify all enum types"""
    logger.info("Verifying enum types...")

    try:
        from app.database.models import DataSource, DatasetStatus, ChartType, UserMode

        # DataSource
        assert DataSource.LOCAL.value == "local"
        assert DataSource.QLIB.value == "qlib"
        assert DataSource.THIRDPARTY.value == "thirdparty"
        logger.success("✓ DataSource enum")

        # DatasetStatus
        assert DatasetStatus.VALID.value == "valid"
        assert DatasetStatus.INVALID.value == "invalid"
        assert DatasetStatus.PENDING.value == "pending"
        logger.success("✓ DatasetStatus enum")

        # ChartType
        assert ChartType.KLINE.value == "kline"
        assert ChartType.LINE.value == "line"
        assert ChartType.BAR.value == "bar"
        assert ChartType.SCATTER.value == "scatter"
        assert ChartType.HEATMAP.value == "heatmap"
        logger.success("✓ ChartType enum")

        # UserMode
        assert UserMode.BEGINNER.value == "beginner"
        assert UserMode.EXPERT.value == "expert"
        logger.success("✓ UserMode enum")

        logger.success("All enums verified successfully!")
        return True

    except Exception as e:
        logger.error(f"Enum verification failed: {e}")
        return False


async def verify_repositories():
    """Verify repository interfaces"""
    logger.info("Verifying repository interfaces...")

    try:
        from app.database.repositories import (
            DatasetRepository,
            ChartRepository,
            UserPreferencesRepository
        )

        # Check DatasetRepository methods
        dataset_methods = [
            "create", "get", "get_multi", "update", "delete",
            "get_by_name", "get_by_source", "get_by_status",
            "search_by_name", "get_statistics"
        ]
        for method in dataset_methods:
            assert hasattr(DatasetRepository, method)
        logger.success("✓ DatasetRepository methods")

        # Check ChartRepository methods
        chart_methods = [
            "create", "get", "get_multi", "update", "delete",
            "get_by_dataset", "get_by_type", "count_by_dataset",
            "duplicate_chart", "get_statistics"
        ]
        for method in chart_methods:
            assert hasattr(ChartRepository, method)
        logger.success("✓ ChartRepository methods")

        # Check UserPreferencesRepository methods
        prefs_methods = [
            "create", "get", "get_multi", "update", "delete",
            "get_by_user_id", "get_or_create", "update_mode",
            "add_completed_guide", "update_settings"
        ]
        for method in prefs_methods:
            assert hasattr(UserPreferencesRepository, method)
        logger.success("✓ UserPreferencesRepository methods")

        logger.success("All repository interfaces verified successfully!")
        return True

    except Exception as e:
        logger.error(f"Repository verification failed: {e}")
        return False


async def verify_config():
    """Verify database configuration"""
    logger.info("Verifying database configuration...")

    try:
        from app.config import settings

        logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'N/A'}")
        logger.info(f"Pool Size: {settings.DATABASE_POOL_SIZE}")
        logger.info(f"Max Overflow: {settings.DATABASE_MAX_OVERFLOW}")
        logger.info(f"Pool Recycle: {settings.DATABASE_POOL_RECYCLE}s")

        assert settings.DATABASE_URL is not None
        assert settings.DATABASE_POOL_SIZE > 0
        logger.success("✓ Database configuration valid")

        logger.success("Configuration verified successfully!")
        return True

    except Exception as e:
        logger.error(f"Configuration verification failed: {e}")
        return False


async def main():
    """Run all verification checks"""
    logger.info("=" * 60)
    logger.info("Qlib-UI Database Layer Verification")
    logger.info("=" * 60)

    results = []

    # Run all verification checks
    results.append(await verify_imports())
    results.append(await verify_enums())
    results.append(await verify_database_structure())
    results.append(await verify_repositories())
    results.append(await verify_config())

    # Summary
    logger.info("=" * 60)
    if all(results):
        logger.success("✓ All verification checks passed!")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("✗ Some verification checks failed")
        logger.info("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
