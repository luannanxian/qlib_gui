"""Indicator API Router

Provides endpoints for discovering and managing technical indicators.
"""

from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, HTTPException, status, Query, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.indicator.schemas.indicator import (
    IndicatorResponse,
    IndicatorListResponse,
    IndicatorCategoryListResponse
)
from app.modules.indicator.services.indicator_service import IndicatorService
from app.database.repositories.indicator_repository import IndicatorRepository
from app.modules.common.logging import get_logger, set_correlation_id
from app.modules.common.logging.decorators import log_async_execution

# Initialize logger for this module
logger = get_logger(__name__)

router = APIRouter(prefix="/api/indicators", tags=["indicators"])


async def set_request_correlation_id(request: Request) -> str:
    """
    Dependency to set correlation ID for request tracking.

    Extracts correlation ID from X-Correlation-ID header or generates new one.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
    set_correlation_id(correlation_id)
    return correlation_id


def get_indicator_service(db: AsyncSession = Depends(get_db)) -> IndicatorService:
    """Dependency to get IndicatorService instance."""
    indicator_repo = IndicatorRepository(db)
    return IndicatorService(indicator_repo)


@router.get("", response_model=IndicatorListResponse)
@log_async_execution(level="INFO")
async def list_indicators(
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: IndicatorService = Depends(get_indicator_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    List indicators with optional filtering and pagination.

    Args:
        category: Optional category filter
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        service: IndicatorService instance
        correlation_id: Request correlation ID

    Returns:
        IndicatorListResponse with list of indicators
    """
    try:
        if category:
            result = await service.get_indicators_by_category(
                category=category,
                skip=skip,
                limit=limit
            )
        else:
            # Get all indicators when no category filter
            result = await service.get_all_indicators(
                skip=skip,
                limit=limit
            )
        return result
    except ValueError as e:
        logger.error(f"Validation error listing indicators: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error listing indicators: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list indicators"
        )


@router.get("/categories", response_model=IndicatorCategoryListResponse)
@log_async_execution(level="INFO")
async def get_categories(
    service: IndicatorService = Depends(get_indicator_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Get all available indicator categories.

    Args:
        service: IndicatorService instance
        correlation_id: Request correlation ID

    Returns:
        IndicatorCategoryListResponse with list of categories
    """
    try:
        result = await service.get_indicator_categories()
        return result
    except Exception as e:
        logger.error(f"Error getting indicator categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get indicator categories"
        )


@router.get("/search", response_model=IndicatorListResponse)
@log_async_execution(level="INFO")
async def search_indicators(
    keyword: str = Query(..., min_length=1, description="Search keyword"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    service: IndicatorService = Depends(get_indicator_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Search indicators by keyword (name, description).

    Args:
        keyword: Search keyword (required)
        skip: Number of records to skip
        limit: Maximum number of records to return
        service: IndicatorService instance
        correlation_id: Request correlation ID

    Returns:
        IndicatorListResponse with search results
    """
    try:
        result = await service.search_indicators(
            keyword=keyword,
            skip=skip,
            limit=limit
        )
        return result
    except Exception as e:
        logger.error(f"Error searching indicators: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search indicators"
        )


@router.get("/popular", response_model=IndicatorListResponse)
@log_async_execution(level="INFO")
async def get_popular_indicators(
    limit: int = Query(10, ge=1, le=50, description="Number of indicators to return"),
    service: IndicatorService = Depends(get_indicator_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Get popular indicators by usage count.

    Args:
        limit: Number of indicators to return
        service: IndicatorService instance
        correlation_id: Request correlation ID

    Returns:
        IndicatorListResponse with popular indicators
    """
    try:
        result = await service.get_popular_indicators(limit=limit)
        return result
    except Exception as e:
        logger.error(f"Error getting popular indicators: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get popular indicators"
        )


@router.get("/{indicator_id}", response_model=IndicatorResponse)
@log_async_execution(level="INFO")
async def get_indicator(
    indicator_id: str,
    service: IndicatorService = Depends(get_indicator_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Get detailed information about a specific indicator.

    Args:
        indicator_id: Indicator ID
        service: IndicatorService instance
        correlation_id: Request correlation ID

    Returns:
        IndicatorResponse with indicator details

    Raises:
        404: If indicator not found
    """
    try:
        indicator = await service.get_indicator_detail(indicator_id)
        if not indicator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Indicator with id '{indicator_id}' not found"
            )
        return indicator
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting indicator {indicator_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get indicator"
        )


@router.post("/{indicator_id}/increment-usage")
@log_async_execution(level="INFO")
async def increment_usage(
    indicator_id: str,
    service: IndicatorService = Depends(get_indicator_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Increment usage count for an indicator.

    Args:
        indicator_id: Indicator ID
        service: IndicatorService instance
        correlation_id: Request correlation ID

    Returns:
        Success message

    Raises:
        404: If indicator not found
    """
    try:
        # First check if indicator exists
        indicator = await service.get_indicator_detail(indicator_id)
        if not indicator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Indicator with id '{indicator_id}' not found"
            )

        success = await service.increment_usage(indicator_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to increment usage count"
            )

        return {"message": "Usage count incremented successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error incrementing usage for indicator {indicator_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to increment usage count"
        )
