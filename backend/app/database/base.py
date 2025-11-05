"""
SQLAlchemy Base Models and Mixins
"""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import DateTime, String, Boolean, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models"""

    # Use type_annotation_map for better type handling
    type_annotation_map = {
        str: String(255),
    }


class TimestampMixin:
    """Mixin for automatic timestamp tracking"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp (UTC)"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Record last update timestamp (UTC)"
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""

    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",  # MySQL uses 0 for false
        index=True,
        comment="Soft delete flag"
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Deletion timestamp (UTC)"
    )


class AuditMixin:
    """Mixin for audit trail (created_by, updated_by)"""

    created_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="User ID who created this record"
    )

    updated_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="User ID who last updated this record"
    )


class UUIDMixin:
    """Mixin for UUID primary key"""

    @declared_attr
    def id(cls) -> Mapped[str]:
        # Using String for compatibility with MySQL
        return mapped_column(
            String(36),
            primary_key=True,
            default=lambda: str(uuid4()),
            comment="Primary key (UUID)"
        )


class BaseDBModel(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin, AuditMixin):
    """
    Base model for all database entities with:
    - UUID primary key
    - Timestamps (created_at, updated_at)
    - Soft delete (is_deleted, deleted_at)
    - Audit trail (created_by, updated_by)
    """

    __abstract__ = True

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<{self.__class__.__name__}(id={self.id})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
