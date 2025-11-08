"""
Dataset API Endpoints

This module provides RESTful API endpoints for dataset management with:
- Full CRUD operations (Create, Read, Update, Delete)
- Database persistence with SQLAlchemy
- Comprehensive logging with correlation IDs
- Proper error handling and validation
- Pagination support
"""

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, Query, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import ValidationError

from app.database import get_db
from app.database.models.dataset import Dataset, DatasetStatus
from app.database.repositories.dataset import DatasetRepository
from app.modules.data_management.schemas.dataset import (
    DatasetCreate,
    DatasetUpdate,
    DatasetResponse,
    DatasetListResponse
)
from app.modules.common.logging import get_logger, set_correlation_id, get_correlation_id
from app.modules.common.logging.decorators import log_async_execution
from app.modules.common.security import sanitize_search, validate_pagination, InputValidator

# Initialize logger for this module
logger = get_logger(__name__)

# API Router configuration
router = APIRouter(prefix="/api/datasets", tags=["datasets"])


async def set_request_correlation_id(request: Request) -> str:
    """
    Dependency to set correlation ID for request tracking.

    Extracts correlation ID from X-Correlation-ID header or generates new one.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
    set_correlation_id(correlation_id)
    return correlation_id


def _dataset_to_response(dataset: Dataset) -> DatasetResponse:
    """
    Convert Dataset model to DatasetResponse.

    Manual conversion to avoid Pydantic confusion between SQLAlchemy's metadata
    attribute and the database field extra_metadata.

    Args:
        dataset: SQLAlchemy Dataset model instance

    Returns:
        DatasetResponse: Pydantic response model
    """
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        source=dataset.source,
        file_path=dataset.file_path,
        status=dataset.status,
        row_count=dataset.row_count,
        columns=dataset.columns if isinstance(dataset.columns, list) else [],
        extra_metadata=dataset.extra_metadata if isinstance(dataset.extra_metadata, dict) else {},
        created_at=dataset.created_at,
        updated_at=dataset.updated_at
    )


@router.get("", response_model=DatasetListResponse)
@log_async_execution(level="INFO")
async def list_datasets(
    skip: int = Query(0, ge=0, description="Number of records to skip (offset)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    source: Optional[str] = Query(None, description="Filter by data source (local, qlib, thirdparty)"),
    dataset_status: Optional[str] = Query(None, description="Filter by status (valid, invalid, pending)"),
    search: Optional[str] = Query(None, description="Search by dataset name"),
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    List datasets with pagination and filtering.

    Args:
        skip: Number of records to skip (default: 0)
        limit: Maximum records to return (default: 100, max: 1000)
        source: Optional filter by data source
        dataset_status: Optional filter by validation status
        search: Optional search term for dataset names
        db: Database session (injected)
        correlation_id: Request correlation ID (injected)

    Returns:
        DatasetListResponse with total count and paginated items

    Raises:
        HTTPException: If database error occurs
    """
    try:
        # Validate and sanitize inputs
        skip, limit = validate_pagination(skip, limit)

        # Sanitize search term
        if search:
            search = sanitize_search(search)

        logger.info(
            f"Listing datasets: skip={skip}, limit={limit}, source={source}, "
            f"status={dataset_status}, search={search}"
        )

        # Initialize repository
        repo = DatasetRepository(db)

        # Get datasets with filters
        if source or dataset_status or search:
            datasets = await repo.get_with_filters(
                source=source,
                status=dataset_status,
                search_term=search,
                skip=skip,
                limit=limit
            )
            # Get total count with same filters
            total = await repo.count(
                **{k: v for k, v in {
                    "source": source,
                    "status": dataset_status
                }.items() if v}
            )
        else:
            datasets = await repo.get_multi(skip=skip, limit=limit)
            total = await repo.count()

        logger.info(f"Retrieved {len(datasets)} datasets (total: {total})")

        # Convert to response models
        items = [_dataset_to_response(ds) for ds in datasets]

        return DatasetListResponse(total=total, items=items)

    except ValueError as e:
        # Input validation errors
        logger.warning(f"Invalid input in list datasets: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error while listing datasets: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error while listing datasets: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{dataset_id}", response_model=DatasetResponse)
