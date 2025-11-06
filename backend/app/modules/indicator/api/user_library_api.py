"""User Library API Router

Provides endpoints for managing user's factor library.
"""

from uuid import uuid4
from fastapi import APIRouter, HTTPException, status, Query, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.indicator.schemas.user_library import (
    UserLibraryItemResponse,
    UserLibraryListResponse,
    AddToLibraryRequest,
    ToggleFavoriteRequest,
    LibraryStatsResponse
)
from app.modules.indicator.services.user_library_service import UserLibraryService
from app.database.repositories.user_factor_library_repository import UserFactorLibraryRepository
from app.modules.common.logging import get_logger, set_correlation_id
from app.modules.common.logging.decorators import log_async_execution

# Initialize logger for this module
logger = get_logger(__name__)

router = APIRouter(prefix="/api/user-library", tags=["user-library"])


async def set_request_correlation_id(request: Request) -> str:
    """
    Dependency to set correlation ID for request tracking.

    Extracts correlation ID from X-Correlation-ID header or generates new one.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
    set_correlation_id(correlation_id)
    return correlation_id


def get_user_library_service(db: AsyncSession = Depends(get_db)) -> UserLibraryService:
    """Dependency to get UserLibraryService instance."""
    user_library_repo = UserFactorLibraryRepository(db)
    return UserLibraryService(user_library_repo)


# TODO: Add authentication dependency to get current user
def get_current_user_id() -> str:
    """Temporary: Return a mock user ID until authentication is implemented."""
    return "user123"


@router.get("", response_model=UserLibraryListResponse)
@log_async_execution(level="INFO")
async def get_library(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    user_id: str = Depends(get_current_user_id),
    service: UserLibraryService = Depends(get_user_library_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Get user's library items.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        user_id: Current user ID (from authentication)
        service: UserLibraryService instance
        correlation_id: Request correlation ID

    Returns:
        UserLibraryListResponse with list of library items
    """
    try:
        result = await service.get_user_library(
            user_id=user_id,
            skip=skip,
            limit=limit
        )
        return result
    except Exception as e:
        logger.error(f"Error getting user library: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get library"
        )


@router.post("", response_model=UserLibraryItemResponse, status_code=status.HTTP_201_CREATED)
@log_async_execution(level="INFO")
async def add_to_library(
    request_data: AddToLibraryRequest,
    user_id: str = Depends(get_current_user_id),
    service: UserLibraryService = Depends(get_user_library_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Add a factor to user's library.

    Args:
        request_data: Factor ID to add
        user_id: Current user ID (from authentication)
        service: UserLibraryService instance
        correlation_id: Request correlation ID

    Returns:
        UserLibraryItemResponse with added item
    """
    try:
        result = await service.add_to_library(
            user_id=user_id,
            factor_id=request_data.factor_id
        )
        return result["item"]
    except ValueError as e:
        logger.error(f"Validation error adding to library: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error adding to library: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add to library"
        )


@router.put("/{factor_id}/favorite", response_model=UserLibraryItemResponse)
@log_async_execution(level="INFO")
async def toggle_favorite(
    factor_id: str,
    request_data: ToggleFavoriteRequest,
    user_id: str = Depends(get_current_user_id),
    service: UserLibraryService = Depends(get_user_library_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Toggle favorite status of a library item.

    Args:
        factor_id: Factor ID
        request_data: New favorite status
        user_id: Current user ID (from authentication)
        service: UserLibraryService instance
        correlation_id: Request correlation ID

    Returns:
        UserLibraryItemResponse with updated item

    Raises:
        404: If library item not found
    """
    try:
        result = await service.toggle_favorite(
            user_id=user_id,
            factor_id=factor_id,
            is_favorite=request_data.is_favorite
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Library item not found for factor '{factor_id}'"
            )
        return result["item"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling favorite: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle favorite"
        )


@router.delete("/{factor_id}", status_code=status.HTTP_204_NO_CONTENT)
@log_async_execution(level="INFO")
async def remove_from_library(
    factor_id: str,
    user_id: str = Depends(get_current_user_id),
    service: UserLibraryService = Depends(get_user_library_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Remove a factor from user's library.

    Args:
        factor_id: Factor ID to remove
        user_id: Current user ID (from authentication)
        service: UserLibraryService instance
        correlation_id: Request correlation ID

    Raises:
        404: If library item not found
    """
    try:
        success = await service.remove_from_library(
            user_id=user_id,
            factor_id=factor_id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Library item not found for factor '{factor_id}'"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from library: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove from library"
        )


@router.get("/favorites", response_model=UserLibraryListResponse)
@log_async_execution(level="INFO")
async def get_favorites(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    user_id: str = Depends(get_current_user_id),
    service: UserLibraryService = Depends(get_user_library_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Get user's favorite library items.

    Args:
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        user_id: Current user ID (from authentication)
        service: UserLibraryService instance
        correlation_id: Request correlation ID

    Returns:
        UserLibraryListResponse with favorite items
    """
    try:
        result = await service.get_favorites(
            user_id=user_id,
            skip=skip,
            limit=limit
        )
        return result
    except Exception as e:
        logger.error(f"Error getting favorites: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get favorites"
        )


@router.get("/most-used", response_model=UserLibraryListResponse)
@log_async_execution(level="INFO")
async def get_most_used(
    limit: int = Query(10, ge=1, le=50, description="Number of items to return"),
    user_id: str = Depends(get_current_user_id),
    service: UserLibraryService = Depends(get_user_library_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Get user's most used library items.

    Args:
        limit: Number of items to return
        user_id: Current user ID (from authentication)
        service: UserLibraryService instance
        correlation_id: Request correlation ID

    Returns:
        UserLibraryListResponse with most used items
    """
    try:
        result = await service.get_most_used(
            user_id=user_id,
            limit=limit
        )
        return result
    except Exception as e:
        logger.error(f"Error getting most used: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get most used items"
        )


@router.get("/stats", response_model=LibraryStatsResponse)
@log_async_execution(level="INFO")
async def get_library_stats(
    user_id: str = Depends(get_current_user_id),
    service: UserLibraryService = Depends(get_user_library_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Get statistics about user's library.

    Args:
        user_id: Current user ID (from authentication)
        service: UserLibraryService instance
        correlation_id: Request correlation ID

    Returns:
        LibraryStatsResponse with library statistics
    """
    try:
        result = await service.get_library_stats(user_id=user_id)
        return result
    except Exception as e:
        logger.error(f"Error getting library stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get library stats"
        )


@router.post("/{factor_id}/increment-usage")
@log_async_execution(level="INFO")
async def increment_usage(
    factor_id: str,
    user_id: str = Depends(get_current_user_id),
    service: UserLibraryService = Depends(get_user_library_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Increment usage count for a library item.

    Args:
        factor_id: Factor ID
        user_id: Current user ID (from authentication)
        service: UserLibraryService instance
        correlation_id: Request correlation ID

    Returns:
        Success message
    """
    try:
        success = await service.increment_usage(
            user_id=user_id,
            factor_id=factor_id
        )
        if not success:
            # Note: This doesn't raise 404 because increment_usage might auto-create
            logger.warning(f"Failed to increment usage for factor {factor_id}")
        return {"message": "Usage count incremented successfully"}
    except Exception as e:
        logger.error(f"Error incrementing usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to increment usage count"
        )
