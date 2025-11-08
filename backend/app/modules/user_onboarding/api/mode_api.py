"""
Mode Management API Endpoints

Provides endpoints for user mode management and preferences with database persistence.
"""

from fastapi import APIRouter, HTTPException, status, Depends

from app.modules.common.schemas.response import APIResponse, success_response
from app.modules.user_onboarding.schemas.mode_schemas import (
    ModeUpdateRequest,
    ModeResponse,
    PreferencesUpdateRequest,
    PreferencesResponse
)
from app.modules.user_onboarding.api.dependencies import (
    get_user_prefs_repo,
    get_current_user_id,
    set_request_correlation_id
)
from app.database.repositories.user_preferences import UserPreferencesRepository
from app.modules.common.logging import get_logger, AuditLogger, AuditEventType, AuditSeverity
from app.modules.common.logging.decorators import log_async_execution

# Initialize logger and audit logger
logger = get_logger(__name__)
audit_logger = AuditLogger()

router = APIRouter()


@router.get("/mode", response_model=APIResponse[ModeResponse])
@log_async_execution(level="INFO")
async def get_current_mode(
    user_id: str = Depends(get_current_user_id),
    repo: UserPreferencesRepository = Depends(get_user_prefs_repo),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Get current user mode.

    Args:
        user_id: User ID from authentication
        repo: UserPreferencesRepository instance
        correlation_id: Request correlation ID

    Returns:
        ModeResponse with current mode

    Raises:
        500: If database operation fails
    """
    try:
        # Get or create user preferences
        prefs, created = await repo.get_or_create(user_id)

        if created:
            logger.info(f"Created default preferences for user: {user_id}")

        mode_response = ModeResponse(
            user_id=prefs.user_id,
            mode=prefs.mode,
            updated_at=prefs.updated_at
        )

        return success_response(mode_response)

    except Exception as e:
        logger.error(f"Error getting mode for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user mode"
        )


@router.post("/mode", response_model=APIResponse[ModeResponse])
@log_async_execution(level="INFO")
async def update_mode(
    request: ModeUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    repo: UserPreferencesRepository = Depends(get_user_prefs_repo),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Update user mode.

    Args:
        request: Mode update request
        user_id: User ID from authentication
        repo: UserPreferencesRepository instance
        correlation_id: Request correlation ID

    Returns:
        ModeResponse with updated mode

    Raises:
        500: If database operation fails
    """
    try:
        # Get or create user preferences
        prefs, created = await repo.get_or_create(user_id)

        old_mode = prefs.mode

        # Update mode using repository method
        updated_prefs = await repo.update_mode(
            user_id=user_id,
            mode=request.mode,
            commit=True
        )

        if updated_prefs is None:
            logger.error(f"Failed to update mode for user {user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user mode"
            )

        # Audit log for mode change
        audit_logger.log_event(
            event_type=AuditEventType.DATA_UPDATED,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            resource_type="user_mode",
            resource_id=user_id,
            action="update_mode",
            details={
                "old_mode": old_mode,
                "new_mode": request.mode,
                "correlation_id": correlation_id
            }
        )

        logger.info(f"User {user_id} switched mode from {old_mode} to {request.mode}")

        mode_response = ModeResponse(
            user_id=updated_prefs.user_id,
            mode=updated_prefs.mode,
            updated_at=updated_prefs.updated_at
        )

        return success_response(mode_response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating mode for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user mode"
        )


@router.get("/preferences", response_model=APIResponse[PreferencesResponse])
@log_async_execution(level="INFO")
async def get_preferences(
    user_id: str = Depends(get_current_user_id),
    repo: UserPreferencesRepository = Depends(get_user_prefs_repo),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Get user preferences.

    Args:
        user_id: User ID from authentication
        repo: UserPreferencesRepository instance
        correlation_id: Request correlation ID

    Returns:
        PreferencesResponse with user preferences

    Raises:
        500: If database operation fails
    """
    try:
        # Get or create user preferences
        prefs, created = await repo.get_or_create(user_id)

        if created:
            logger.info(f"Created default preferences for user: {user_id}")

        prefs_response = PreferencesResponse(
            user_id=prefs.user_id,
            mode=prefs.mode,
            completed_guides=prefs.completed_guides or [],
            show_tooltips=prefs.show_tooltips,
            language=prefs.language,
            created_at=prefs.created_at,
            updated_at=prefs.updated_at
        )

        return success_response(prefs_response)

    except Exception as e:
        logger.error(f"Error getting preferences for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user preferences"
        )


@router.put("/preferences", response_model=APIResponse[PreferencesResponse])
@log_async_execution(level="INFO")
async def update_preferences(
    request: PreferencesUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    repo: UserPreferencesRepository = Depends(get_user_prefs_repo),
    correlation_id: str = Depends(set_request_correlation_id)
):
    """
    Update user preferences (supports partial updates).

    Args:
        request: Preferences update request
        user_id: User ID from authentication
        repo: UserPreferencesRepository instance
        correlation_id: Request correlation ID

    Returns:
        PreferencesResponse with updated preferences

    Raises:
        500: If database operation fails
    """
    try:
        # Get or create user preferences
        prefs, created = await repo.get_or_create(user_id)

        # Track what changed for audit log
        changes = {}

        # Update language if provided
        if request.language is not None and request.language != prefs.language:
            changes["language"] = {"old": prefs.language, "new": request.language}
            prefs = await repo.update_language(user_id, request.language, commit=False)

        # Update tooltips if provided
        if request.show_tooltips is not None and request.show_tooltips != prefs.show_tooltips:
            changes["show_tooltips"] = {"old": prefs.show_tooltips, "new": request.show_tooltips}
            # Manually update since we don't have a specific method for this
            prefs.show_tooltips = request.show_tooltips

        # Update completed guides if provided
        if request.completed_guides is not None:
            old_guides = prefs.completed_guides or []
            if set(request.completed_guides) != set(old_guides):
                changes["completed_guides"] = {
                    "old": old_guides,
                    "new": request.completed_guides
                }
                prefs.completed_guides = request.completed_guides

        # Commit all changes
        if changes:
            await repo.session.commit()
            await repo.session.refresh(prefs)

            # Audit log for preference changes
            audit_logger.log_event(
                event_type=AuditEventType.DATA_UPDATED,
                severity=AuditSeverity.INFO,
                user_id=user_id,
                resource_type="user_preferences",
                resource_id=user_id,
                action="update_preferences",
                details={
                    "changes": changes,
                    "correlation_id": correlation_id
                }
            )

            logger.info(f"Updated preferences for user {user_id}: {list(changes.keys())}")

        prefs_response = PreferencesResponse(
            user_id=prefs.user_id,
            mode=prefs.mode,
            completed_guides=prefs.completed_guides or [],
            show_tooltips=prefs.show_tooltips,
            language=prefs.language,
            created_at=prefs.created_at,
            updated_at=prefs.updated_at
        )

        return success_response(prefs_response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user preferences"
        )
