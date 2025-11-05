"""
Base Repository Pattern

This module provides a generic base repository with common CRUD operations
for SQLAlchemy models with async support.
"""

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar, Type, List, Optional, Dict

from loguru import logger
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import BaseDBModel

# Generic type for models
ModelType = TypeVar("ModelType", bound=BaseDBModel)


class BaseRepository(Generic[ModelType]):
    """
    Generic base repository providing common CRUD operations.

    Features:
    - Create, Read, Update, Delete operations
    - Soft delete support
    - Pagination
    - Filtering and searching
    - Count and exists checks
    - Transaction management

    Type Parameters:
        ModelType: SQLAlchemy model class
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        """
        Initialize repository.

        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session

    async def create(
        self,
        obj_in: Dict[str, Any],
        commit: bool = True,
        user_id: Optional[str] = None
    ) -> ModelType:
        """
        Create a new record.

        Args:
            obj_in: Dictionary of model attributes
            commit: Whether to commit the transaction
            user_id: Optional user ID for audit trail

        Returns:
            Created model instance

        Example:
            dataset = await repo.create({
                "name": "My Dataset",
                "source": "local",
                "file_path": "/path/to/data.csv"
            })
        """
        # Add audit trail
        if user_id:
            obj_in["created_by"] = user_id

        db_obj = self.model(**obj_in)
        self.session.add(db_obj)

        # Always flush to get the ID even if not committing
        await self.session.flush()
        await self.session.refresh(db_obj)

        if commit:
            await self.session.commit()

        logger.debug(f"Created {self.model.__name__} with id={db_obj.id}")
        return db_obj

    async def get(
        self,
        id: str,
        include_deleted: bool = False
    ) -> Optional[ModelType]:
        """
        Get a record by ID.

        Args:
            id: Record ID
            include_deleted: Whether to include soft-deleted records

        Returns:
            Model instance or None if not found

        Example:
            dataset = await repo.get("uuid-123")
        """
        stmt = select(self.model).where(self.model.id == id)

        if not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False,
        order_by: Optional[str] = None,
        **filters
    ) -> List[ModelType]:
        """
        Get multiple records with pagination and filtering.

        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted records
            order_by: Column name to order by (prefix with - for descending)
            **filters: Additional filters as keyword arguments

        Returns:
            List of model instances

        Example:
            datasets = await repo.get_multi(
                skip=0,
                limit=10,
                source="local",
                order_by="-created_at"
            )
        """
        stmt = select(self.model)

        # Apply soft delete filter
        if not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)

        # Apply additional filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)

        # Apply ordering
        if order_by:
            if order_by.startswith("-"):
                order_column = order_by[1:]
                if hasattr(self.model, order_column):
                    stmt = stmt.order_by(getattr(self.model, order_column).desc())
            else:
                if hasattr(self.model, order_by):
                    stmt = stmt.order_by(getattr(self.model, order_by))
        else:
            # Default ordering by created_at descending
            stmt = stmt.order_by(self.model.created_at.desc())

        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        id: str,
        obj_in: Dict[str, Any],
        commit: bool = True,
        user_id: Optional[str] = None
    ) -> Optional[ModelType]:
        """
        Update a record by ID.

        Args:
            id: Record ID
            obj_in: Dictionary of attributes to update
            commit: Whether to commit the transaction
            user_id: Optional user ID for audit trail

        Returns:
            Updated model instance or None if not found

        Example:
            dataset = await repo.update(
                "uuid-123",
                {"status": "valid", "row_count": 1000}
            )
        """
        db_obj = await self.get(id)
        if db_obj is None:
            logger.warning(f"{self.model.__name__} not found: id={id}")
            return None

        # Update attributes
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        # Add audit trail
        if user_id:
            db_obj.updated_by = user_id

        # Always flush to persist changes to the session
        await self.session.flush()
        await self.session.refresh(db_obj)

        if commit:
            await self.session.commit()

        logger.debug(f"Updated {self.model.__name__} with id={id}")
        return db_obj

    async def delete(
        self,
        id: str,
        soft: bool = True,
        commit: bool = True,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Delete a record by ID.

        Args:
            id: Record ID
            soft: Whether to use soft delete (default) or hard delete
            commit: Whether to commit the transaction
            user_id: Optional user ID for audit trail

        Returns:
            True if deleted, False if not found

        Example:
            # Soft delete (default)
            success = await repo.delete("uuid-123")

            # Hard delete
            success = await repo.delete("uuid-123", soft=False)
        """
        db_obj = await self.get(id, include_deleted=soft)
        if db_obj is None:
            logger.warning(f"{self.model.__name__} not found: id={id}")
            return False

        if soft:
            # Soft delete: mark as deleted
            db_obj.is_deleted = True
            db_obj.deleted_at = datetime.now()  # Use local timezone
            if user_id:
                db_obj.updated_by = user_id
            # Flush to persist the soft delete
            await self.session.flush()
        else:
            # Hard delete: remove from database
            await self.session.delete(db_obj)
            # Flush to execute the delete
            await self.session.flush()

        if commit:
            await self.session.commit()

        logger.debug(f"{'Soft' if soft else 'Hard'} deleted {self.model.__name__} with id={id}")
        return True

    async def count(
        self,
        include_deleted: bool = False,
        **filters
    ) -> int:
        """
        Count records with optional filtering.

        Args:
            include_deleted: Whether to include soft-deleted records
            **filters: Additional filters as keyword arguments

        Returns:
            Number of matching records

        Example:
            total = await repo.count(source="local")
        """
        stmt = select(func.count()).select_from(self.model)

        # Apply soft delete filter
        if not include_deleted:
            stmt = stmt.where(self.model.is_deleted == False)

        # Apply additional filters
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)

        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists(
        self,
        id: str,
        include_deleted: bool = False
    ) -> bool:
        """
        Check if a record exists.

        Args:
            id: Record ID
            include_deleted: Whether to include soft-deleted records

        Returns:
            True if record exists, False otherwise

        Example:
            exists = await repo.exists("uuid-123")
        """
        obj = await self.get(id, include_deleted=include_deleted)
        return obj is not None

    async def bulk_create(
        self,
        objects: List[Dict[str, Any]],
        commit: bool = True,
        user_id: Optional[str] = None
    ) -> List[ModelType]:
        """
        Create multiple records in bulk.

        Args:
            objects: List of dictionaries with model attributes
            commit: Whether to commit the transaction
            user_id: Optional user ID for audit trail

        Returns:
            List of created model instances

        Example:
            datasets = await repo.bulk_create([
                {"name": "Dataset 1", "source": "local", "file_path": "/path1"},
                {"name": "Dataset 2", "source": "qlib", "file_path": "/path2"}
            ])
        """
        db_objects = []
        for obj_data in objects:
            if user_id:
                obj_data["created_by"] = user_id
            db_obj = self.model(**obj_data)
            db_objects.append(db_obj)

        self.session.add_all(db_objects)

        if commit:
            await self.session.commit()
            for db_obj in db_objects:
                await self.session.refresh(db_obj)

        logger.debug(f"Bulk created {len(db_objects)} {self.model.__name__} records")
        return db_objects

    async def restore(
        self,
        id: str,
        commit: bool = True,
        user_id: Optional[str] = None
    ) -> Optional[ModelType]:
        """
        Restore a soft-deleted record.

        Args:
            id: Record ID
            commit: Whether to commit the transaction
            user_id: Optional user ID for audit trail

        Returns:
            Restored model instance or None if not found

        Example:
            dataset = await repo.restore("uuid-123")
        """
        db_obj = await self.get(id, include_deleted=True)
        if db_obj is None or not db_obj.is_deleted:
            logger.warning(
                f"{self.model.__name__} not found or not deleted: id={id}"
            )
            return None

        db_obj.is_deleted = False
        db_obj.deleted_at = None
        if user_id:
            db_obj.updated_by = user_id

        if commit:
            await self.session.commit()
            await self.session.refresh(db_obj)

        logger.debug(f"Restored {self.model.__name__} with id={id}")
        return db_obj
