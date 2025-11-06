"""Exception Handlers

Global exception handlers for FastAPI application to ensure consistent error responses.
"""

from typing import Union
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.modules.common.exceptions import ApplicationException
from app.modules.common.schemas.error import ErrorResponse, ErrorDetail, ErrorCode
from app.modules.common.logging import get_logger

logger = get_logger(__name__)


async def application_exception_handler(
    request: Request,
    exc: ApplicationException
) -> JSONResponse:
    """Handle custom application exceptions."""
    request_id = request.headers.get("X-Correlation-ID", "unknown")

    logger.error(
        f"Application exception: {exc.error_code}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "request_id": request_id,
            "path": request.url.path,
            "details": exc.error_details
        }
    )

    error_response = ErrorResponse(
        error_code=exc.error_code,
        message=exc.detail.get("message") if isinstance(exc.detail, dict) else str(exc.detail),
        details=[ErrorDetail(**d) for d in exc.error_details] if exc.error_details else None,
        request_id=request_id
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(exclude_none=True),
        headers=exc.headers
    )


async def validation_exception_handler(
    request: Request,
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    request_id = request.headers.get("X-Correlation-ID", "unknown")

    # Convert Pydantic errors to our error format
    error_details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        error_details.append(
            ErrorDetail(
                field=field if field else None,
                message=error["msg"],
                code="VALIDATION_ERROR"
            )
        )

    logger.warning(
        "Validation error",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "errors": error_details
        }
    )

    error_response = ErrorResponse(
        error_code=ErrorCode.VALIDATION_ERROR,
        message="Invalid input data",
        details=error_details,
        request_id=request_id
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(exclude_none=True)
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """Handle database errors."""
    request_id = request.headers.get("X-Correlation-ID", "unknown")

    # Check if it's an integrity error (unique constraint, foreign key, etc.)
    if isinstance(exc, IntegrityError):
        error_code = ErrorCode.DUPLICATE_ENTRY
        message = "Database constraint violation"
        status_code = status.HTTP_409_CONFLICT

        # Try to extract meaningful info from the error
        error_msg = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
        if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
            message = "Record with this value already exists"
        elif "foreign key" in error_msg.lower():
            message = "Referenced record does not exist"

        logger.error(
            "Database integrity error",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "error": error_msg
            }
        )
    else:
        error_code = ErrorCode.DATABASE_ERROR
        message = "Database operation failed"
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        logger.error(
            "Database error",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "error": str(exc)
            },
            exc_info=True
        )

    error_response = ErrorResponse(
        error_code=error_code,
        message=message,
        request_id=request_id
    )

    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(exclude_none=True)
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions."""
    request_id = request.headers.get("X-Correlation-ID", "unknown")

    logger.error(
        "Unexpected error",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "error_type": type(exc).__name__
        },
        exc_info=True
    )

    error_response = ErrorResponse(
        error_code=ErrorCode.INTERNAL_ERROR,
        message="An unexpected error occurred",
        request_id=request_id
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(exclude_none=True)
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(ApplicationException, application_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
