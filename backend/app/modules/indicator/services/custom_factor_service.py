"""
CustomFactorService - Business logic for custom factor operations

Provides high-level operations for managing user-defined custom factors.
"""

from typing import Dict, Any, List, Optional
from loguru import logger
from sqlalchemy.exc import IntegrityError

from app.database.repositories.custom_factor_repository import CustomFactorRepository
from app.database.models.indicator import FactorStatus
from app.modules.indicator.exceptions import ValidationError, AuthorizationError, ConflictError


class CustomFactorService:
    """
    Service for custom factor operations.

    Provides business logic for:
    - Factor CRUD with authorization
    - Publishing workflow (draft → published → public)
    - Factor cloning
    - Usage tracking
    - Public factor discovery
    """

    def __init__(self, custom_factor_repo: CustomFactorRepository):
        """
        Initialize service with repository.

        Args:
            custom_factor_repo: CustomFactorRepository instance
        """
        self.custom_factor_repo = custom_factor_repo

    async def create_factor(
        self,
        factor_data: Dict[str, Any],
        authenticated_user_id: str
    ) -> Dict[str, Any]:
        """
        Create a new custom factor with input validation.

        Args:
            factor_data: Factor creation data
            authenticated_user_id: ID of authenticated user (from auth context)

        Returns:
            Dict with created factor

        Raises:
            ValidationError: If required fields are missing or invalid
            ConflictError: If factor with same name already exists for user
        """
        try:
            # Validate required fields
            required_fields = ['factor_name', 'formula', 'formula_language']
            missing = [f for f in required_fields if f not in factor_data or not factor_data[f]]
            if missing:
                raise ValidationError(f"Missing required fields: {', '.join(missing)}")

            # Force use authenticated user ID (prevent authorization bypass)
            factor_data['user_id'] = authenticated_user_id

            # Set default values if not provided
            factor_data.setdefault('status', FactorStatus.DRAFT.value)
            factor_data.setdefault('is_public', False)

            # Validate formula language
            valid_languages = ['qlib_alpha', 'python', 'pandas']
            if factor_data['formula_language'] not in valid_languages:
                raise ValidationError(
                    f"Invalid formula_language. Must be one of: {', '.join(valid_languages)}"
                )

            factor = await self.custom_factor_repo.create(factor_data, commit=True)

            logger.info(
                f"Factor created successfully",
                extra={
                    "factor_id": factor.id,
                    "user_id": authenticated_user_id,
                    "factor_name": factor.factor_name
                }
            )

            return {
                "factor": self._to_dict(factor),
                "message": "Factor created successfully"
            }
        except ValidationError:
            raise
        except IntegrityError as e:
            logger.warning(f"Integrity violation creating factor: {e}")
            raise ConflictError(
                f"Factor with name '{factor_data.get('factor_name')}' already exists"
            ) from e
        except Exception as e:
            logger.exception(f"Unexpected error creating factor: {e}")
            raise

    async def get_user_factors(
        self,
        user_id: str,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get user's custom factors.

        Args:
            user_id: User ID
            status: Optional status filter
            skip: Skip records
            limit: Limit records

        Returns:
            Dict with factors list and total count
        """
        try:
            factors = await self.custom_factor_repo.get_user_factors(
                user_id=user_id,
                status=status,
                skip=skip,
                limit=limit
            )

            # Get total count from database
            total_count = await self.custom_factor_repo.count_user_factors(
                user_id=user_id,
                status=status
            )

            return {
                "factors": [self._to_dict(f) for f in factors],
                "total": total_count,
                "skip": skip,
                "limit": limit
            }
        except Exception as e:
            logger.error(f"Error getting user factors: {e}")
            raise

    async def get_factor_detail(
        self,
        factor_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed factor information with optional authorization check.

        Args:
            factor_id: Factor ID
            user_id: Optional user ID for authorization check.
                    If provided, only returns factor if user owns it or it's public.

        Returns:
            Dict with factor details or None if not found/unauthorized
        """
        try:
            factor = await self.custom_factor_repo.get(factor_id)
            if not factor:
                return None

            # If user_id provided, check authorization
            if user_id is not None:
                # User can access if: owns the factor OR factor is public
                if factor.user_id != user_id and not factor.is_public:
                    logger.warning(
                        f"Unauthorized access attempt for factor {factor_id} by user {user_id}"
                    )
                    return None

            return {
                "factor": self._to_dict(factor),
                "message": "Factor retrieved successfully"
            }
        except Exception as e:
            logger.error(f"Error getting factor detail: {e}")
            raise

    async def update_factor(
        self,
        factor_id: str,
        factor_data: Dict[str, Any],
        authenticated_user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Update a custom factor with authorization check.

        Args:
            factor_id: Factor ID to update
            factor_data: Dictionary of fields to update
            authenticated_user_id: ID of authenticated user (from auth context)

        Returns:
            Dict with updated factor or None if not found/unauthorized

        Raises:
            ValidationError: If update data is invalid
            AuthorizationError: If user doesn't own the factor
        """
        try:
            # Verify ownership
            factor = await self.custom_factor_repo.get(factor_id)
            if not factor:
                return None

            if factor.user_id != authenticated_user_id:
                logger.warning(
                    f"Unauthorized update attempt for factor {factor_id} by user {authenticated_user_id}"
                )
                raise AuthorizationError(
                    f"User {authenticated_user_id} is not authorized to update factor {factor_id}"
                )

            # Prevent changing user_id
            if 'user_id' in factor_data:
                del factor_data['user_id']

            # Validate formula_language if provided
            if 'formula_language' in factor_data:
                valid_languages = ['qlib_alpha', 'python', 'pandas']
                if factor_data['formula_language'] not in valid_languages:
                    raise ValidationError(
                        f"Invalid formula_language. Must be one of: {', '.join(valid_languages)}"
                    )

            # Update factor
            updated = await self.custom_factor_repo.update(factor_id, factor_data, commit=True)
            if not updated:
                return None

            logger.info(
                f"Factor updated successfully",
                extra={
                    "factor_id": factor_id,
                    "user_id": authenticated_user_id,
                    "updated_fields": list(factor_data.keys())
                }
            )

            return {
                "factor": self._to_dict(updated),
                "message": "Factor updated successfully"
            }
        except (ValidationError, AuthorizationError):
            raise
        except Exception as e:
            logger.error(f"Error updating factor {factor_id}: {e}")
            raise

    async def publish_factor(
        self,
        factor_id: str,
        user_id: str,
        is_public: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Publish a draft factor (requires ownership).

        Args:
            factor_id: Factor ID
            user_id: User ID requesting publish
            is_public: Whether to make the factor public upon publishing

        Returns:
            Dict with updated factor or None if unauthorized/not found
        """
        try:
            # Verify ownership
            factor = await self.custom_factor_repo.get(factor_id)
            if not factor or factor.user_id != user_id:
                logger.warning(f"Unauthorized publish attempt for factor {factor_id} by user {user_id}")
                return None

            # Publish
            published = await self.custom_factor_repo.publish_factor(factor_id)
            if not published:
                return None

            # Make public if requested
            if is_public:
                published = await self.custom_factor_repo.make_public(factor_id)
                if not published:
                    return None

            logger.info(
                f"Factor published successfully",
                extra={
                    "factor_id": factor_id,
                    "user_id": user_id,
                    "is_public": is_public
                }
            )

            return {
                "factor": self._to_dict(published),
                "message": f"Factor published successfully{' and made public' if is_public else ''}"
            }
        except Exception as e:
            logger.error(f"Error publishing factor: {e}")
            raise

    async def make_public(
        self,
        factor_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Make a published factor public (requires ownership).

        Args:
            factor_id: Factor ID
            user_id: User ID requesting publish

        Returns:
            Updated factor or None if unauthorized/not found
        """
        try:
            # Verify ownership
            factor = await self.custom_factor_repo.get(factor_id)
            if not factor or factor.user_id != user_id:
                logger.warning(f"Unauthorized make public attempt for factor {factor_id} by user {user_id}")
                return None

            # Make public
            public = await self.custom_factor_repo.make_public(factor_id)
            if not public:
                return None

            return {
                "factor": self._to_dict(public),
                "message": "Factor shared publicly"
            }
        except Exception as e:
            logger.error(f"Error making factor public: {e}")
            raise

    async def clone_factor(
        self,
        factor_id: str,
        authenticated_user_id: str,
        new_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Clone a public factor to the authenticated user.

        Args:
            factor_id: Source factor ID
            authenticated_user_id: User ID who is cloning (from auth context)
            new_name: Optional new name for cloned factor

        Returns:
            Dict with cloned factor or None if source not found/not public
        """
        try:
            # Verify source exists and is public
            source = await self.custom_factor_repo.get(factor_id)
            if not source:
                logger.warning(f"Attempt to clone non-existent factor {factor_id}")
                return None

            if not source.is_public:
                logger.warning(f"Attempt to clone non-public factor {factor_id}")
                return None

            # Clone to authenticated user
            cloned = await self.custom_factor_repo.clone_factor(
                factor_id=factor_id,
                new_user_id=authenticated_user_id,
                new_factor_name=new_name
            )

            if not cloned:
                return None

            logger.info(
                f"Factor cloned successfully",
                extra={
                    "source_factor_id": factor_id,
                    "cloned_factor_id": cloned.id,
                    "user_id": authenticated_user_id
                }
            )

            return {
                "factor": self._to_dict(cloned),
                "message": "Factor cloned successfully"
            }
        except Exception as e:
            logger.error(f"Error cloning factor: {e}")
            raise

    async def search_public_factors(
        self,
        keyword: str,
        skip: int = 0,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Search public factors by keyword.

        Args:
            keyword: Search keyword
            skip: Skip records
            limit: Limit records

        Returns:
            Dict with search results
        """
        try:
            factors = await self.custom_factor_repo.search_by_name(
                keyword=keyword,
                user_id=None,  # Search all public factors
                skip=skip,
                limit=limit
            )

            # Filter to only public factors
            public_factors = [f for f in factors if f.is_public and f.status == FactorStatus.PUBLISHED.value]

            # Get total count (note: this is not 100% accurate due to filtering in app layer)
            # TODO: Move filtering to repository layer for accurate pagination
            total_count = await self.custom_factor_repo.count_search_results(
                keyword=keyword,
                user_id=None
            )

            return {
                "factors": [self._to_dict(f) for f in public_factors],
                "total": total_count,  # Approximate - includes non-public matches
                "keyword": keyword
            }
        except Exception as e:
            logger.error(f"Error searching public factors: {e}")
            raise

    async def get_popular_factors(
        self,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get popular public factors.

        Args:
            limit: Number of factors to return

        Returns:
            Dict with popular factors
        """
        try:
            factors = await self.custom_factor_repo.get_popular_factors(limit=limit)

            return {
                "factors": [self._to_dict(f) for f in factors],
                "total": len(factors)
            }
        except Exception as e:
            logger.error(f"Error getting popular factors: {e}")
            raise

    async def delete_factor(
        self,
        factor_id: str,
        user_id: str,
        soft: bool = True
    ) -> bool:
        """
        Delete a factor (requires ownership).

        Args:
            factor_id: Factor ID
            user_id: User ID requesting deletion
            soft: Soft delete flag

        Returns:
            Success status
        """
        try:
            # Verify ownership
            factor = await self.custom_factor_repo.get(factor_id)
            if not factor or factor.user_id != user_id:
                logger.warning(f"Unauthorized delete attempt for factor {factor_id} by user {user_id}")
                return False

            # Delete
            return await self.custom_factor_repo.delete(factor_id, soft=soft)
        except Exception as e:
            logger.error(f"Error deleting factor: {e}")
            return False

    def _to_dict(self, factor) -> Dict[str, Any]:
        """
        Convert factor model to dictionary.

        Args:
            factor: CustomFactor model instance

        Returns:
            Dictionary representation
        """
        return {
            "id": factor.id,
            "factor_name": factor.factor_name,
            "user_id": factor.user_id,
            "base_indicator_id": factor.base_indicator_id,
            "formula": factor.formula,
            "formula_language": factor.formula_language,
            "description": factor.description,
            "status": factor.status,
            "is_public": factor.is_public,
            "published_at": factor.published_at.isoformat() if factor.published_at else None,
            "shared_at": factor.shared_at.isoformat() if factor.shared_at else None,
            "usage_count": factor.usage_count,
            "clone_count": factor.clone_count,
            "cloned_from_id": factor.cloned_from_id,
            "created_at": factor.created_at.isoformat() if factor.created_at else None,
            "updated_at": factor.updated_at.isoformat() if factor.updated_at else None
        }
