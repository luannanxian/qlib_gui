"""Custom Factor API Router

Provides endpoints for creating and managing custom factors.
"""

from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, HTTPException, status, Query, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.modules.indicator.schemas.custom_factor import (
    CustomFactorCreate,
    CustomFactorUpdate,
    CustomFactorResponse,
    CustomFactorListResponse,
    PublishFactorRequest,
    CloneFactorRequest
)
from app.modules.indicator.services.custom_factor_service import CustomFactorService
from app.database.repositories.custom_factor_repository import CustomFactorRepository
from app.modules.common.logging import get_logger, set_correlation_id
from app.modules.common.logging.decorators import log_async_execution

# Initialize logger for this module
logger = get_logger(__name__)

router = APIRouter(prefix="/api/custom-factors", tags=["custom-factors"])


async def set_request_correlation_id(request: Request) -> str:
    """
    Dependency to set correlation ID for request tracking.

    Extracts correlation ID from X-Correlation-ID header or generates new one.
    """
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
    set_correlation_id(correlation_id)
    return correlation_id


def get_custom_factor_service(db: AsyncSession = Depends(get_db)) -> CustomFactorService:
    """Dependency to get CustomFactorService instance."""
    custom_factor_repo = CustomFactorRepository(db)
    return CustomFactorService(custom_factor_repo)


# TODO: Add authentication dependency to get current user
def get_current_user_id() -> str:
    """Temporary: Return a mock user ID until authentication is implemented."""
    return "user123"


@router.post("", response_model=CustomFactorResponse, status_code=status.HTTP_201_CREATED)
@log_async_execution(level="INFO")
async def create_factor(
    factor_data: CustomFactorCreate,
    user_id: str = Depends(get_current_user_id),
    service: CustomFactorService = Depends(get_custom_factor_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Create a new custom factor.

    Args:
        factor_data: Factor creation data
        user_id: Current user ID (from authentication)
        service: CustomFactorService instance
        correlation_id: Request correlation ID

    Returns:
        CustomFactorResponse with created factor
    """
    try:
        result = await service.create_factor(
            factor_data=factor_data.model_dump(),
            authenticated_user_id=user_id
        )
        return result["factor"]
    except ValueError as e:
        logger.error(f"Validation error creating factor: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating factor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create factor"
        )


@router.get("", response_model=CustomFactorListResponse)
@log_async_execution(level="INFO")
async def list_user_factors(
    status: Optional[str] = Query(None, description="Filter by status (draft, published, etc.)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    user_id: str = Depends(get_current_user_id),
    service: CustomFactorService = Depends(get_custom_factor_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    List current user's custom factors.

    Args:
        status: Optional status filter (draft, published, etc.)
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        user_id: Current user ID (from authentication)
        service: CustomFactorService instance
        correlation_id: Request correlation ID

    Returns:
        CustomFactorListResponse with list of factors
    """
    try:
        result = await service.get_user_factors(
            user_id=user_id,
            status=status,
            skip=skip,
            limit=limit
        )
        return result
    except Exception as e:
        logger.error(f"Error listing user factors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list factors"
        )


@router.get("/{factor_id}", response_model=CustomFactorResponse)
@log_async_execution(level="INFO")
async def get_factor(
    factor_id: str,
    user_id: str = Depends(get_current_user_id),
    service: CustomFactorService = Depends(get_custom_factor_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Get a specific custom factor.

    Args:
        factor_id: Factor ID
        user_id: Current user ID (from authentication)
        service: CustomFactorService instance
        correlation_id: Request correlation ID

    Returns:
        CustomFactorResponse with factor details

    Raises:
        404: If factor not found or user not authorized
    """
    try:
        factor = await service.get_factor_detail(factor_id, user_id)
        if not factor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Factor with id '{factor_id}' not found or access denied"
            )
        return factor["factor"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting factor {factor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get factor"
        )


@router.put("/{factor_id}", response_model=CustomFactorResponse)
@log_async_execution(level="INFO")
async def update_factor(
    factor_id: str,
    factor_data: CustomFactorUpdate,
    user_id: str = Depends(get_current_user_id),
    service: CustomFactorService = Depends(get_custom_factor_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Update a custom factor.

    Args:
        factor_id: Factor ID
        factor_data: Factor update data
        user_id: Current user ID (from authentication)
        service: CustomFactorService instance
        correlation_id: Request correlation ID

    Returns:
        CustomFactorResponse with updated factor

    Raises:
        404: If factor not found or user not authorized
    """
    try:
        result = await service.update_factor(
            factor_id=factor_id,
            factor_data=factor_data.model_dump(exclude_unset=True),
            authenticated_user_id=user_id
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Factor with id '{factor_id}' not found or access denied"
            )
        return result["factor"]
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating factor: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating factor {factor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update factor"
        )


@router.delete("/{factor_id}", status_code=status.HTTP_204_NO_CONTENT)
@log_async_execution(level="INFO")
async def delete_factor(
    factor_id: str,
    user_id: str = Depends(get_current_user_id),
    service: CustomFactorService = Depends(get_custom_factor_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Delete a custom factor.

    Args:
        factor_id: Factor ID
        user_id: Current user ID (from authentication)
        service: CustomFactorService instance
        correlation_id: Request correlation ID

    Raises:
        404: If factor not found or user not authorized
    """
    try:
        success = await service.delete_factor(factor_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Factor with id '{factor_id}' not found or access denied"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting factor {factor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete factor"
        )


@router.post("/{factor_id}/publish", response_model=CustomFactorResponse)
@log_async_execution(level="INFO")
async def publish_factor(
    factor_id: str,
    publish_data: PublishFactorRequest,
    user_id: str = Depends(get_current_user_id),
    service: CustomFactorService = Depends(get_custom_factor_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Publish a custom factor.

    Args:
        factor_id: Factor ID
        publish_data: Publish configuration
        user_id: Current user ID (from authentication)
        service: CustomFactorService instance
        correlation_id: Request correlation ID

    Returns:
        CustomFactorResponse with published factor

    Raises:
        404: If factor not found or user not authorized
    """
    try:
        result = await service.publish_factor(
            factor_id=factor_id,
            authenticated_user_id=user_id,
            is_public=publish_data.is_public
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Factor with id '{factor_id}' not found or access denied"
            )
        return result["factor"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing factor {factor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish factor"
        )


@router.post("/{factor_id}/clone", response_model=CustomFactorResponse, status_code=status.HTTP_201_CREATED)
@log_async_execution(level="INFO")
async def clone_factor(
    factor_id: str,
    clone_data: CloneFactorRequest,
    user_id: str = Depends(get_current_user_id),
    service: CustomFactorService = Depends(get_custom_factor_service),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Clone a custom factor.

    Args:
        factor_id: Factor ID to clone
        clone_data: Clone configuration
        user_id: Current user ID (from authentication)
        service: CustomFactorService instance
        correlation_id: Request correlation ID

    Returns:
        CustomFactorResponse with cloned factor

    Raises:
        404: If factor not found
    """
    try:
        result = await service.clone_factor(
            factor_id=factor_id,
            authenticated_user_id=user_id,
            new_name=clone_data.new_name
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Factor with id '{factor_id}' not found"
            )
        return result["factor"]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cloning factor {factor_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clone factor"
        )
