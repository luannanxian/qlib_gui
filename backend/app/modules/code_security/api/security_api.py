"""
Code Security API Endpoints

Provides REST API endpoints for secure code execution in sandboxed environment.

Security Considerations:
    - All code execution happens in isolated process
    - Resource limits enforced (timeout, memory)
    - TODO: Implement rate limiting per user
    - TODO: Implement IP-based restrictions
    - All executions are audit logged
"""

import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends

from app.modules.code_security.schemas import (
    ExecuteCodeRequest,
    ExecuteCodeResponse,
    HealthCheckResponse,
    ExecutionLimitsResponse
)
from app.modules.code_security.simple_executor import (
    SimpleCodeExecutor,
    ExecutionError,
    TimeoutError as ExecutorTimeoutError,
    MemoryLimitError
)
from app.modules.code_security.api.dependencies import (
    get_code_executor,
    get_current_user_id,
    set_request_correlation_id
)
from app.modules.common.schemas.response import APIResponse, success_response, error_response
from app.modules.common.logging import get_logger, AuditLogger, AuditEventType, AuditSeverity
from app.modules.common.logging.decorators import log_async_execution

# Initialize logger and audit logger
logger = get_logger(__name__)
audit_logger = AuditLogger()

router = APIRouter()

# Execution limits constants
MAX_TIMEOUT_SECONDS = 300
MIN_TIMEOUT_SECONDS = 1
MAX_MEMORY_MB = 2048
MIN_MEMORY_MB = 64
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MEMORY_MB = 512


@router.post("/execute", response_model=APIResponse[ExecuteCodeResponse])
@log_async_execution(level="INFO")
async def execute_code(
    request: ExecuteCodeRequest,
    user_id: str = Depends(get_current_user_id),
    correlation_id: str = Depends(set_request_correlation_id)
) -> APIResponse[ExecuteCodeResponse]:
    """
    Execute Python code in a sandboxed environment.

    This endpoint executes user-provided Python code in an isolated process
    with configurable resource limits (timeout, memory).

    Security Features:
        - Process isolation using multiprocessing
        - Configurable timeout (1-300 seconds)
        - Memory limits (64-2048 MB)
        - Stdout/stderr capture
        - Detailed error reporting

    Rate Limiting:
        TODO: Implement rate limiting in production
        - Suggested: 10 requests per minute per user
        - Suggested: 100 requests per hour per user

    IP Restrictions:
        TODO: Consider IP-based restrictions for production
        - Whitelist known IPs
        - Geo-blocking if needed

    Args:
        request: Code execution request with code and limits
        user_id: Authenticated user ID from dependency
        correlation_id: Request correlation ID for tracking

    Returns:
        APIResponse[ExecuteCodeResponse]: Execution result with stdout/stderr

    Raises:
        400 Bad Request: Invalid input or syntax error
        408 Request Timeout: Code execution timeout
        500 Internal Server Error: Execution error
        507 Insufficient Storage: Memory limit exceeded

    Example:
        ```python
        POST /api/security/execute
        {
            "code": "print('Hello, World!')",
            "timeout": 30,
            "max_memory_mb": 512,
            "capture_locals": false
        }
        ```

        Response:
        ```json
        {
            "success": true,
            "data": {
                "success": true,
                "stdout": "Hello, World!\\n",
                "stderr": "",
                "error_type": null,
                "error_message": null,
                "execution_time": 0.001,
                "memory_used_mb": 12.5,
                "locals_dict": null
            }
        }
        ```
    """
    logger.info(
        f"Code execution request from user {user_id}",
        extra={
            "user_id": user_id,
            "code_length": len(request.code),
            "timeout": request.timeout,
            "max_memory_mb": request.max_memory_mb,
            "correlation_id": correlation_id
        }
    )

    try:
        # Create executor with requested limits
        # Note: SimpleCodeExecutor uses multiprocessing which is blocking
        # We use asyncio.to_thread to prevent blocking the event loop
        executor = SimpleCodeExecutor(
            timeout=request.timeout or DEFAULT_TIMEOUT_SECONDS,
            max_memory_mb=request.max_memory_mb or DEFAULT_MEMORY_MB
        )

        # Execute code in a separate thread to avoid blocking
        # This is necessary because multiprocessing operations are blocking
        result = await asyncio.to_thread(
            executor.execute,
            code=request.code,
            globals_dict=request.globals,
            locals_dict=request.locals,
            capture_locals=request.capture_locals
        )

        # Convert ExecutionResult to response schema
        response_data = ExecuteCodeResponse(
            success=result.success,
            stdout=result.stdout,
            stderr=result.stderr,
            error_type=type(result.error).__name__ if result.error else None,
            error_message=str(result.error) if result.error else None,
            execution_time=result.execution_time,
            memory_used_mb=result.memory_used_mb,
            locals_dict=result.locals_dict
        )

        # Audit log successful execution
        # Using DATA_CREATED as a proxy for code execution audit events
        # TODO: Add CODE_EXECUTED to AuditEventType enum in future
        audit_logger.log_event(
            event_type=AuditEventType.DATA_CREATED,
            severity=AuditSeverity.LOW,
            user_id=user_id,
            resource_type="code_execution",
            resource_id=correlation_id,
            action="execute_code",
            details={
                "success": result.success,
                "code_length": len(request.code),
                "execution_time": result.execution_time,
                "memory_used_mb": result.memory_used_mb,
                "has_error": result.error is not None,
                "error_type": type(result.error).__name__ if result.error else None,
                "correlation_id": correlation_id
            }
        )

        logger.info(
            f"Code execution completed for user {user_id}",
            extra={
                "user_id": user_id,
                "success": result.success,
                "execution_time": result.execution_time,
                "correlation_id": correlation_id
            }
        )

        return success_response(response_data)

    except ExecutorTimeoutError as e:
        # Code execution timed out
        logger.warning(
            f"Code execution timeout for user {user_id}",
            extra={
                "user_id": user_id,
                "timeout": request.timeout,
                "correlation_id": correlation_id
            }
        )

        # Audit log timeout
        # Using SECURITY_VIOLATION for timeout events
        audit_logger.log_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            severity=AuditSeverity.MEDIUM,
            user_id=user_id,
            resource_type="code_execution",
            resource_id=correlation_id,
            action="execute_code_timeout",
            details={
                "timeout": request.timeout,
                "correlation_id": correlation_id
            }
        )

        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Code execution timeout after {request.timeout} seconds"
        )

    except MemoryLimitError as e:
        # Memory limit exceeded
        logger.warning(
            f"Code execution memory limit exceeded for user {user_id}",
            extra={
                "user_id": user_id,
                "max_memory_mb": request.max_memory_mb,
                "correlation_id": correlation_id
            }
        )

        # Audit log memory error
        # Using SECURITY_VIOLATION for memory limit errors
        audit_logger.log_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            severity=AuditSeverity.MEDIUM,
            user_id=user_id,
            resource_type="code_execution",
            resource_id=correlation_id,
            action="execute_code_memory_exceeded",
            details={
                "max_memory_mb": request.max_memory_mb,
                "correlation_id": correlation_id
            }
        )

        raise HTTPException(
            status_code=status.HTTP_507_INSUFFICIENT_STORAGE,
            detail=f"Code execution exceeded memory limit of {request.max_memory_mb} MB"
        )

    except SyntaxError as e:
        # Syntax error in code
        logger.info(
            f"Code execution syntax error for user {user_id}",
            extra={
                "user_id": user_id,
                "error": str(e),
                "correlation_id": correlation_id
            }
        )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Syntax error in code: {str(e)}"
        )

    except ExecutionError as e:
        # General execution error
        logger.error(
            f"Code execution error for user {user_id}",
            extra={
                "user_id": user_id,
                "error": str(e),
                "correlation_id": correlation_id
            },
            exc_info=True
        )

        # Audit log execution error
        # Using SECURITY_VIOLATION for execution errors
        audit_logger.log_event(
            event_type=AuditEventType.SECURITY_VIOLATION,
            severity=AuditSeverity.HIGH,
            user_id=user_id,
            resource_type="code_execution",
            resource_id=correlation_id,
            action="execute_code_error",
            details={
                "error": str(e),
                "correlation_id": correlation_id
            }
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code execution failed: {str(e)}"
        )

    except Exception as e:
        # Unexpected error
        logger.error(
            f"Unexpected error during code execution for user {user_id}",
            extra={
                "user_id": user_id,
                "error": str(e),
                "correlation_id": correlation_id
            },
            exc_info=True
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during code execution"
        )


