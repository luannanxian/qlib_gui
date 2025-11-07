"""
Backtest module exceptions.

Custom exceptions for backtest configuration and execution errors.
"""


class BacktestError(Exception):
    """Base exception for backtest module."""
    pass


class InvalidConfigError(BacktestError):
    """Raised when backtest configuration is invalid."""
    pass


class InvalidDateRangeError(BacktestError):
    """Raised when date range is invalid."""
    pass


class InvalidCapitalError(BacktestError):
    """Raised when capital constraints are violated."""
    pass


class ResourceNotFoundError(BacktestError):
    """Raised when a requested resource is not found."""
    pass


class BacktestExecutionError(BacktestError):
    """Raised when backtest execution fails."""
    pass
