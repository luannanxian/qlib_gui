"""
FactorValidationResultRepository - Repository for FactorValidationResult model

Manages factor validation results including IC analysis, backtesting metrics,
and performance evaluations.
"""

from typing import List, Optional
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repositories.base import BaseRepository
from app.database.models.indicator import FactorValidationResult, ValidationStatus, ValidationType


class FactorValidationResultRepository(BaseRepository[FactorValidationResult]):
    """
    Repository for FactorValidationResult operations.

    Provides specialized methods for:
    - Factor validation history
    - Validation type filtering
    - Latest validation results
    - Status tracking
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with FactorValidationResult model"""
        super().__init__(FactorValidationResult, session)

    async def get_by_factor(
        self,
        factor_id: str,
        validation_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[FactorValidationResult]:
        """
        Get all validation results for a factor

        Args:
            factor_id: Custom factor ID
            validation_type: Filter by validation type
            skip: Skip records
            limit: Limit records

        Returns:
            List of validation results
        """
        conditions = [
            self.model.factor_id == factor_id,
            self.model.is_deleted == False
        ]

        if validation_type:
            conditions.append(self.model.validation_type == validation_type)

        stmt = select(self.model).where(and_(*conditions)).order_by(
            desc(self.model.created_at)
        ).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_by_factor(
        self,
        factor_id: str,
        validation_type: Optional[str] = None
    ) -> Optional[FactorValidationResult]:
        """
        Get the latest validation result for a factor

        Args:
            factor_id: Custom factor ID
            validation_type: Filter by validation type

        Returns:
            Latest validation result or None
        """
        results = await self.get_by_factor(
            factor_id=factor_id,
            validation_type=validation_type,
            skip=0,
            limit=1
        )
        return results[0] if results else None

    async def get_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[FactorValidationResult]:
        """
        Get validation results by status

        Args:
            status: Validation status
            skip: Skip records
            limit: Limit records

        Returns:
            List of validation results
        """
        stmt = select(self.model).where(
            and_(
                self.model.status == status,
                self.model.is_deleted == False
            )
        ).order_by(
            desc(self.model.created_at)
        ).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_status(
        self,
        validation_id: str,
        status: str
    ) -> Optional[FactorValidationResult]:
        """
        Update validation status

        Args:
            validation_id: Validation result ID
            status: New status

        Returns:
            Updated validation result or None
        """
        validation = await self.get(validation_id)
        if not validation:
            return None

        validation.status = status
        await self.session.commit()
        await self.session.refresh(validation)
        return validation
