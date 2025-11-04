"""
Base Exceptions for Qlib-UI
"""


class QlibUIException(Exception):
    """Base exception for all Qlib-UI errors"""

    def __init__(
        self, message: str, code: str = "INTERNAL_ERROR", details: dict = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)
