"""
Data Preprocessing SQLAlchemy Models

Models for tracking preprocessing rules, templates, and task execution.
"""

import enum
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    String, Integer, Enum, JSON, Text, Float, Index,
    ForeignKey, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import BaseDBModel

if TYPE_CHECKING:
    from app.database.models.dataset import Dataset


# ==================== Enums ====================

class MissingValueMethod(str, enum.Enum):
    """Missing value handling methods"""
    DELETE_ROWS = "delete_rows"  # Delete rows with missing values
    MEAN_FILL = "mean_fill"  # Fill with column mean
    MEDIAN_FILL = "median_fill"  # Fill with column median
    FORWARD_FILL = "forward_fill"  # Forward fill (use previous value)
    BACKWARD_FILL = "backward_fill"  # Backward fill (use next value)
    CONSTANT_FILL = "constant_fill"  # Fill with constant value
    INTERPOLATE = "interpolate"  # Linear interpolation


class OutlierDetectionMethod(str, enum.Enum):
    """Outlier detection methods"""
    STANDARD_DEVIATION = "std_dev"  # Standard deviation (z-score)
    QUANTILE = "quantile"  # Quantile/IQR method
    ISOLATION_FOREST = "isolation_forest"  # Isolation forest algorithm
    MAD = "mad"  # Median Absolute Deviation


class OutlierHandlingStrategy(str, enum.Enum):
    """Outlier handling strategies"""
    DELETE = "delete"  # Delete outlier rows
    CAP = "cap"  # Cap to threshold (winsorization)
    REPLACE_MEAN = "replace_mean"  # Replace with mean
    REPLACE_MEDIAN = "replace_median"  # Replace with median
    KEEP = "keep"  # Keep but flag for reference


class TransformationType(str, enum.Enum):
    """Data transformation types"""
    NORMALIZE = "normalize"  # Min-Max normalization (0-1)
    STANDARDIZE = "standardize"  # Z-score standardization
    LOG_TRANSFORM = "log_transform"  # Logarithmic transformation
    SQRT_TRANSFORM = "sqrt_transform"  # Square root transformation
    BOX_COX = "box_cox"  # Box-Cox transformation
    TYPE_CONVERSION = "type_conversion"  # Data type conversion
    ROUND = "round"  # Round to specified decimals


class FilterOperator(str, enum.Enum):
    """Filter operators for data filtering"""
    EQUALS = "eq"  # Equal to
    NOT_EQUALS = "ne"  # Not equal to
    GREATER_THAN = "gt"  # Greater than
    GREATER_EQUAL = "ge"  # Greater than or equal
    LESS_THAN = "lt"  # Less than
    LESS_EQUAL = "le"  # Less than or equal
    IN = "in"  # In list
    NOT_IN = "not_in"  # Not in list
    CONTAINS = "contains"  # String contains
    STARTS_WITH = "starts_with"  # String starts with
    ENDS_WITH = "ends_with"  # String ends with
    IS_NULL = "is_null"  # Is null
    NOT_NULL = "not_null"  # Is not null
    BETWEEN = "between"  # Between two values


class PreprocessingRuleType(str, enum.Enum):
    """Preprocessing rule types"""
    MISSING_VALUE = "missing_value"
    OUTLIER_DETECTION = "outlier_detection"
    TRANSFORMATION = "transformation"
    FILTERING = "filtering"


class PreprocessingTaskStatus(str, enum.Enum):
    """Preprocessing task execution status"""
    PENDING = "pending"  # Task created, waiting to start
    RUNNING = "running"  # Task is currently running
    COMPLETED = "completed"  # Successfully completed
    FAILED = "failed"  # Failed with errors
    CANCELLED = "cancelled"  # Cancelled by user
    PARTIAL = "partial"  # Partially completed with warnings


# ==================== Models ====================

