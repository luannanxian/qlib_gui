"""
Task SQLAlchemy Model

This module defines the database model for the Task Scheduling System.
"""

import enum
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import String, Float, Integer, JSON, Index, CheckConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import BaseDBModel


class TaskType(str, enum.Enum):
    """Task type enumeration"""
    BACKTEST = "BACKTEST"
    OPTIMIZATION = "OPTIMIZATION"
    DATA_IMPORT = "DATA_IMPORT"
    DATA_PREPROCESSING = "DATA_PREPROCESSING"
    FACTOR_BACKTEST = "FACTOR_BACKTEST"
    CUSTOM_CODE = "CUSTOM_CODE"


class TaskStatus(str, enum.Enum):
    """Task status enumeration"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class TaskPriority(int, enum.Enum):
    """Task priority enumeration"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class Task(BaseDBModel):
    """
    Task model for managing background tasks

    Stores task configuration, status, progress, and results.
    Supports various task types including backtest, data import, optimization, etc.

    Relationships:
    - Can be associated with users (via created_by)
    - Can reference other entities (via params JSON)
    """

    __tablename__ = "tasks"

    # Task identification
    type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Task type (BACKTEST, DATA_IMPORT, etc.)"
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Task name/description"
    )

    # Task status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Task status (PENDING, RUNNING, COMPLETED, etc.)"
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=TaskPriority.NORMAL.value,
        index=True,
        comment="Task priority (0=LOW, 1=NORMAL, 2=HIGH, 3=URGENT)"
    )

    # Task parameters (JSON)
    params: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Task parameters and configuration"
    )

    # Progress tracking
    progress: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        comment="Task progress (0-100)"
    )

    current_step: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Current step description"
    )

    eta: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Estimated time remaining (seconds)"
    )

    # Results and errors
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Task result data"
    )

    error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if task failed"
    )

    # Metadata
    created_by: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="User who created the task"
    )

    started_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Task start time"
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Task completion time"
    )

    # Indexes for query optimization
    __table_args__ = (
        Index('idx_task_type_status', 'type', 'status'),
        Index('idx_task_created_by_status', 'created_by', 'status'),
        Index('idx_task_priority_status', 'priority', 'status'),
        CheckConstraint('progress >= 0 AND progress <= 100', name='check_progress_range'),
        CheckConstraint('priority >= 0 AND priority <= 3', name='check_priority_range'),
    )

    def __init__(self, **kwargs):
        """Initialize Task with default values for optional fields"""
        # Set default values if not provided
        if 'priority' not in kwargs:
            kwargs['priority'] = TaskPriority.NORMAL.value
        if 'progress' not in kwargs:
            kwargs['progress'] = 0.0
        super().__init__(**kwargs)
