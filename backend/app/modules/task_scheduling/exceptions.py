"""
Task Scheduling Exceptions

Custom exceptions for the task scheduling module.
"""


class TaskSchedulingError(Exception):
    """Base exception for task scheduling errors."""
    pass


class TaskNotFoundError(TaskSchedulingError):
    """Raised when a task is not found."""
    pass


class TaskExecutionError(TaskSchedulingError):
    """Raised when task execution fails."""
    pass


class TaskValidationError(TaskSchedulingError):
    """Raised when task validation fails."""
    pass


class TaskCancellationError(TaskSchedulingError):
    """Raised when task cancellation fails."""
    pass