class DataPreprocessingRule(BaseDBModel):
    """
    Data Preprocessing Rule/Template Model

    Stores preprocessing configurations that can be reused.
    Users can save up to 20 templates per user.

    Relationships:
    - Many-to-One with Dataset (many rules can reference one dataset)
    - One-to-Many with DataPreprocessingTask (one rule can be used by many tasks)
    """

    __tablename__ = "preprocessing_rules"

    # Core fields
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Rule/template name"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Rule description"
    )

    rule_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of preprocessing rule (missing_value, outlier, transform, filter)"
    )

    # Template flag
    is_template: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
        server_default="0",
        index=True,
        comment="Whether this is a reusable template (vs one-time rule)"
    )

    # User ownership (for template quota enforcement)
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="User who owns this template (NULL for system templates)"
    )

    # Rule configuration (flexible JSON structure)
    # Structure depends on rule_type:
    # - missing_value: {"method": "mean_fill", "columns": ["price", "volume"], "fill_value": null}
    # - outlier: {"detection_method": "std_dev", "threshold": 3.0, "handling": "cap", "columns": ["price"]}
    # - transformation: {"type": "normalize", "columns": ["price"], "range": [0, 1]}
    # - filtering: {"conditions": [{"column": "volume", "operator": "gt", "value": 1000}], "logic": "AND"}
    configuration: Mapped[str] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Rule configuration (JSON object)"
    )

    # Metadata
    # {"affected_columns": ["price", "volume"], "expected_rows_affected": 100, "tags": ["finance", "cleaning"]}
    extra_metadata: Mapped[str] = mapped_column(
        "metadata",  # Column name in database
        JSON,
        nullable=False,
        server_default="{}",
        comment="Additional rule metadata (JSON object)"
    )

    # Reference dataset (optional - for validation or as example)
    dataset_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Reference dataset ID (optional)"
    )

    # Usage statistics
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of times this rule/template was used"
    )

    # Relationships
    dataset: Mapped[Optional["Dataset"]] = relationship(
        "Dataset",
        foreign_keys=[dataset_id],
        lazy="selectin"
    )

    tasks: Mapped[List["DataPreprocessingTask"]] = relationship(
        "DataPreprocessingTask",
        back_populates="rule",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin"
    )

    # Table constraints and indexes
    __table_args__ = (
        # Check constraints
        CheckConstraint("usage_count >= 0", name="check_usage_count_non_negative"),

        # Composite indexes for common query patterns
        Index("ix_preprocessing_rule_type_template", "rule_type", "is_template"),
        Index("ix_preprocessing_rule_user_template", "user_id", "is_template", "is_deleted"),
        Index("ix_preprocessing_rule_user_type", "user_id", "rule_type", "is_deleted"),
        Index("ix_preprocessing_rule_deleted_created", "is_deleted", "created_at"),
        Index("ix_preprocessing_rule_deleted_usage", "is_deleted", "usage_count"),

        # Unique constraint for template names per user
        UniqueConstraint(
            "user_id", "name", "is_deleted",
            name="uq_user_template_name",
            # Note: This allows same name for different users, but not for same user
        ),

        {
            "comment": "Data preprocessing rules and templates",
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4"
        }
    )

    def __repr__(self) -> str:
        return (
            f"<DataPreprocessingRule(id={self.id}, name={self.name}, "
            f"type={self.rule_type}, is_template={self.is_template})>"
        )


