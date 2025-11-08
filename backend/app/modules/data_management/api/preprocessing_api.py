"""
Preprocessing API Endpoints

This module provides RESTful API endpoints for data preprocessing with:
- Full CRUD operations for preprocessing rules/templates
- Preprocessing execution and task tracking
- Preview functionality for testing operations
- Comprehensive logging and error handling
- Pagination and filtering support
"""

from typing import Optional, Dict, Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, Query, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import ValidationError

from app.database import get_db
from app.database.models.preprocessing import (
    DataPreprocessingRule,
    DataPreprocessingTask,
    PreprocessingTaskStatus
)
from app.database.repositories.preprocessing import PreprocessingRuleRepository, PreprocessingTaskRepository
from app.modules.data_management.schemas.preprocessing import (
    PreprocessingRuleCreate,
    PreprocessingRuleUpdate,
    PreprocessingRuleResponse,
    PreprocessingRuleListResponse,
    PreprocessingExecuteRequest,
    PreprocessingExecuteResponse,
    PreprocessingTaskResponse,
    PreprocessingPreviewRequest,
    PreprocessingPreviewResponse
)
from app.modules.data_management.services.preprocessing_service import PreprocessingService
from app.database.repositories.dataset import DatasetRepository
from app.modules.common.logging import get_logger, set_correlation_id, get_correlation_id
from app.modules.common.logging.decorators import log_async_execution
from app.modules.common.security import sanitize_search, validate_pagination, InputValidator

import pandas as pd
import json
from datetime import datetime

# Initialize logger for this module
logger = get_logger(__name__)

# API Router configuration
router = APIRouter(prefix="/api/preprocessing", tags=["preprocessing"])


# ==================== Helper Functions ====================

