"""
Strategy Module Custom Exceptions

This module defines all custom exceptions used in the Strategy module,
including Strategy Builder related exceptions.
"""


class StrategyError(Exception):
    """Base exception for Strategy module"""
    pass


class StrategyNotFoundError(StrategyError):
    """Raised when a strategy is not found"""
    pass


class StrategyValidationError(StrategyError):
    """Raised when strategy validation fails"""
    pass


# ==================== Strategy Builder Exceptions ====================

class BuilderServiceError(StrategyError):
    """Base exception for Strategy Builder services"""
    pass


class ValidationError(BuilderServiceError):
    """Raised when validation fails"""
    pass


class ResourceNotFoundError(BuilderServiceError):
    """Raised when resource is not found"""
    pass


class AuthorizationError(BuilderServiceError):
    """Raised when user is not authorized"""
    pass


class LogicFlowError(BuilderServiceError):
    """Raised when logic flow is invalid"""
    pass


class CodeGenerationError(BuilderServiceError):
    """Raised when code generation fails"""
    pass


class QuickTestError(BuilderServiceError):
    """Raised when quick test execution fails"""
    pass


class TemplateRenderError(CodeGenerationError):
    """Raised when template rendering fails"""
    pass


class TemplateNotFoundError(CodeGenerationError):
    """Raised when template file is not found"""
    pass


__all__ = [
    "StrategyError",
    "StrategyNotFoundError",
    "StrategyValidationError",
    "BuilderServiceError",
    "ValidationError",
    "ResourceNotFoundError",
    "AuthorizationError",
    "LogicFlowError",
    "CodeGenerationError",
    "QuickTestError",
    "TemplateRenderError",
    "TemplateNotFoundError",
]