@log_async_execution(level="INFO")
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Get a single dataset by ID.

    Args:
        dataset_id: UUID of the dataset
        db: Database session (injected)
        correlation_id: Request correlation ID (injected)

    Returns:
        DatasetResponse with dataset details

    Raises:
        HTTPException: 404 if dataset not found, 500 for database errors
    """
    try:
        logger.info(f"Fetching dataset: id={dataset_id}")

        # Initialize repository
        repo = DatasetRepository(db)

        # Get dataset by ID
        dataset = await repo.get(dataset_id)

        if dataset is None:
            logger.warning(f"Dataset not found: id={dataset_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset with id {dataset_id} not found"
            )

        logger.info(f"Dataset retrieved successfully: id={dataset_id}, name={dataset.name}")

        return _dataset_to_response(dataset)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error while fetching dataset {dataset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
@log_async_execution(level="INFO")
async def create_dataset(
    dataset_in: DatasetCreate,
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Create a new dataset.

    Args:
        dataset_in: Dataset creation schema
        db: Database session (injected)
        correlation_id: Request correlation ID (injected)

    Returns:
        DatasetResponse with created dataset details

    Raises:
        HTTPException: 409 if dataset name exists, 400 for validation errors, 500 for database errors
    """
    try:
        # Validate and sanitize inputs
        dataset_in.name = InputValidator.sanitize_name(dataset_in.name)
        dataset_in.file_path = InputValidator.sanitize_file_path(dataset_in.file_path)

        # Validate JSON fields size (DatasetCreate only has extra_metadata, not columns)
        if dataset_in.extra_metadata:
            import json
            InputValidator.validate_json_size(json.dumps(dataset_in.extra_metadata))

        logger.info(f"Creating dataset: name={dataset_in.name}, source={dataset_in.source}")

        # Initialize repository
        repo = DatasetRepository(db)

        # Check for duplicate name
        existing = await repo.get_by_name(dataset_in.name)
        if existing:
            logger.warning(f"Dataset name already exists: {dataset_in.name}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Dataset with name '{dataset_in.name}' already exists"
            )

        # Prepare dataset data
        dataset_data = dataset_in.model_dump()
        # Convert enum to string value
        dataset_data["source"] = dataset_in.source.value
        # Set initial status
        dataset_data["status"] = DatasetStatus.PENDING.value

        # Create dataset in database
        dataset = await repo.create(obj_in=dataset_data, commit=True)

        logger.info(
            f"Dataset created successfully: id={dataset.id}, name={dataset.name}, "
            f"source={dataset.source}"
        )

        return _dataset_to_response(dataset)

    except ValueError as e:
        # Input validation errors
        logger.warning(f"Invalid input in create dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except IntegrityError as e:
        logger.error(f"Integrity error while creating dataset: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dataset with this name or constraint already exists"
        )
    except ValidationError as e:
        logger.warning(f"Validation error while creating dataset: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error while creating dataset: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error while creating dataset: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.put("/{dataset_id}", response_model=DatasetResponse)
@log_async_execution(level="INFO")
async def update_dataset(
    dataset_id: str,
    dataset_in: DatasetUpdate,
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Update an existing dataset.

    Args:
        dataset_id: UUID of the dataset to update
        dataset_in: Dataset update schema (all fields optional)
        db: Database session (injected)
        correlation_id: Request correlation ID (injected)

    Returns:
        DatasetResponse with updated dataset details

    Raises:
        HTTPException: 404 if dataset not found, 409 for conflicts, 400 for validation, 500 for database errors
    """
    try:
        logger.info(f"Updating dataset: id={dataset_id}")

        # Initialize repository
        repo = DatasetRepository(db)

        # Check if dataset exists
        existing_dataset = await repo.get(dataset_id)
        if existing_dataset is None:
            logger.warning(f"Dataset not found for update: id={dataset_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset with id {dataset_id} not found"
            )

        # Check for name conflict if name is being updated
        if dataset_in.name and dataset_in.name != existing_dataset.name:
            name_conflict = await repo.get_by_name(dataset_in.name)
            if name_conflict:
                logger.warning(
                    f"Dataset name already exists during update: {dataset_in.name}"
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Dataset with name '{dataset_in.name}' already exists"
                )

        # Prepare update data (exclude unset fields)
        update_data = dataset_in.model_dump(exclude_unset=True)

        # Convert enum to string if status is provided
        if "status" in update_data and update_data["status"]:
            update_data["status"] = update_data["status"].value

        logger.debug(f"Update data: {update_data}")

        # Update dataset in database
        updated_dataset = await repo.update(
            id=dataset_id,
            obj_in=update_data,
            commit=True
        )

        logger.info(
            f"Dataset updated successfully: id={dataset_id}, "
            f"updated_fields={list(update_data.keys())}"
        )

        return _dataset_to_response(updated_dataset)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except IntegrityError as e:
        logger.error(f"Integrity error while updating dataset {dataset_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Dataset constraint violation"
        )
    except ValidationError as e:
        logger.warning(f"Validation error while updating dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except SQLAlchemyError as e:
        logger.error(f"Database error while updating dataset {dataset_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error while updating dataset {dataset_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
@log_async_execution(level="INFO")
async def delete_dataset(
    dataset_id: str,
    hard_delete: bool = Query(False, description="Permanently delete (true) or soft delete (false)"),
    db: AsyncSession = Depends(get_db),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Delete a dataset (soft delete by default).

    Args:
        dataset_id: UUID of the dataset to delete
        hard_delete: If True, permanently delete; if False, soft delete (default)
        db: Database session (injected)
        correlation_id: Request correlation ID (injected)

    Returns:
        204 No Content on success

    Raises:
        HTTPException: 404 if dataset not found, 500 for database errors
    """
    try:
        logger.info(f"Deleting dataset: id={dataset_id}, hard_delete={hard_delete}")

        # Initialize repository
        repo = DatasetRepository(db)

        # Delete dataset
        deleted = await repo.delete(id=dataset_id, soft=not hard_delete, commit=True)

        if not deleted:
            logger.warning(f"Dataset not found for deletion: id={dataset_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset with id {dataset_id} not found"
            )

        delete_type = "hard" if hard_delete else "soft"
        logger.info(f"Dataset {delete_type} deleted successfully: id={dataset_id}")

        return None  # 204 No Content

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error while deleting dataset {dataset_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error while deleting dataset {dataset_id}: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )
