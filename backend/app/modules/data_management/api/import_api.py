"""
Import Task API

Handles file upload, import task management, and data import operations.
"""

import os
import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.repositories.import_task import ImportTaskRepository
from app.database.models.import_task import ImportStatus, ImportType
from app.modules.data_management.services.import_service import DataImportService
from app.modules.data_management.schemas.import_schemas import (
    ImportTaskCreate,
    ImportTaskResponse,
    ImportTaskListResponse,
    ImportTaskUpdate,
)
from app.modules.common.logging import get_logger
from app.modules.common.logging.decorators import log_async_execution
from app.config import settings

router = APIRouter(prefix="/api/imports", tags=["imports"])


@router.post(
    "/upload",
    response_model=ImportTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file and create import task",
    description="Upload a data file (CSV/Excel) and create an import task for processing"
)
@log_async_execution(log_args=False)
async def upload_file(
    file: UploadFile = File(..., description="Data file to upload (CSV/Excel)"),
    task_name: Optional[str] = Form(None, description="Custom task name"),
    user_id: Optional[str] = Form(None, description="User ID"),
    session: AsyncSession = Depends(get_db)
):
    """
    Upload a file and create an import task.

    The file will be saved to the upload directory and an import task will be created.
    The actual processing will be done asynchronously (in the future via Celery).

    Args:
        file: Uploaded file
        task_name: Optional custom task name
        user_id: Optional user ID
        session: Database session

    Returns:
        Created import task details
    """
    # Validate file extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext == '.csv':
        import_type = ImportType.CSV
    elif file_ext in ['.xlsx', '.xls']:
        import_type = ImportType.EXCEL
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file_ext}. Supported: .csv, .xlsx, .xls"
        )

    # Read file content and save
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename
    unique_id = str(uuid.uuid4())[:8]
    safe_filename = f"{unique_id}_{file.filename}"
    file_path = os.path.join(upload_dir, safe_filename)

    try:
        # Save uploaded file
        contents = await file.read()
        file_size = len(contents)

        # Check file size
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size {file_size} bytes exceeds maximum {max_size} bytes"
            )

        with open(file_path, 'wb') as f:
            f.write(contents)

        # Create import task
        import_service = DataImportService(session, upload_dir)

        task_create = ImportTaskCreate(
            task_name=task_name or f"Import {file.filename}",
            import_type=import_type,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            import_config={},
            user_id=user_id
        )

        task_id = await import_service.create_import_task(task_create)

        # Get created task for response
        repo = ImportTaskRepository(session)
        task = await repo.get(task_id)

        return ImportTaskResponse.model_validate(task)

    except HTTPException:
        # Clean up file if task creation failed
        if os.path.exists(file_path):
            os.remove(file_path)
        raise
    except Exception as e:
        # Clean up file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )


@router.post(
    "/{task_id}/process",
    response_model=ImportTaskResponse,
    summary="Process import task",
    description="Start processing an uploaded import task"
)
@log_async_execution(log_args=False)
async def process_import_task(
    task_id: str,
    session: AsyncSession = Depends(get_db)
):
    """
    Process an import task.

    This will validate the file, parse the data, and create a dataset.
    Currently runs synchronously - will be moved to Celery for async processing.

    Args:
        task_id: Import task ID
        session: Database session

    Returns:
        Updated import task details
    """
    repo = ImportTaskRepository(session)
    task = await repo.get(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import task {task_id} not found"
        )

    if task.status != ImportStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task is already {task.status}, cannot reprocess"
        )

    # Process the import
    import_service = DataImportService(session, settings.UPLOAD_DIR)

    result = await import_service.process_import(
        task_id=task_id,
        file_path=task.file_path,
        import_type=ImportType(task.import_type),
        import_config=task.import_config
    )

    # Get updated task
    task = await repo.get(task_id)

    return ImportTaskResponse.model_validate(task)


@router.get(
    "",
    response_model=ImportTaskListResponse,
    summary="List import tasks",
    description="List all import tasks with optional filtering"
)
@log_async_execution(log_args=False)
async def list_import_tasks(
    skip: int = 0,
    limit: int = 100,
    task_status: Optional[ImportStatus] = None,
    user_id: Optional[str] = None,
    session: AsyncSession = Depends(get_db)
):
    """
    List import tasks with pagination and filtering.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        task_status: Filter by status
        user_id: Filter by user ID
        session: Database session

    Returns:
        Paginated list of import tasks
    """
    repo = ImportTaskRepository(session)

    # Get tasks based on filters
    if user_id:
        tasks = await repo.get_by_user(
            user_id=user_id,
            status=task_status,
            skip=skip,
            limit=limit
        )
        total = await repo.count(user_id=user_id)
    elif task_status:
        tasks = await repo.get_by_status(
            status=task_status,
            skip=skip,
            limit=limit
        )
        total = await repo.count_by_status(task_status)
    else:
        tasks = await repo.get_multi(skip=skip, limit=limit)
        total = await repo.count()

    return ImportTaskListResponse(
        total=total,
        items=[ImportTaskResponse.model_validate(task) for task in tasks]
    )


@router.get(
    "/{task_id}",
    response_model=ImportTaskResponse,
    summary="Get import task",
    description="Get details of a specific import task"
)
@log_async_execution(log_args=False)
async def get_import_task(
    task_id: str,
    session: AsyncSession = Depends(get_db)
):
    """
    Get import task by ID.

    Args:
        task_id: Import task ID
        session: Database session

    Returns:
        Import task details
    """
    repo = ImportTaskRepository(session)
    task = await repo.get(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import task {task_id} not found"
        )

    return ImportTaskResponse.model_validate(task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete import task",
    description="Delete an import task (soft delete by default)"
)
@log_async_execution(log_args=False)
async def delete_import_task(
    task_id: str,
    hard_delete: bool = False,
    session: AsyncSession = Depends(get_db)
):
    """
    Delete an import task.

    Args:
        task_id: Import task ID
        hard_delete: Whether to hard delete (default: soft delete)
        session: Database session
    """
    repo = ImportTaskRepository(session)
    task = await repo.get(task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import task {task_id} not found"
        )

    # Delete the task
    success = await repo.delete(task_id, soft=not hard_delete, commit=True)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete import task"
        )

    # Delete uploaded file if hard delete
    if hard_delete and os.path.exists(task.file_path):
        try:
            os.remove(task.file_path)
        except Exception as e:
            # Log but don't fail the request
            pass


@router.get(
    "/active/count",
    summary="Get active task count",
    description="Get count of active (not completed/failed) import tasks"
)
@log_async_execution(log_args=False)
async def get_active_task_count(
    session: AsyncSession = Depends(get_db)
):
    """
    Get count of active import tasks.

    Args:
        session: Database session

    Returns:
        Count of active tasks
    """
    repo = ImportTaskRepository(session)
    tasks = await repo.get_active_tasks()

    return {"active_count": len(tasks)}