class DataPreprocessingTask(BaseDBModel):
    """
    Data Preprocessing Task Execution Model

    Tracks the execution of preprocessing operations on datasets.

    Relationships:
    - Many-to-One with Dataset (many tasks can process one dataset)
    - Many-to-One with DataPreprocessingRule (many tasks can use one rule)
    """

    __tablename__ = "preprocessing_tasks"

    # Core fields
    task_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Human-readable task name"
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
        comment="Task execution status"
    )

    # Foreign keys
    dataset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Source dataset ID to preprocess"
    )

    rule_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("preprocessing_rules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Preprocessing rule/template used (NULL for ad-hoc tasks)"
    )

    # Result dataset (preprocessed output)
    output_dataset_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Output dataset ID (preprocessed result)"
    )

    # Execution details
    # Configuration snapshot (copied from rule or provided directly)
    execution_config: Mapped[str] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Execution configuration snapshot (JSON object)"
    )

    # Progress tracking
    total_operations: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Total preprocessing operations to execute"
    )

    completed_operations: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of completed operations"
    )

    progress_percentage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        server_default="0.0",
        comment="Progress percentage (0-100)"
    )

    # Row statistics
    input_row_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of rows in input dataset"
    )

    output_row_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of rows in output dataset"
    )

    rows_affected: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of rows modified/removed by preprocessing"
    )

    # Error tracking
    error_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of errors encountered"
    )

    warning_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of warnings generated"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if task failed"
    )

    # Execution results and logs
    # {"operations_applied": [...], "statistics": {...}, "warnings": [...]}
    execution_results: Mapped[Optional[str]] = mapped_column(
        JSON,
        nullable=True,
        comment="Detailed execution results (JSON object)"
    )

    execution_logs: Mapped[Optional[str]] = mapped_column(
        JSON,
        nullable=True,
        comment="Execution logs and messages (JSON array)"
    )

    # Performance metrics
    execution_time_seconds: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="Task execution time in seconds"
    )

    # User tracking
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="User who initiated the task (optional for now)"
    )

    # Relationships
    dataset: Mapped["Dataset"] = relationship(
        "Dataset",
        foreign_keys=[dataset_id],
        lazy="selectin"
    )

    rule: Mapped[Optional["DataPreprocessingRule"]] = relationship(
        "DataPreprocessingRule",
        back_populates="tasks",
        foreign_keys=[rule_id],
        lazy="selectin"
    )

    output_dataset: Mapped[Optional["Dataset"]] = relationship(
        "Dataset",
        foreign_keys=[output_dataset_id],
        lazy="selectin"
    )

    # Table constraints and indexes
    __table_args__ = (
        # Check constraints
        CheckConstraint("total_operations >= 0", name="check_total_operations_non_negative"),
        CheckConstraint("completed_operations >= 0", name="check_completed_operations_non_negative"),
        CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100", name="check_progress_range"),
        CheckConstraint("input_row_count >= 0", name="check_input_rows_non_negative"),
        CheckConstraint("output_row_count >= 0", name="check_output_rows_non_negative"),
        CheckConstraint("rows_affected >= 0", name="check_affected_rows_non_negative"),
        CheckConstraint("error_count >= 0", name="check_error_count_non_negative"),
        CheckConstraint("warning_count >= 0", name="check_warning_count_non_negative"),

        # Composite indexes for common query patterns
        Index("ix_preprocessing_task_status_created", "status", "created_at"),
        Index("ix_preprocessing_task_user_status", "user_id", "status", "is_deleted"),
        Index("ix_preprocessing_task_dataset_status", "dataset_id", "status", "is_deleted"),
        Index("ix_preprocessing_task_rule_status", "rule_id", "status", "is_deleted"),
        Index("ix_preprocessing_task_deleted_created", "is_deleted", "created_at"),
        Index("ix_preprocessing_task_deleted_updated", "is_deleted", "updated_at"),

        {
            "comment": "Data preprocessing task execution tracking",
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4"
        }
    )

    def __repr__(self) -> str:
        return (
            f"<DataPreprocessingTask(id={self.id}, name={self.task_name}, "
            f"status={self.status}, progress={self.progress_percentage}%)>"
        )

    def update_progress(self, completed: int, total: int):
        """
        Update task progress

        Args:
            completed: Number of completed operations
            total: Total operations to execute
        """
        self.completed_operations = completed
        self.total_operations = total
        self.progress_percentage = (completed / total * 100) if total > 0 else 0.0
