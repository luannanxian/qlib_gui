"""
Data Import Tasks

Celery tasks for asynchronous data import and processing.
"""

import asyncio
from typing import Optional, Dict, Any

from celery import Task
from celery.utils.log import get_task_logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.celery_app import celery_app
from app.database.session import init_session_maker
from app.database.models.import_task import ImportType, ImportStatus
from app.modules.data_management.services.import_service import DataImportService

logger = get_task_logger(__name__)


# Initialize session maker on module import
async_session_maker = init_session_maker()


class DatabaseTask(Task):
    """Base task class with database session management."""

    _session = None

    def get_session(self) -> AsyncSession:
        """Get async database session."""
        if self._session is None:
            self._session = async_session_maker()
        return self._session

    async def close_session(self):
        """Close database session."""
        if self._session is not None:
            await self._session.close()
            self._session = None


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.modules.data_management.tasks.process_data_import",
    max_retries=3,
    default_retry_delay=60,  # Retry after 1 minute
)
def process_data_import(
    self,
    task_id: str,
    file_path: str,
    import_type: str,
    import_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Process data import asynchronously.

    Args:
        task_id: Import task ID
        file_path: Path to uploaded file
        import_type: Type of import (csv, excel, etc.)
        import_config: Import configuration options

    Returns:
        Dict with processing result
    """

    async def _process():
        """Inner async function for processing."""
        session = None
        try:
            # Create database session
            session = async_session_maker()

            # Initialize import service
            service = DataImportService(session=session)

            # Convert import_type string to enum
            import_type_enum = ImportType(import_type)

            # Update task to PROCESSING
            await service.import_task_repo.update(
                id=task_id,
                obj_in={
                    "status": ImportStatus.PROCESSING.value,
                    "celery_task_id": self.request.id,
                },
                commit=True,
            )

            logger.info(
                f"Starting data import processing",
                extra={
                    "task_id": task_id,
                    "file_path": file_path,
                    "import_type": import_type,
                },
            )

            # Process the import
            result = await service.process_import(
                task_id=task_id,
                file_path=file_path,
                import_type=import_type_enum,
                import_config=import_config,
            )

            if result.success:
                logger.info(
                    f"Data import completed successfully",
                    extra={
                        "task_id": task_id,
                        "rows_processed": result.rows_processed,
                        "rows_skipped": result.rows_skipped,
                        "dataset_id": result.dataset_id,
                    },
                )

                return {
                    "success": True,
                    "task_id": task_id,
                    "rows_processed": result.rows_processed,
                    "rows_skipped": result.rows_skipped,
                    "dataset_id": result.dataset_id,
                    "errors": result.errors,
                }
            else:
                logger.error(
                    f"Data import failed",
                    extra={
                        "task_id": task_id,
                        "errors": result.errors,
                    },
                )

                return {
                    "success": False,
                    "task_id": task_id,
                    "errors": result.errors,
                }

        except Exception as e:
            logger.error(
                f"Error processing data import: {str(e)}",
                exc_info=True,
                extra={"task_id": task_id},
            )

            # Update task to FAILED
            if session:
                try:
                    service = DataImportService(session=session)
                    await service.import_task_repo.update(
                        id=task_id,
                        obj_in={
                            "status": ImportStatus.FAILED.value,
                            "error_message": str(e),
                        },
                        commit=True,
                    )
                except Exception as update_error:
                    logger.error(
                        f"Failed to update task status: {str(update_error)}",
                        exc_info=True,
                    )

            # Retry on certain errors
            if "database" in str(e).lower() or "connection" in str(e).lower():
                raise self.retry(exc=e)

            raise

        finally:
            # Always close session
            if session:
                await session.close()

    # Run async function in event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_process())


@celery_app.task(
    bind=True,
    base=DatabaseTask,
    name="app.modules.data_management.tasks.validate_import_file",
)
def validate_import_file(
    self,
    task_id: str,
    file_path: str,
    import_type: str,
) -> Dict[str, Any]:
    """
    Validate import file asynchronously.

    Args:
        task_id: Import task ID
        file_path: Path to uploaded file
        import_type: Type of import

    Returns:
        Dict with validation result
    """

    async def _validate():
        """Inner async function for validation."""
        session = None
        try:
            # Create database session
            session = async_session_maker()

            # Initialize import service
            service = DataImportService(session=session)

            # Convert import_type string to enum
            import_type_enum = ImportType(import_type)

            logger.info(
                f"Starting file validation",
                extra={
                    "task_id": task_id,
                    "file_path": file_path,
                    "import_type": import_type,
                },
            )

            # Validate file
            validation = await service.validate_file(file_path, import_type_enum)

            # Update task with validation results
            await service.import_task_repo.update(
                id=task_id,
                obj_in={
                    "parsing_metadata": validation.metadata,
                    "validation_errors": validation.errors if not validation.is_valid else None,
                },
                commit=True,
            )

            logger.info(
                f"File validation completed",
                extra={
                    "task_id": task_id,
                    "is_valid": validation.is_valid,
                    "errors": len(validation.errors),
                    "warnings": len(validation.warnings),
                },
            )

            return {
                "success": validation.is_valid,
                "task_id": task_id,
                "errors": validation.errors,
                "warnings": validation.warnings,
                "metadata": validation.metadata,
            }

        except Exception as e:
            logger.error(
                f"Error validating file: {str(e)}",
                exc_info=True,
                extra={"task_id": task_id},
            )

            return {
                "success": False,
                "task_id": task_id,
                "errors": [str(e)],
                "warnings": [],
                "metadata": {},
            }

        finally:
            # Always close session
            if session:
                await session.close()

    # Run async function in event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_validate())


@celery_app.task(
    bind=True,
    name="app.modules.data_management.tasks.cleanup_old_imports",
)
def cleanup_old_imports(self, days: int = 30) -> Dict[str, Any]:
    """
    Cleanup old import tasks and files.

    Args:
        days: Delete tasks older than this many days

    Returns:
        Dict with cleanup result
    """

    async def _cleanup():
        """Inner async function for cleanup."""
        session = None
        try:
            # Create database session
            session = async_session_maker()

            # Initialize repository
            from app.database.repositories.import_task import ImportTaskRepository
            from datetime import datetime, timedelta
            import os

            repo = ImportTaskRepository(session)

            # Find old tasks
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Get old failed/cancelled tasks
            old_tasks = await repo.find_by_filters(
                filters={
                    "status": [ImportStatus.FAILED.value, ImportStatus.CANCELLED.value],
                    "created_before": cutoff_date,
                },
                is_deleted=False,
            )

            deleted_count = 0
            files_deleted = 0

            for task in old_tasks:
                # Delete associated file if exists
                if task.file_path and os.path.exists(task.file_path):
                    try:
                        os.remove(task.file_path)
                        files_deleted += 1
                    except Exception as e:
                        logger.warning(
                            f"Failed to delete file {task.file_path}: {str(e)}"
                        )

                # Soft delete task
                await repo.delete(task.id, commit=False)
                deleted_count += 1

            await session.commit()

            logger.info(
                f"Cleanup completed: deleted {deleted_count} tasks and {files_deleted} files"
            )

            return {
                "success": True,
                "tasks_deleted": deleted_count,
                "files_deleted": files_deleted,
            }

        except Exception as e:
            logger.error(
                f"Error during cleanup: {str(e)}",
                exc_info=True,
            )

            return {
                "success": False,
                "error": str(e),
            }

        finally:
            # Always close session
            if session:
                await session.close()

    # Run async function in event loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(_cleanup())
