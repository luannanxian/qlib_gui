"""
Strategy Builder Extension Models

This module extends the Strategy system with:
- NodeTemplate: Reusable node templates for logic flow builder
- QuickTest: Quick backtest execution and results
- CodeGeneration: Logic flow to Python code generation history
- BuilderSession: User session management for draft auto-save
"""

import enum
from datetime import datetime
from typing import List, TYPE_CHECKING, Optional

from sqlalchemy import String, Integer, Enum, JSON, Index, CheckConstraint, Text, Boolean, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime

from app.database.base import BaseDBModel

if TYPE_CHECKING:
    from app.database.models.strategy import StrategyInstance


# Enums for Strategy Builder System
class NodeTypeCategory(str, enum.Enum):
    """Node template categories"""
    INDICATOR = "INDICATOR"
    CONDITION = "CONDITION"
    SIGNAL = "SIGNAL"
    POSITION = "POSITION"
    STOP_LOSS = "STOP_LOSS"
    STOP_PROFIT = "STOP_PROFIT"
    RISK_MANAGEMENT = "RISK_MANAGEMENT"
    CUSTOM = "CUSTOM"


class QuickTestStatus(str, enum.Enum):
    """Quick test execution status"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ValidationStatus(str, enum.Enum):
    """Code validation status"""
    PENDING = "PENDING"
    VALID = "VALID"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    SECURITY_ERROR = "SECURITY_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"


class SessionType(str, enum.Enum):
    """Builder session types"""
    DRAFT = "DRAFT"
    AUTOSAVE = "AUTOSAVE"
    COLLABORATIVE = "COLLABORATIVE"


class NodeTemplate(BaseDBModel):
    """
    Node Template model for reusable logic flow nodes

    Stores predefined and user-defined node templates with:
    - Parameter schema definitions
    - Input/output port configurations
    - Validation rules and constraints
    - Category and metadata

    Relationships:
    - Referenced by StrategyTemplate and StrategyInstance logic_flow JSON
    """

    __tablename__ = "node_templates"

    # Core fields
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Node template name"
    )

    display_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Display name for UI"
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Node description and usage guide"
    )

    node_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Node category type (INDICATOR, CONDITION, SIGNAL, etc.)"
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Sub-category for better organization (e.g., TREND, MOMENTUM)"
    )

    # JSON fields for flexible schema definition
    parameter_schema: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="JSON Schema for node parameters with validation rules"
    )

    default_parameters: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Default parameter values"
    )

    input_ports: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="[]",
        comment="Input port definitions (type, name, required)"
    )

    output_ports: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="[]",
        comment="Output port definitions (type, name)"
    )

    # Template metadata
    is_system_template: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
        index=True,
        comment="True for built-in templates, False for custom"
    )

    user_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="User ID for custom node templates (NULL for system templates)"
    )

    # Validation and execution
    validation_rules: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional validation rules for node connections and parameters"
    )

    execution_hints: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Hints for code generation and execution optimization"
    )

    # Usage statistics
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of times template has been used"
    )

    # Icon and UI metadata
    icon: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Icon identifier or SVG for UI display"
    )

    color: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Color code for node display in builder UI"
    )

    # Version control
    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0.0",
        server_default="1.0.0",
        comment="Template version for compatibility tracking"
    )

    # Table constraints and indexes
    __table_args__ = (
        CheckConstraint("usage_count >= 0", name="check_node_usage_count_non_negative"),
        # Composite indexes for common query patterns
        Index("ix_node_type_system", "node_type", "is_system_template"),
        Index("ix_node_user_type", "user_id", "node_type"),
        Index("ix_node_category_type", "category", "node_type"),
        Index("ix_node_deleted_created", "is_deleted", "created_at"),
        # Unique constraint for system templates
        Index("ix_node_unique_system_name", "name", "is_system_template",
              unique=False),  # Can be made unique with partial index in PostgreSQL
        {"comment": "Node template storage for strategy builder", "mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    )

    def __repr__(self) -> str:
        return f"<NodeTemplate(id={self.id}, name={self.name}, type={self.node_type})>"


class QuickTest(BaseDBModel):
    """
    Quick Test model for rapid strategy validation

    Stores quick backtest configurations and results for strategy instances
    Enables fast iteration and validation of strategy logic

    Relationships:
    - Many-to-One with StrategyInstance
    """

    __tablename__ = "quick_tests"

    # Foreign key relationship
    instance_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("strategy_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to strategy instance being tested"
    )

    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="User who initiated the test"
    )

    # Test configuration
    test_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Optional name for the test run"
    )

    test_config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Test configuration (date range, stock pool, initial capital, etc.)"
    )

    logic_flow_snapshot: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Snapshot of logic flow at test time (for version tracking)"
    )

    parameters_snapshot: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Snapshot of parameters at test time"
    )

    # Execution status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
        index=True,
        comment="Test execution status (PENDING, RUNNING, COMPLETED, FAILED, CANCELLED)"
    )

    # Test results
    test_result: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Test results including metrics, trades, and performance data"
    )

    metrics_summary: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Summary metrics (returns, sharpe, max drawdown, win rate, etc.)"
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if test failed"
    )

    # Execution metadata
    execution_time: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Test execution time in seconds"
    )

    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Test start timestamp"
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Test completion timestamp"
    )

    # Relationships
    instance: Mapped["StrategyInstance"] = relationship(
        "StrategyInstance",
        foreign_keys=[instance_id],
        lazy="selectin"
    )

    # Table constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "execution_time IS NULL OR execution_time >= 0",
            name="check_execution_time_non_negative"
        ),
        # Composite indexes for common query patterns
        Index("ix_quicktest_instance_status", "instance_id", "status"),
        Index("ix_quicktest_user_created", "user_id", "created_at"),
        Index("ix_quicktest_status_created", "status", "created_at"),
        Index("ix_quicktest_user_instance", "user_id", "instance_id"),
        Index("ix_quicktest_deleted_completed", "is_deleted", "completed_at"),
        {"comment": "Quick test execution and results storage", "mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    )

    def __repr__(self) -> str:
        return f"<QuickTest(id={self.id}, instance_id={self.instance_id}, status={self.status})>"


class CodeGeneration(BaseDBModel):
    """
    Code Generation model for Logic Flow to Python code conversion

    Tracks the history of code generation from visual logic flows
    Includes validation results and version tracking

    Relationships:
    - Many-to-One with StrategyInstance
    """

    __tablename__ = "code_generations"

    # Foreign key relationship
    instance_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("strategy_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to strategy instance"
    )

    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="User who requested code generation"
    )

    # Logic flow snapshot
    logic_flow_snapshot: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Logic flow data at generation time"
    )

    parameters_snapshot: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Parameters at generation time"
    )

    # Generated code
    generated_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Generated Python code from logic flow"
    )

    code_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="SHA-256 hash of generated code for deduplication"
    )

    # Validation results
    validation_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING",
        server_default="PENDING",
        index=True,
        comment="Validation status (PENDING, VALID, SYNTAX_ERROR, SECURITY_ERROR, RUNTIME_ERROR)"
    )

    validation_result: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Detailed validation results including errors and warnings"
    )

    syntax_check_passed: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        comment="Whether syntax check passed"
    )

    security_check_passed: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        comment="Whether security scan passed"
    )

    # Code metadata
    code_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="1.0.0",
        server_default="1.0.0",
        comment="Version of code generation engine used"
    )

    line_count: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of lines in generated code"
    )

    complexity_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Cyclomatic complexity score"
    )

    # Generation metadata
    generation_time: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Code generation time in seconds"
    )

    # Relationships
    instance: Mapped["StrategyInstance"] = relationship(
        "StrategyInstance",
        foreign_keys=[instance_id],
        lazy="selectin"
    )

    # Table constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "generation_time IS NULL OR generation_time >= 0",
            name="check_generation_time_non_negative"
        ),
        CheckConstraint(
            "line_count IS NULL OR line_count >= 0",
            name="check_line_count_non_negative"
        ),
        CheckConstraint(
            "complexity_score IS NULL OR complexity_score >= 0",
            name="check_complexity_score_non_negative"
        ),
        # Composite indexes for common query patterns
        Index("ix_codegen_instance_created", "instance_id", "created_at"),
        Index("ix_codegen_user_created", "user_id", "created_at"),
        Index("ix_codegen_validation_status", "validation_status", "created_at"),
        Index("ix_codegen_user_instance", "user_id", "instance_id"),
        Index("ix_codegen_hash_instance", "code_hash", "instance_id"),
        Index("ix_codegen_deleted_created", "is_deleted", "created_at"),
        {"comment": "Code generation history and validation results", "mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    )

    def __repr__(self) -> str:
        return f"<CodeGeneration(id={self.id}, instance_id={self.instance_id}, status={self.validation_status})>"


class BuilderSession(BaseDBModel):
    """
    Builder Session model for draft auto-save and collaborative editing

    Manages user sessions in strategy builder with:
    - Auto-save functionality for unsaved changes
    - Draft storage for work-in-progress
    - Future support for collaborative editing

    Relationships:
    - Many-to-One with StrategyInstance (optional for new unsaved strategies)
    """

    __tablename__ = "builder_sessions"

    # Foreign key relationship (optional for new strategies)
    instance_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("strategy_instances.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Reference to strategy instance (NULL for new unsaved strategies)"
    )

    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="User who owns this session"
    )

    # Session metadata
    session_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="DRAFT",
        server_default="DRAFT",
        index=True,
        comment="Session type (DRAFT, AUTOSAVE, COLLABORATIVE)"
    )

    session_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Optional session name for user identification"
    )

    # Draft content
    draft_logic_flow: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        comment="Draft logic flow data"
    )

    draft_parameters: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        server_default="{}",
        comment="Draft parameter values"
    )

    draft_metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional draft metadata (cursor position, zoom level, etc.)"
    )

    # Session state
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
        index=True,
        comment="Whether session is currently active"
    )

    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Last user activity timestamp for session cleanup"
    )

    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Session expiration timestamp"
    )

    # Collaborative editing (future feature)
    collaborator_ids: Mapped[list | None] = mapped_column(
        JSON,
        nullable=True,
        comment="List of collaborator user IDs (for future collaborative editing)"
    )

    lock_info: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
        comment="Locking information for collaborative editing"
    )

    # Relationships
    instance: Mapped["StrategyInstance"] = relationship(
        "StrategyInstance",
        foreign_keys=[instance_id],
        lazy="selectin"
    )

    # Table constraints and indexes
    __table_args__ = (
        # Composite indexes for common query patterns
        Index("ix_session_user_active", "user_id", "is_active"),
        Index("ix_session_user_activity", "user_id", "last_activity_at"),
        Index("ix_session_type_active", "session_type", "is_active"),
        Index("ix_session_expires", "expires_at", "is_active"),
        Index("ix_session_instance_user", "instance_id", "user_id"),
        Index("ix_session_deleted_activity", "is_deleted", "last_activity_at"),
        {"comment": "Builder session management for draft auto-save", "mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"}
    )

    def __repr__(self) -> str:
        return f"<BuilderSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
