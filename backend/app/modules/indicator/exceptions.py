"""
Custom exceptions for indicator module

Provides specific exception types for better error handling and debugging.
"""


class IndicatorServiceError(Exception):
    """Base exception for indicator services"""
    pass


class ValidationError(IndicatorServiceError):
    """Raised when input validation fails"""
    pass


class AuthorizationError(IndicatorServiceError):
    """Raised when user is not authorized for an operation"""
    pass


class ResourceNotFoundError(IndicatorServiceError):
    """Raised when requested resource is not found"""
    pass


class ConflictError(IndicatorServiceError):
    """Raised when resource conflict occurs (e.g., duplicate entry)"""
    pass


class ServiceUnavailableError(IndicatorServiceError):
    """Raised when external service is unavailable"""
    pass
