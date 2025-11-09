"""
Strategy API Endpoints

Provides REST API endpoints for strategy template and instance management.

Template Endpoints:
- POST /api/strategy-templates - Create template
- GET /api/strategy-templates - List templates with filters
- GET /api/strategy-templates/popular - Get popular templates
- GET /api/strategy-templates/{id} - Get template details
- PUT /api/strategy-templates/{id} - Update template
- DELETE /api/strategy-templates/{id} - Delete template
- POST /api/strategy-templates/{id}/rate - Add/update rating

Instance Endpoints:
- POST /api/strategies - Create strategy instance
- GET /api/strategies - List user's strategies
- GET /api/strategies/{id} - Get strategy details
- PUT /api/strategies/{id} - Update strategy
- DELETE /api/strategies/{id} - Soft delete strategy
- POST /api/strategies/{id}/copy - Duplicate strategy
- POST /api/strategies/{id}/snapshot - Save version snapshot
- GET /api/strategies/{id}/versions - Get version history
- POST /api/strategies/{id}/validate - Validate strategy logic
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import get_db
from app.database.models.strategy import StrategyCategory, StrategyStatus
from app.database.repositories.strategy_template import StrategyTemplateRepository
from app.database.repositories.strategy_instance import StrategyInstanceRepository
from app.database.repositories.template_rating import TemplateRatingRepository
from app.modules.strategy.services.template_service import TemplateService
from app.modules.strategy.services.instance_service import InstanceService
from app.modules.strategy.services.validation_service import ValidationService
from app.modules.strategy.schemas.strategy import (
    # Template schemas
    StrategyTemplateCreate,
    StrategyTemplateUpdate,
    StrategyTemplateResponse,
    StrategyTemplateListResponse,
    TemplateRatingCreate,
    TemplateRatingResponse,
    # Instance schemas
    StrategyCreateRequest,
    StrategyUpdateRequest,
    StrategyResponse,
    StrategyListResponse,
    StrategyVersionResponse,
    # Validation schemas
    StrategyValidationResponse,
    LogicFlow,
)

router = APIRouter(prefix="/api", tags=["strategies"])

# User ID placeholder for authentication
# TODO: Replace with actual authentication when implemented
MOCK_USER_ID = "test_user"


# ========================================
# Template Management Endpoints
# ========================================

@router.post(
    "/strategy-templates",
    response_model=StrategyTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create strategy template",
    description="Create a new strategy template (admin only)"
)
async def create_template(
    template: StrategyTemplateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new strategy template."""
    try:
        repo = StrategyTemplateRepository(db)

        # Convert Pydantic model to dict for repository
        template_data = template.model_dump()

        # Create template
        db_template = await repo.create(template_data, user_id=MOCK_USER_ID)
        await db.commit()
        await db.refresh(db_template)

        logger.info(f"Created template: {db_template.id}")
        return db_template

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating template: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )


@router.get(
    "/strategy-templates",
    response_model=StrategyTemplateListResponse,
    summary="List strategy templates",
    description="Get list of strategy templates with optional filters"
)
async def list_templates(
    category: Optional[StrategyCategory] = Query(None, description="Filter by category"),
    is_system_template: Optional[bool] = Query(None, description="Filter by system/custom"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum items to return"),
    db: AsyncSession = Depends(get_db)
):
    """List strategy templates with filtering and pagination."""
    try:
        repo = StrategyTemplateRepository(db)

        # Convert enum to string if provided
        category_str = category.value if category else None

        # Get templates
        templates = await repo.list_all(
            category=category_str,
            is_system_template=is_system_template,
            skip=skip,
            limit=limit
        )

        # Get total count
        total = await repo.count(
            category=category_str,
            is_system_template=is_system_template
        )

        return {
            "total": total,
            "items": templates,
            "skip": skip,
            "limit": limit
        }

    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list templates: {str(e)}"
        )


@router.get(
    "/strategy-templates/popular",
    response_model=List[StrategyTemplateResponse],
    summary="Get popular templates",
    description="Get top N popular templates sorted by usage count"
)
async def get_popular_templates(
    limit: int = Query(5, ge=1, le=20, description="Number of templates to return"),
    category: Optional[StrategyCategory] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db)
):
    """Get popular templates."""
    try:
        service = TemplateService(db)
        templates = await service.get_popular_templates(limit=limit, category=category)
        return templates

    except Exception as e:
        logger.error(f"Error getting popular templates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get popular templates: {str(e)}"
        )


