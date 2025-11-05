"""
Dataset Repository

This module provides repository pattern implementation for Dataset model
with custom query methods specific to dataset operations.
"""

from typing import List, Optional

from loguru import logger
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.dataset import Dataset, DataSource, DatasetStatus
from app.database.repositories.base import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    """
    Repository for Dataset model with specialized query methods.

    Extends BaseRepository with dataset-specific operations such as:
    - Search by name
    - Filter by source
    - Filter by status
    - Get datasets with chart counts
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize dataset repository.

        Args:
            session: Async database session
        """
        super().__init__(Dataset, session)

    async def get_by_name(
        self,
        name: str,
        include_deleted: bool = False
    ) -> Optional[Dataset]:
        """
        Get a dataset by exact name.

        Args:
            name: Dataset name
            include_deleted: Whether to include soft-deleted records

        Returns:
            Dataset instance or None if not found

        Example:
            dataset = await repo.get_by_name("Stock Data 2024")
        """
        stmt = select(Dataset).where(Dataset.name == name)

        if not include_deleted:
            stmt = stmt.where(Dataset.is_deleted == False)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_source(
        self,
        source: DataSource | str,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[Dataset]:
        """
        Get datasets by data source.

        Args:
            source: Data source type (local, qlib, thirdparty)
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of Dataset instances

        Example:
            datasets = await repo.get_by_source("local", limit=20)
        """
        # Convert enum to string if needed
        source_str = source.value if isinstance(source, DataSource) else source

        stmt = select(Dataset).where(Dataset.source == source_str)

        if not include_deleted:
            stmt = stmt.where(Dataset.is_deleted == False)

        stmt = stmt.order_by(Dataset.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_status(
        self,
        status: DatasetStatus | str,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[Dataset]:
        """
        Get datasets by validation status.

        Args:
            status: Dataset status (valid, invalid, pending)
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of Dataset instances

        Example:
            valid_datasets = await repo.get_by_status("valid")
        """
        # Convert enum to string if needed
        status_str = status.value if isinstance(status, DatasetStatus) else status

        stmt = select(Dataset).where(Dataset.status == status_str)

        if not include_deleted:
            stmt = stmt.where(Dataset.is_deleted == False)

        stmt = stmt.order_by(Dataset.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_by_name(
        self,
        search_term: str,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[Dataset]:
        """
        Search datasets by name (case-insensitive partial match).

        Args:
            search_term: Search term to match against dataset names
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of Dataset instances matching the search term

        Example:
            results = await repo.search_by_name("stock", limit=10)
        """
        stmt = select(Dataset).where(
            Dataset.name.ilike(f"%{search_term}%")
        )

        if not include_deleted:
            stmt = stmt.where(Dataset.is_deleted == False)

        stmt = stmt.order_by(Dataset.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_filters(
        self,
        source: Optional[DataSource | str] = None,
        status: Optional[DatasetStatus | str] = None,
        search_term: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[Dataset]:
        """
        Get datasets with multiple filters combined.

        Args:
            source: Optional data source filter
            status: Optional status filter
            search_term: Optional name search term
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records

        Returns:
            List of Dataset instances matching all filters

        Example:
            datasets = await repo.get_with_filters(
                source="local",
                status="valid",
                search_term="2024"
            )
        """
        stmt = select(Dataset)

        # Apply filters
        if source:
            source_str = source.value if isinstance(source, DataSource) else source
            stmt = stmt.where(Dataset.source == source_str)

        if status:
            status_str = status.value if isinstance(status, DatasetStatus) else status
            stmt = stmt.where(Dataset.status == status_str)

        if search_term:
            stmt = stmt.where(Dataset.name.ilike(f"%{search_term}%"))

        if not include_deleted:
            stmt = stmt.where(Dataset.is_deleted == False)

        stmt = stmt.order_by(Dataset.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_source(
        self,
        source: DataSource | str,
        include_deleted: bool = False
    ) -> int:
        """
        Count datasets by source.

        Args:
            source: Data source type
            include_deleted: Whether to include soft-deleted records

        Returns:
            Number of datasets for the given source

        Example:
            count = await repo.count_by_source("local")
        """
        source_str = source.value if isinstance(source, DataSource) else source
        return await self.count(include_deleted=include_deleted, source=source_str)

    async def count_by_status(
        self,
        status: DatasetStatus | str,
        include_deleted: bool = False
    ) -> int:
        """
        Count datasets by status.

        Args:
            status: Dataset status
            include_deleted: Whether to include soft-deleted records

        Returns:
            Number of datasets with the given status

        Example:
            pending_count = await repo.count_by_status("pending")
        """
        status_str = status.value if isinstance(status, DatasetStatus) else status
        return await self.count(include_deleted=include_deleted, status=status_str)

    async def get_statistics(self) -> dict:
        """
        Get dataset statistics (counts by source and status).

        Returns:
            Dictionary with statistics

        Example:
            stats = await repo.get_statistics()
            # Returns: {
            #     "total": 100,
            #     "by_source": {"local": 50, "qlib": 30, "thirdparty": 20},
            #     "by_status": {"valid": 80, "invalid": 10, "pending": 10}
            # }
        """
        # Total count
        total = await self.count()

        # Count by source
        by_source = {}
        for source in DataSource:
            by_source[source.value] = await self.count_by_source(source)

        # Count by status
        by_status = {}
        for status in DatasetStatus:
            by_status[status.value] = await self.count_by_status(status)

        stats = {
            "total": total,
            "by_source": by_source,
            "by_status": by_status,
        }

        logger.debug(f"Dataset statistics: {stats}")
        return stats
