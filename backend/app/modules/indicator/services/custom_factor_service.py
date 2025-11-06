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

            return {
                "factors": [self._to_dict(f) for f in factors],
                "total": len(factors),
                "skip": skip,
                "limit": limit
            }
        except Exception as e:
            logger.error(f"Error getting user factors: {e}")
            raise

    async def get_factor_detail(self, factor_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed factor information.

        Args:
            factor_id: Factor ID

        Returns:
            Factor details or None if not found
        """
        try:
            factor = await self.custom_factor_repo.get(factor_id)
            if not factor:
                return None

            return self._to_dict(factor)
        except Exception as e:
            logger.error(f"Error getting factor detail: {e}")
            raise

    async def publish_factor(
        self,
        factor_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Publish a draft factor (requires ownership).

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
                logger.warning(f"Unauthorized publish attempt for factor {factor_id} by user {user_id}")
                return None

            # Publish
            published = await self.custom_factor_repo.publish_factor(factor_id)
            if not published:
                return None

            return {
                "factor": self._to_dict(published),
                "message": "Factor published successfully"
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
        new_user_id: str,
        new_factor_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Clone a public factor to another user.

        Args:
            factor_id: Source factor ID
            new_user_id: New owner user ID
            new_factor_name: Optional new name

        Returns:
            Cloned factor or None if source not public
        """
        try:
            # Verify source is public
            source = await self.custom_factor_repo.get(factor_id)
            if not source or not source.is_public:
                logger.warning(f"Attempt to clone non-public factor {factor_id}")
                return None

            # Clone
            cloned = await self.custom_factor_repo.clone_factor(
                factor_id=factor_id,
                new_user_id=new_user_id,
                new_factor_name=new_factor_name
            )

            if not cloned:
                return None

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

            return {
                "factors": [self._to_dict(f) for f in public_factors],
                "total": len(public_factors),
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