@router.get(
    "/strategy-templates/{template_id}",
    response_model=StrategyTemplateResponse,
    summary="Get template details",
    description="Get detailed information about a specific template"
)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get template by ID."""
    try:
        repo = StrategyTemplateRepository(db)
        template = await repo.get(template_id)

        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template not found: {template_id}"
            )

        return template

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template: {str(e)}"
        )


@router.put(
    "/strategy-templates/{template_id}",
    response_model=StrategyTemplateResponse,
    summary="Update template",
    description="Update an existing template (admin only)"
)
async def update_template(
    template_id: str,
    template: StrategyTemplateUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update template."""
    try:
        repo = StrategyTemplateRepository(db)

        # Check if template exists
        existing = await repo.get(template_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template not found: {template_id}"
            )

        # Update template
        update_data = template.model_dump(exclude_unset=True)
        updated = await repo.update(template_id, update_data, user_id=MOCK_USER_ID)
        await db.commit()
        await db.refresh(updated)

        logger.info(f"Updated template: {template_id}")
        return updated

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update template: {str(e)}"
        )


@router.delete(
    "/strategy-templates/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete template",
    description="Delete a template (admin only)"
)
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete template."""
    try:
        repo = StrategyTemplateRepository(db)

        # Check if template exists
        existing = await repo.get(template_id)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template not found: {template_id}"
            )

        # Delete template
        await repo.delete(template_id, user_id=MOCK_USER_ID)
        await db.commit()

        logger.info(f"Deleted template: {template_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete template: {str(e)}"
        )


@router.post(
    "/strategy-templates/{template_id}/rate",
    response_model=TemplateRatingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Rate template",
    description="Add or update rating for a template"
)
async def rate_template(
    template_id: str,
    rating_data: TemplateRatingCreate,
    db: AsyncSession = Depends(get_db)
):
    """Add or update template rating."""
    try:
        service = TemplateService(db)

        # Add/update rating
        rating = await service.add_rating(
            template_id=template_id,
            user_id=MOCK_USER_ID,
            rating=rating_data.rating,
            comment=rating_data.comment
        )
        await db.commit()
        await db.refresh(rating)

        logger.info(f"Rated template {template_id}: {rating_data.rating}/5")
        return rating

    except ValueError as e:
        await db.rollback()
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error rating template {template_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rate template: {str(e)}"
        )


# ========================================
# Strategy Instance Endpoints
# ========================================

@router.post(
    "/strategies",
    response_model=StrategyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create strategy",
    description="Create a strategy instance from template or custom"
)
async def create_strategy(
    strategy: StrategyCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create strategy instance."""
    try:
        service = InstanceService(db)

        # Create from template or custom
        if strategy.template_id:
            # Create from template
            instance = await service.create_from_template(
                template_id=strategy.template_id,
                user_id=MOCK_USER_ID,
                name=strategy.name,
                parameters=strategy.parameters
            )
        else:
            # Create custom strategy
            instance = await service.create_custom(
                user_id=MOCK_USER_ID,
                name=strategy.name,
                logic_flow=strategy.logic_flow.model_dump(),
                parameters=strategy.parameters
            )

        await db.commit()
        await db.refresh(instance)

        logger.info(f"Created strategy: {instance.id}")
        return instance

    except ValueError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating strategy: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create strategy: {str(e)}"
        )