@router.get("/health", response_model=APIResponse[HealthCheckResponse])
async def health_check() -> APIResponse[HealthCheckResponse]:
    """
    Health check endpoint for code execution service.

    This endpoint does not require authentication and can be used
    to verify that the code execution service is operational.

    Returns:
        APIResponse[HealthCheckResponse]: Service health status

    Example:
        ```
        GET /api/security/health
        ```

        Response:
        ```json
        {
            "success": true,
            "data": {
                "status": "healthy",
                "executor_available": true,
                "default_timeout": 30,
                "default_memory_limit_mb": 512
            }
        }
        ```
    """
    try:
        # Test executor creation
        executor = SimpleCodeExecutor(
            timeout=DEFAULT_TIMEOUT_SECONDS,
            max_memory_mb=DEFAULT_MEMORY_MB
        )
        executor_available = True
    except Exception as e:
        logger.error(f"Executor health check failed: {e}", exc_info=True)
        executor_available = False

    response_data = HealthCheckResponse(
        status="healthy" if executor_available else "degraded",
        executor_available=executor_available,
        default_timeout=DEFAULT_TIMEOUT_SECONDS,
        default_memory_limit_mb=DEFAULT_MEMORY_MB
    )

    return success_response(response_data)


@router.get("/limits", response_model=APIResponse[ExecutionLimitsResponse])
@log_async_execution(level="INFO")
async def get_execution_limits(
    user_id: str = Depends(get_current_user_id),
    correlation_id: str = Depends(set_request_correlation_id)
) -> APIResponse[ExecutionLimitsResponse]:
    """
    Get current execution limits for code execution.

    Returns the maximum and minimum allowed values for timeout and memory limits,
    as well as the default values used when not specified.

    Requires authentication.

    Args:
        user_id: Authenticated user ID from dependency
        correlation_id: Request correlation ID for tracking

    Returns:
        APIResponse[ExecutionLimitsResponse]: Current execution limits

    Example:
        ```
        GET /api/security/limits
        ```

        Response:
        ```json
        {
            "success": true,
            "data": {
                "max_timeout_seconds": 300,
                "min_timeout_seconds": 1,
                "max_memory_mb": 2048,
                "min_memory_mb": 64,
                "default_timeout_seconds": 30,
                "default_memory_mb": 512
            }
        }
        ```
    """
    logger.info(
        f"Execution limits requested by user {user_id}",
        extra={
            "user_id": user_id,
            "correlation_id": correlation_id
        }
    )

    response_data = ExecutionLimitsResponse(
        max_timeout_seconds=MAX_TIMEOUT_SECONDS,
        min_timeout_seconds=MIN_TIMEOUT_SECONDS,
        max_memory_mb=MAX_MEMORY_MB,
        min_memory_mb=MIN_MEMORY_MB,
        default_timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        default_memory_mb=DEFAULT_MEMORY_MB
    )

    return success_response(response_data)
