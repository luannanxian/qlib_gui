"""
Pydantic schemas for Task Scheduling API

Defines request and response models for task operations.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class TaskCreate(BaseModel):
    """Schema for creating a new task."""

    type: str = Field(..., description="Task type (BACKTEST, DATA_IMPORT, etc.)")
    name: str = Field(..., min_length=1, max_length=255, description="Task name")
    params: Dict[str, Any] = Field(..., description="Task parameters")
    created_by: str = Field(..., min_length=1, max_length=100, description="User who created the task")
    priority: Optional[int] = Field(default=1, ge=0, le=3, description="Task priority (0=LOW, 1=NORMAL, 2=HIGH, 3=URGENT)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "BACKTEST",
                "name": "Strategy Backtest",
                "params": {
                    "strategy_id": "strategy_001",
                    "dataset_id": "dataset_001"
                },
                "created_by": "user_001",
                "priority": 1
            }
        }
    }


class TaskResponse(BaseModel):
    """Schema for task response."""

    id: str = Field(..., description="Task ID")
    type: str = Field(..., description="Task type")
    name: str = Field(..., description="Task name")
    status: str = Field(..., description="Task status")
    priority: int = Field(..., description="Task priority")
    params: Dict[str, Any] = Field(..., description="Task parameters")
    progress: float = Field(..., description="Task progress (0-100)")
    current_step: Optional[str] = Field(None, description="Current step description")
    eta: Optional[int] = Field(None, description="Estimated time remaining (seconds)")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result data")
    error: Optional[str] = Field(None, description="Error message if task failed")
    created_by: str = Field(..., description="User who created the task")
    created_at: datetime = Field(..., description="Task creation time")
    started_at: Optional[datetime] = Field(None, description="Task start time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")
    updated_at: datetime = Field(..., description="Last update time")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "task_123",
                "type": "BACKTEST",
                "name": "Strategy Backtest",
                "status": "RUNNING",
                "priority": 1,
                "params": {
                    "strategy_id": "strategy_001",
                    "dataset_id": "dataset_001"
                },
                "progress": 50.0,
                "current_step": "Processing data",
                "eta": 120,
                "result": None,
                "error": None,
                "created_by": "user_001",
                "created_at": "2024-01-01T00:00:00",
                "started_at": "2024-01-01T00:01:00",
                "completed_at": None,
                "updated_at": "2024-01-01T00:02:00"
            }
        }
    }


class TaskUpdate(BaseModel):
    """Schema for updating a task."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Task name")
    priority: Optional[int] = Field(None, ge=0, le=3, description="Task priority")
    params: Optional[Dict[str, Any]] = Field(None, description="Task parameters")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Updated Task Name",
                "priority": 2
            }
        }
    }


class TaskProgressUpdate(BaseModel):
    """Schema for updating task progress."""

    progress: float = Field(..., ge=0.0, le=100.0, description="Task progress (0-100)")
    current_step: Optional[str] = Field(None, max_length=255, description="Current step description")
    eta: Optional[int] = Field(None, ge=0, description="Estimated time remaining (seconds)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "progress": 75.0,
                "current_step": "Calculating metrics",
                "eta": 60
            }
        }
    }


class TaskListResponse(BaseModel):
    """Schema for paginated task list response."""

    total: int = Field(..., description="Total number of tasks")
    items: List[TaskResponse] = Field(..., description="List of tasks")
    skip: int = Field(..., description="Number of records skipped")
    limit: int = Field(..., description="Maximum number of records returned")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 100,
                "items": [],
                "skip": 0,
                "limit": 10
            }
        }
    }


class TaskStats(BaseModel):
    """Schema for task statistics."""

    total: int = Field(..., description="Total number of tasks")
    pending: int = Field(..., description="Number of pending tasks")
    running: int = Field(..., description="Number of running tasks")
    paused: int = Field(..., description="Number of paused tasks")
    completed: int = Field(..., description="Number of completed tasks")
    failed: int = Field(..., description="Number of failed tasks")
    cancelled: int = Field(..., description="Number of cancelled tasks")

    model_config = {
        "json_schema_extra": {
            "example": {
                "total": 100,
                "pending": 10,
                "running": 5,
                "paused": 2,
                "completed": 70,
                "failed": 8,
                "cancelled": 5
            }
        }
    }