@router.get(
    "/strategies",
    response_model=StrategyListResponse,
    summary="List strategies",
    description="Get list of user's strategies with optional filters"
)
async def list_strategies(
    status_filter: Optional[StrategyStatus] = Query(None, alias="status", description="Filter by status"),
    template_id: Optional[str] = Query(None, description="Filter by template"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum items to return"),
    db: AsyncSession = Depends(get_db)
):
    """List user's strategies."""
    try:
        repo = StrategyInstanceRepository(db)

        # Convert enum to string if provided
        status_str = status_filter.value if status_filter else None

        # Get strategies for user
        strategies = await repo.list_by_user(
            user_id=MOCK_USER_ID,
            status=status_str,
            template_id=template_id,
            skip=skip,
            limit=limit
        )

        # Get total count
        total = await repo.count_by_user(
            user_id=MOCK_USER_ID,
            status=status_str,
            template_id=template_id
        )

        return {
            "total": total,
            "items": strategies,
            "skip": skip,
            "limit": limit
        }

    except Exception as e:
        logger.error(f"Error listing strategies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list strategies: {str(e)}"
        )


@router.get(
    "/strategies/{strategy_id}",
    response_model=StrategyResponse,
    summary="Get strategy details",
    description="Get detailed information about a specific strategy"
)
async def get_strategy(
    strategy_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get strategy by ID."""
    try:
        repo = StrategyInstanceRepository(db)
        strategy = await repo.get(strategy_id)

        if strategy is None or strategy.user_id != MOCK_USER_ID:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy not found: {strategy_id}"
            )

        return strategy

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting strategy {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get strategy: {str(e)}"
        )


@router.put(
    "/strategies/{strategy_id}",
    response_model=StrategyResponse,
    summary="Update strategy",
    description="Update strategy logic and parameters"
)
async def update_strategy(
    strategy_id: str,
    strategy: StrategyUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update strategy."""
    try:
        repo = StrategyInstanceRepository(db)

        # Check if strategy exists and belongs to user
        existing = await repo.get(strategy_id)
        if existing is None or existing.user_id != MOCK_USER_ID:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy not found: {strategy_id}"
            )

        # Update strategy
        update_data = strategy.model_dump(exclude_unset=True)
        updated = await repo.update(strategy_id, update_data, user_id=MOCK_USER_ID)
        await db.commit()
        await db.refresh(updated)

        logger.info(f"Updated strategy: {strategy_id}")
        return updated

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating strategy {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update strategy: {str(e)}"
        )


@router.delete(
    "/strategies/{strategy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete strategy",
    description="Soft delete a strategy"
)
async def delete_strategy(
    strategy_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Soft delete strategy."""
    try:
        repo = StrategyInstanceRepository(db)

        # Check if strategy exists and belongs to user
        existing = await repo.get(strategy_id)
        if existing is None or existing.user_id != MOCK_USER_ID:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy not found: {strategy_id}"
            )

        # Delete strategy
        await repo.delete(strategy_id, user_id=MOCK_USER_ID)
        await db.commit()

        logger.info(f"Deleted strategy: {strategy_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting strategy {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete strategy: {str(e)}"
        )


@router.post(
    "/strategies/{strategy_id}/copy",
    response_model=StrategyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Copy strategy",
    description="Duplicate a strategy with a new name"
)
async def copy_strategy(
    strategy_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Duplicate strategy."""
    try:
        service = InstanceService(db)

        # Get new name from request
        new_name = data.get("name")
        if not new_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name is required for copying strategy"
            )

        # Duplicate strategy
        duplicate = await service.duplicate_strategy(
            strategy_id=strategy_id,
            user_id=MOCK_USER_ID,
            new_name=new_name
        )
        await db.commit()
        await db.refresh(duplicate)

        logger.info(f"Copied strategy {strategy_id} as {duplicate.id}")
        return duplicate

    except ValueError as e:
        await db.rollback()
        if "not found" in str(e).lower() or "access denied" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error copying strategy {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to copy strategy: {str(e)}"
        )


@router.post(
    "/strategies/{strategy_id}/snapshot",
    response_model=StrategyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create snapshot",
    description="Save a version snapshot (max 5 snapshots)"
)
async def create_snapshot(
    strategy_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Create version snapshot."""
    try:
        service = InstanceService(db)

        # Create snapshot
        snapshot = await service.save_snapshot(
            strategy_id=strategy_id,
            user_id=MOCK_USER_ID
        )
        await db.commit()
        await db.refresh(snapshot)

        logger.info(f"Created snapshot for strategy {strategy_id}: version {snapshot.version}")
        return snapshot

    except ValueError as e:
        await db.rollback()
        if "not found" in str(e).lower() or "access denied" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating snapshot for {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create snapshot: {str(e)}"
        )


@router.get(
    "/strategies/{strategy_id}/versions",
    response_model=List[StrategyVersionResponse],
    summary="Get version history",
    description="Get all version snapshots for a strategy"
)
async def get_versions(
    strategy_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get version history."""
    try:
        service = InstanceService(db)

        # Get versions
        versions = await service.get_versions(
            strategy_id=strategy_id,
            user_id=MOCK_USER_ID
        )

        return versions

    except ValueError as e:
        if "not found" in str(e).lower() or "access denied" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting versions for {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get versions: {str(e)}"
        )


@router.post(
    "/strategies/{strategy_id}/validate",
    response_model=StrategyValidationResponse,
    summary="Validate strategy",
    description="Validate strategy logic and configuration"
)
async def validate_strategy(
    strategy_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Validate strategy logic."""
    try:
        repo = StrategyInstanceRepository(db)

        # Get strategy
        strategy = await repo.get(strategy_id)
        if strategy is None or strategy.user_id != MOCK_USER_ID:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Strategy not found: {strategy_id}"
            )

        # Validate - convert dict to LogicFlow object
        service = ValidationService()
        flow = LogicFlow.model_validate(strategy.logic_flow)
        result = service.validate_logic_flow(flow)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating strategy {strategy_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate strategy: {str(e)}"
        )
