"""
Dataset SQLAlchemy Model
"""

import enum
from typing import Any, List, TYPE_CHECKING

from sqlalchemy import String, Integer, Enum, JSON, Index, CheckConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseDBModel

if TYPE_CHECKING:
    from app.database.models.chart import ChartConfig


class DataSource(str, enum.Enum):
    """Data source types"""
    LOCAL = "local"
    QLIB = "qlib"
    THIRDPARTY = "thirdparty"


class DatasetStatus(str, enum.Enum):
    """Dataset status types"""
    VALID = "valid"
    INVALID = "invalid"
    PENDING = "pending"


class Dataset(BaseDBModel):
    """
    Dataset model for managing uploaded and imported data

    Relationships:
    - One-to-Many with ChartConfig (one dataset can have multiple charts)
    """

    __tablename__ = "datasets"

    # Core fields
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Dataset name"
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Data source type"
    )

    file_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="File path or URI to dataset"
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
        comment="Dataset validation status"
    )

    row_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of rows in dataset"
    )

    # JSON fields for flexible storage
    columns: Mapped[str] = mapped_column(
        JSON,
        nullable=False,
        server_default="[]",
        comment="List of column names (JSON array)"
    )

    extra_metadata: Mapped[str] = mapped_column(
        "metadata",  # Column name in database
        JSON,
        nullable=False,
        server_default="{}",
        comment="Additional metadata (JSON object)"
    )

    # Relationships
    charts: Mapped[List["ChartConfig"]] = relationship(
        "ChartConfig",
        back_populates="dataset",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin"  # Eager loading for better async performance
    )

    # Table constraints and indexes
    __table_args__ = (
        CheckConstraint("row_count >= 0", name="check_row_count_non_negative"),
        # Composite indexes for common query patterns
        Index("ix_dataset_source_status", "source", "status"),
        Index("ix_dataset_status_created", "status", "created_at"),
        Index("ix_dataset_name_source", "name", "source"),  # For name + source lookups
        Index("ix_dataset_deleted_created", "is_deleted", "created_at"),  # For soft-delete queries
        Index("ix_dataset_deleted_updated", "is_deleted", "updated_at"),  # For recently updated queries
        # Single column indexes (some already defined with index=True in mapped_column)
        # Note: name, source, status already have individual indexes from mapped_column(index=True)
        {"comment": "Dataset storage table", "mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    )

    def __repr__(self) -> str:
        return f"<Dataset(id={self.id}, name={self.name}, source={self.source})>"
