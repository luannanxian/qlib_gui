#!/usr/bin/env python3
"""
Recreate import_tasks table (drop and create)
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database.session import db_manager
from app.modules.common.logging import get_logger

logger = get_logger(__name__)


async def recreate_table():
    """Drop and recreate import_tasks table"""
    db_manager.init()

    async with db_manager.session() as session:
        try:
            # Drop table if exists
            await session.execute(text("DROP TABLE IF EXISTS import_tasks"))
            await session.commit()
            logger.info("✅ Dropped import_tasks table")

            # Create table with correct schema
            create_table_sql = """
            CREATE TABLE import_tasks (
                id VARCHAR(36) PRIMARY KEY COMMENT 'UUID primary key',
                task_name VARCHAR(255) NOT NULL COMMENT 'Human-readable task name',
                import_type VARCHAR(50) NOT NULL COMMENT 'Import file type',
                status VARCHAR(50) NOT NULL DEFAULT 'pending' COMMENT 'Import task status',

                original_filename VARCHAR(255) NOT NULL COMMENT 'Original uploaded filename',
                file_path TEXT NOT NULL COMMENT 'Server file path',
                file_size INT NOT NULL DEFAULT 0 COMMENT 'File size in bytes',

                total_rows INT NOT NULL DEFAULT 0 COMMENT 'Total rows to process',
                processed_rows INT NOT NULL DEFAULT 0 COMMENT 'Rows processed',
                progress_percentage FLOAT NOT NULL DEFAULT 0.0 COMMENT 'Progress percentage',

                error_count INT NOT NULL DEFAULT 0 COMMENT 'Error count',
                error_message TEXT NULL COMMENT 'Error message if failed',

                validation_errors JSON NULL COMMENT 'Validation errors array',
                parsing_metadata JSON NULL COMMENT 'Parsing metadata',
                import_config JSON NULL COMMENT 'Import configuration',

                user_id VARCHAR(255) NULL COMMENT 'User who initiated import',
                dataset_id VARCHAR(36) NULL COMMENT 'Created/updated dataset ID',

                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation timestamp',
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last update timestamp',
                is_deleted BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Soft delete flag',
                deleted_at TIMESTAMP NULL COMMENT 'Soft delete timestamp',
                created_by VARCHAR(255) NULL COMMENT 'User who created this record',
                updated_by VARCHAR(255) NULL COMMENT 'User who last updated this record',

                INDEX ix_import_tasks_task_name (task_name),
                INDEX ix_import_tasks_import_type (import_type),
                INDEX ix_import_tasks_status (status),
                INDEX ix_import_tasks_user_id (user_id),
                INDEX ix_import_tasks_dataset_id (dataset_id),
                INDEX ix_import_status_created (status, created_at),
                INDEX ix_import_user_status (user_id, status),
                INDEX ix_import_type_status (import_type, status),

                CONSTRAINT fk_import_task_dataset
                    FOREIGN KEY (dataset_id)
                    REFERENCES datasets(id)
                    ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Import task tracking table';
            """

            await session.execute(text(create_table_sql))
            await session.commit()
            logger.info("✅ Created import_tasks table with correct schema")

            return True

        except Exception as e:
            logger.error(f"❌ Error: {e}", exc_info=True)
            await session.rollback()
            return False
        finally:
            await db_manager.close()


if __name__ == "__main__":
    success = asyncio.run(recreate_table())
    sys.exit(0 if success else 1)