def _rule_to_response(rule: DataPreprocessingRule) -> PreprocessingRuleResponse:
    """
    Convert DataPreprocessingRule model to PreprocessingRuleResponse.

    This helper avoids Pydantic validation issues with SQLAlchemy metadata field.
    Manually constructs the response object from rule attributes.
    """
    import json

    # Parse metadata JSON if it's a string
    metadata = rule.extra_metadata if rule.extra_metadata else {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except (json.JSONDecodeError, TypeError):
            metadata = {}
    elif not isinstance(metadata, dict):
        metadata = {}

    # Parse configuration JSON if it's a string
    configuration = rule.configuration if rule.configuration else {}
    if isinstance(configuration, str):
        try:
            configuration = json.loads(configuration)
        except (json.JSONDecodeError, TypeError):
            configuration = {}
    elif not isinstance(configuration, dict):
        configuration = {}

    return PreprocessingRuleResponse(
        id=str(rule.id),
        name=rule.name,
        description=rule.description,
        rule_type=rule.rule_type,
        configuration=configuration,
        is_template=rule.is_template,
        user_id=rule.user_id,
        dataset_id=rule.dataset_id,
        usage_count=rule.usage_count,
        metadata=metadata,
        created_at=rule.created_at,
        updated_at=rule.updated_at
    )


async def set_request_correlation_id(request: Request) -> str:
    """
    Dependency to set correlation ID for request tracking.

    Extracts correlation ID from X-Correlation-ID header or generates new one.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
    set_correlation_id(correlation_id)
    return correlation_id


# ==================== Preprocessing Rule CRUD Endpoints ====================

@router.post("/rules", response_model=PreprocessingRuleResponse, status_code=status.HTTP_201_CREATED)
@log_async_execution(level="INFO")
async def create_preprocessing_rule(
    rule_in: PreprocessingRuleCreate,
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Create a new preprocessing rule/template.

    Args:
        rule_in: Rule creation schema
        db: Database session (injected)
        correlation_id: Request correlation ID (injected)

    Returns:
        PreprocessingRuleResponse with created rule details

    Raises:
        HTTPException: 409 if rule name exists for user, 400 for validation, 500 for database errors
    """
    try:
        # Validate and sanitize inputs
        rule_in.name = InputValidator.sanitize_name(rule_in.name)

        logger.info(f"Creating preprocessing rule: name={rule_in.name}, type={rule_in.rule_type}")

        # Initialize repository
        repo = PreprocessingRuleRepository(db)

        # Check for duplicate name for same user
        if rule_in.user_id:
            existing = await repo.get_by_user_and_name(rule_in.user_id, rule_in.name)
            if existing:
                logger.warning(f"Rule name already exists for user: {rule_in.name}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Rule with name '{rule_in.name}' already exists for this user"
                )

        # Prepare rule data
        rule_data = rule_in.model_dump()

        # Create rule in database
        rule = await repo.create(obj_in=rule_data, commit=True)

        logger.info(
            f"Preprocessing rule created successfully: id={rule.id}, name={rule.name}, "
            f"type={rule.rule_type}"
        )

        return _rule_to_response(rule)

    except ValueError as e:
        logger.warning(f"Invalid input in create rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except IntegrityError as e:
        logger.error(f"Integrity error while creating rule: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Rule with this name already exists"
        )
    except ValidationError as e:
        logger.warning(f"Validation error while creating rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error while creating rule: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error while creating rule: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/rules", response_model=PreprocessingRuleListResponse)
@log_async_execution(level="INFO")
async def list_preprocessing_rules(
    skip: int = Query(0, ge=0, description="Number of records to skip (offset)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    rule_type: Optional[str] = Query(None, description="Filter by rule type"),
    is_template: Optional[bool] = Query(None, description="Filter by template flag"),
    search: Optional[str] = Query(None, description="Search by rule name"),
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    List preprocessing rules with pagination and filtering.

    Args:
        skip: Number of records to skip (default: 0)
        limit: Maximum records to return (default: 100, max: 1000)
        user_id: Optional filter by user ID
        rule_type: Optional filter by rule type
        is_template: Optional filter by template flag
        search: Optional search term for rule names
        db: Database session (injected)
        correlation_id: Request correlation ID (injected)

    Returns:
        PreprocessingRuleListResponse with total count and paginated items

    Raises:
        HTTPException: If database error occurs
    """
    try:
        # Validate and sanitize inputs
        skip, limit = validate_pagination(skip, limit)

        if search:
            search = sanitize_search(search)

        logger.info(
            f"Listing preprocessing rules: skip={skip}, limit={limit}, user_id={user_id}, "
            f"rule_type={rule_type}, is_template={is_template}, search={search}"
        )

        # Initialize repository
        repo = PreprocessingRuleRepository(db)

        # Get rules with filters
        if user_id or rule_type or is_template is not None or search:
            rules = await repo.get_with_filters(
                user_id=user_id,
                rule_type=rule_type,
                is_template=is_template,
                search_term=search,
                skip=skip,
                limit=limit
            )
            # Get total count with same filters
            total = await repo.count(
                **{k: v for k, v in {
                    "user_id": user_id,
                    "rule_type": rule_type,
                    "is_template": is_template
                }.items() if v is not None}
            )
        else:
            rules = await repo.get_multi(skip=skip, limit=limit)
            total = await repo.count()

        logger.info(f"Retrieved {len(rules)} rules (total: {total})")

        # Convert to response models
        items = [_rule_to_response(rule) for rule in rules]

        return PreprocessingRuleListResponse(total=total, items=items)

    except ValueError as e:
        logger.warning(f"Invalid input in list rules: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error while listing rules: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error while listing rules: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/rules/{rule_id}", response_model=PreprocessingRuleResponse)
@log_async_execution(level="INFO")
async def get_preprocessing_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Get a single preprocessing rule by ID.

    Args:
        rule_id: UUID of the rule
        db: Database session (injected)
        correlation_id: Request correlation ID (injected)

    Returns:
        PreprocessingRuleResponse with rule details

    Raises:
        HTTPException: 404 if rule not found, 500 for database errors
    """
    try:
        logger.info(f"Fetching preprocessing rule: id={rule_id}")

        # Initialize repository
        repo = PreprocessingRuleRepository(db)

        # Get rule by ID
        rule = await repo.get(rule_id)

        if rule is None:
            logger.warning(f"Rule not found: id={rule_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preprocessing rule with id {rule_id} not found"
            )

        logger.info(f"Rule retrieved successfully: id={rule_id}, name={rule.name}")

        return _rule_to_response(rule)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching rule {rule_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error while fetching rule {rule_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/rules/{rule_id}", response_model=PreprocessingRuleResponse)
@log_async_execution(level="INFO")
async def update_preprocessing_rule(
    rule_id: str,
    rule_in: PreprocessingRuleUpdate,
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Update an existing preprocessing rule.

    Args:
        rule_id: UUID of the rule to update
        rule_in: Rule update schema (all fields optional)
        db: Database session (injected)
        correlation_id: Request correlation ID (injected)

    Returns:
        PreprocessingRuleResponse with updated rule details

    Raises:
        HTTPException: 404 if rule not found, 409 for conflicts, 400 for validation, 500 for database errors
    """
    try:
        logger.info(f"Updating preprocessing rule: id={rule_id}")

        # Initialize repository
        repo = PreprocessingRuleRepository(db)

        # Check if rule exists
        existing_rule = await repo.get(rule_id)
        if existing_rule is None:
            logger.warning(f"Rule not found for update: id={rule_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preprocessing rule with id {rule_id} not found"
            )

        # Check for name conflict if name is being updated
        if rule_in.name and rule_in.name != existing_rule.name and existing_rule.user_id:
            name_conflict = await repo.get_by_user_and_name(existing_rule.user_id, rule_in.name)
            if name_conflict:
                logger.warning(
                    f"Rule name already exists during update: {rule_in.name}"
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Rule with name '{rule_in.name}' already exists"
                )

        # Prepare update data (exclude unset fields)
        update_data = rule_in.model_dump(exclude_unset=True)

        logger.debug(f"Update data: {update_data}")

        # Update rule in database
        updated_rule = await repo.update(
            id=rule_id,
            obj_in=update_data,
            commit=True
        )

        logger.info(
            f"Rule updated successfully: id={rule_id}, "
            f"updated_fields={list(update_data.keys())}"
        )

        return _rule_to_response(updated_rule)

    except HTTPException:
        raise
    except IntegrityError as e:
        logger.error(f"Integrity error while updating rule {rule_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Rule constraint violation"
        )
    except ValidationError as e:
        logger.warning(f"Validation error while updating rule {rule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error while updating rule {rule_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error while updating rule {rule_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
@log_async_execution(level="INFO")
async def delete_preprocessing_rule(
    rule_id: str,
    hard_delete: bool = Query(False, description="Permanently delete (true) or soft delete (false)"),
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Delete a preprocessing rule (soft delete by default).

    Args:
        rule_id: UUID of the rule to delete
        hard_delete: If True, permanently delete; if False, soft delete (default)
        db: Database session (injected)
        correlation_id: Request correlation ID (injected)

    Returns:
        204 No Content on success

    Raises:
        HTTPException: 404 if rule not found, 500 for database errors
    """
    try:
        logger.info(f"Deleting preprocessing rule: id={rule_id}, hard_delete={hard_delete}")

        # Initialize repository
        repo = PreprocessingRuleRepository(db)

        # Delete rule
        deleted = await repo.delete(id=rule_id, soft=not hard_delete, commit=True)

        if not deleted:
            logger.warning(f"Rule not found for deletion: id={rule_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preprocessing rule with id {rule_id} not found"
            )

        delete_type = "hard" if hard_delete else "soft"
        logger.info(f"Rule {delete_type} deleted successfully: id={rule_id}")

        return None  # 204 No Content

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while deleting rule {rule_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error while deleting rule {rule_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# ==================== Preprocessing Execution Endpoints ====================

@router.post("/execute", response_model=PreprocessingExecuteResponse, status_code=status.HTTP_201_CREATED)
@log_async_execution(level="INFO")
async def execute_preprocessing(
    request_in: PreprocessingExecuteRequest,
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Execute preprocessing on a dataset.

    Args:
        request_in: Preprocessing execution request
        db: Database session (injected)
        correlation_id: Request correlation ID (injected)

    Returns:
        PreprocessingExecuteResponse with task ID and status

    Raises:
        HTTPException: 404 if dataset/rule not found, 400 for validation, 500 for errors
    """
    try:
        logger.info(f"Executing preprocessing on dataset: {request_in.dataset_id}")

        # Validate that either rule_id or operations is provided
        if not request_in.rule_id and not request_in.operations:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either rule_id or operations must be provided"
            )

        # Initialize repositories
        dataset_repo = DatasetRepository(db)
        rule_repo = PreprocessingRuleRepository(db)
        task_repo = PreprocessingTaskRepository(db)

        # Verify dataset exists
        dataset = await dataset_repo.get(request_in.dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset with id {request_in.dataset_id} not found"
            )

        # Get execution config
        execution_config = {}
        rule_id = None

        if request_in.rule_id:
            # Use rule configuration
            rule = await rule_repo.get(request_in.rule_id)
            if not rule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Preprocessing rule with id {request_in.rule_id} not found"
                )
            execution_config = rule.configuration
            rule_id = rule.id

            # Increment usage count
            await rule_repo.increment_usage_count(rule.id)
        else:
            # Use inline operations
            execution_config = {"operations": request_in.operations}

        # Generate task name
        task_name = request_in.output_dataset_name or f"Preprocess {dataset.name}"

        # Create preprocessing task
        task_data = {
            "task_name": task_name,
            "status": PreprocessingTaskStatus.PENDING.value,
            "dataset_id": request_in.dataset_id,
            "rule_id": rule_id,
            "execution_config": execution_config,
            "user_id": request_in.user_id,
            "total_operations": len(request_in.operations) if request_in.operations else 1,
            "input_row_count": dataset.row_count
        }

        task = await task_repo.create(obj_in=task_data, commit=True)

        logger.info(
            f"Preprocessing task created: id={task.id}, dataset={request_in.dataset_id}, "
            f"status={task.status}"
        )

        return PreprocessingExecuteResponse(
            task_id=task.id,
            task_name=task.task_name,
            status=task.status,
            dataset_id=task.dataset_id,
            message="Preprocessing task created successfully"
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while executing preprocessing: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error while executing preprocessing: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# ==================== Preprocessing Task Status Endpoints ====================

@router.get("/tasks/{task_id}", response_model=PreprocessingTaskResponse)
@log_async_execution(level="INFO")
async def get_preprocessing_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Get preprocessing task status and details.

    Args:
        task_id: UUID of the task
        db: Database session (injected)
        correlation_id: Request correlation ID (injected)

    Returns:
        PreprocessingTaskResponse with task details

    Raises:
        HTTPException: 404 if task not found, 500 for database errors
    """
    try:
        logger.info(f"Fetching preprocessing task: id={task_id}")

        # Initialize repository
        repo = PreprocessingTaskRepository(db)

        # Get task by ID
        task = await repo.get(task_id)

        if task is None:
            logger.warning(f"Task not found: id={task_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preprocessing task with id {task_id} not found"
            )

        logger.info(
            f"Task retrieved successfully: id={task_id}, status={task.status}, "
            f"progress={task.progress_percentage}%"
        )

        return PreprocessingTaskResponse.model_validate(task, from_attributes=True)

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching task {task_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error while fetching task {task_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


# ==================== Preprocessing Preview Endpoints ====================

@router.post("/preview", response_model=PreprocessingPreviewResponse)
@log_async_execution(level="INFO")
async def preview_preprocessing(
    request_in: PreprocessingPreviewRequest,
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Preview preprocessing results without persisting.

    Args:
        request_in: Preview request with dataset ID and operations
        db: Database session (injected)
        correlation_id: Request correlation ID (injected)

    Returns:
        PreprocessingPreviewResponse with preview data and statistics

    Raises:
        HTTPException: 404 if dataset not found, 400 for validation, 500 for errors
    """
    try:
        logger.info(
            f"Previewing preprocessing on dataset: {request_in.dataset_id}, "
            f"preview_rows={request_in.preview_rows}"
        )

        # Initialize repositories
        dataset_repo = DatasetRepository(db)

        # Verify dataset exists
        dataset = await dataset_repo.get(request_in.dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset with id {request_in.dataset_id} not found"
            )

        # Load dataset (mock for now - in real implementation, load from file_path)
        # For testing purposes, create a sample DataFrame
        original_df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=100),
            "price": [100 + i + (i % 5 == 0) * float('nan') for i in range(100)],
            "volume": [1000 + i * 10 for i in range(100)]
        })

        original_row_count = len(original_df)
        result_df = original_df.copy()
        warnings = []

        # Initialize preprocessing service
        rule_repo = PreprocessingRuleRepository(db)
        preprocessing_service = PreprocessingService(rule_repo)

        # Apply operations
        for operation in request_in.operations:
            op_type = operation.get("type")
            op_config = operation.get("config", {})

            if op_type == "missing_value":
                result_df = await preprocessing_service.handle_missing_values(result_df, op_config)
            elif op_type == "outlier":
                result_df = await preprocessing_service.handle_outliers(result_df, op_config)
            elif op_type == "transformation":
                result_df = await preprocessing_service.transform_data(result_df, op_config)
            elif op_type == "filter":
                result_df = await preprocessing_service.filter_data(result_df, op_config)

        # Prepare preview data
        preview_df = result_df.head(request_in.preview_rows)
        preview_data = preview_df.to_dict(orient="records")

        # Calculate statistics
        rows_affected = original_row_count - len(result_df)
        statistics = {
            "rows_deleted": rows_affected,
            "operations_applied": len(request_in.operations)
        }

        logger.info(
            f"Preview completed: original_rows={original_row_count}, "
            f"output_rows={len(result_df)}, preview_rows={len(preview_df)}"
        )

        return PreprocessingPreviewResponse(
            original_row_count=original_row_count,
            preview_row_count=len(preview_df),
            estimated_output_rows=len(result_df),
            preview_data=preview_data,
            columns=list(result_df.columns),
            statistics=statistics,
            warnings=warnings
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while previewing preprocessing: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error while previewing preprocessing: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
