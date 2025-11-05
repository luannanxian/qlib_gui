"""
Import Task SQLAlchemy Model

Tracks file upload and data import operations with progress monitoring.
"""

import enum
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Integer, Enum, JSON, Text, Float, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseDBModel

if TYPE_CHECKING:
    from app.database.models.dataset import Dataset


class ImportStatus(str, enum.Enum):
    """Import task status types"""
    PENDING = "pending"  # Task created, waiting to start
    VALIDATING = "validating"  # Validating file format and content
    PARSING = "parsing"  # Parsing file data
    PROCESSING = "processing"  # Processing and transforming data
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Failed with errors
    CANCELLED = "cancelled"  # Cancelled by user


class ImportType(str, enum.Enum):
    """Import data types"""
    CSV = "csv"
    EXCEL = "excel"
    QLIB = "qlib"
    JSON = "json"


class ImportTask(BaseDBModel):
    """
    Import Task model for tracking data import operations

    Relationships:
    - Many-to-One with Dataset (many imports can create/update one dataset)
    """

    __tablename__ = "import_tasks"

    # Core fields
    task_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Human-readable task name"
    )

    import_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Import file type (csv, excel, qlib, json)"
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
        comment="Import task status"
    )

    # File information
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Original uploaded filename"
    )

    file_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Server file path where uploaded file is stored"
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="File size in bytes"
    )

    # Progress tracking
    total_rows: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total rows to process"
    )

    processed_rows: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of rows processed"
    )

    progress_percentage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Progress percentage (0-100)"
    )

    # Error tracking
    error_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of errors encountered"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if task failed"
    )

    # Validation and parsing results
    validation_errors: Mapped[Optional[str]] = mapped_column(
        JSON,
        nullable=True,
        comment="List of validation errors (JSON array)"
    )

    parsing_metadata: Mapped[Optional[str]] = mapped_column(
        JSON,
        nullable=True,
        comment="Parsing metadata (columns detected, data types, etc.)"
    )

    # Processing configuration
    import_config: Mapped[Optional[str]] = mapped_column(
        JSON,
        nullable=True,
        comment="Import configuration (delimiter, encoding, skip rows, etc.)"
    )

    # User tracking
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="User who initiated the import (optional for now)"
    )

    # Foreign key to created/updated dataset
    dataset_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="ID of dataset created or updated by this import"
    )

    # Relationships
    dataset: Mapped[Optional["Dataset"]] = relationship(
        "Dataset",
        foreign_keys=[dataset_id],
        lazy="selectin"
    )

    # Table constraints and indexes
    __table_args__ = (
        # Composite indexes for common query patterns
        Index("ix_import_status_created", "status", "created_at"),
        Index("ix_import_user_status", "user_id", "status"),
        Index("ix_import_type_status", "import_type", "status"),
        # Optimized indexes for soft-delete and filtering queries
        Index("ix_import_deleted_status_created", "is_deleted", "status", "created_at"),  # For get_active_tasks()
        Index("ix_import_dataset_deleted_created", "dataset_id", "is_deleted", "created_at"),  # For get_by_dataset()
        Index("ix_import_user_deleted_created", "user_id", "is_deleted", "created_at"),  # For get_by_user()
        {
            "comment": "Import task tracking table",
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4"
        }
    )

    def __repr__(self) -> str:
        return (
            f"<ImportTask(id={self.id}, name={self.task_name}, "
            f"status={self.status}, progress={self.progress_percentage}%)>"
        )

    def update_progress(self, processed: int, total: int):
        """
        Update task progress

        Args:
            processed: Number of rows processed
            total: Total rows to process
        """
        self.processed_rows = processed
        self.total_rows = total
        self.progress_percentage = (processed / total * 100) if total > 0 else 0.0
