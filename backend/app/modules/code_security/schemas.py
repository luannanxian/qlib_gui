"""
Code Security API Schemas

Pydantic models for code execution API requests and responses.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator


class ExecuteCodeRequest(BaseModel):
    """
    Request schema for code execution.

    Security Note:
        All code execution happens in a sandboxed environment with resource limits.
        See SimpleCodeExecutor for implementation details.
    """
    code: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Python code to execute in sandbox",
        examples=["print('Hello, World!')"]
    )
    timeout: Optional[int] = Field(
        default=30,
        ge=1,
        le=300,
        description="Maximum execution time in seconds (1-300)"
    )
    max_memory_mb: Optional[int] = Field(
        default=512,
        ge=64,
        le=2048,
        description="Maximum memory limit in MB (64-2048)"
    )
    globals: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Global variables for execution context"
    )
    locals: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Local variables for execution context"
    )
    capture_locals: bool = Field(
        default=False,
        description="Whether to capture local variables after execution"
    )

    @field_validator('code')
    @classmethod
    def validate_code_not_empty(cls, v: str) -> str:
        """Ensure code is not just whitespace"""
        if not v or not v.strip():
            raise ValueError("Code cannot be empty or whitespace only")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "code": "import numpy as np\nresult = np.array([1, 2, 3]).mean()\nprint(f'Mean: {result}')",
                "timeout": 30,
                "max_memory_mb": 512,
                "capture_locals": True
            }
        }


class ExecuteCodeResponse(BaseModel):
    """
    Response schema for code execution result.
    """
    success: bool = Field(
        ...,
        description="Whether code execution completed successfully"
    )
    stdout: str = Field(
        default="",
        description="Standard output from code execution"
    )
    stderr: str = Field(
        default="",
        description="Standard error from code execution"
    )
    error_type: Optional[str] = Field(
        default=None,
        description="Type of error if execution failed"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if execution failed"
    )
    execution_time: float = Field(
        ...,
        ge=0,
        description="Actual execution time in seconds"
    )
    memory_used_mb: float = Field(
        default=0.0,
        ge=0,
        description="Approximate memory used in MB"
    )
    locals_dict: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Local variables after execution (if capture_locals=True)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "stdout": "Mean: 2.0\n",
                "stderr": "",
                "error_type": None,
                "error_message": None,
                "execution_time": 0.125,
                "memory_used_mb": 45.2,
                "locals_dict": {"result": 2.0}
            }
        }


class HealthCheckResponse(BaseModel):
    """
    Response schema for health check endpoint.
    """
    status: str = Field(
        ...,
        description="Service health status"
    )
    executor_available: bool = Field(
        ...,
        description="Whether code executor is available"
    )
    default_timeout: int = Field(
        ...,
        description="Default timeout in seconds"
    )
    default_memory_limit_mb: int = Field(
        ...,
        description="Default memory limit in MB"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "executor_available": True,
                "default_timeout": 30,
                "default_memory_limit_mb": 512
            }
        }


class ExecutionLimitsResponse(BaseModel):
    """
    Response schema for execution limits endpoint.
    """
    max_timeout_seconds: int = Field(
        ...,
        description="Maximum allowed timeout in seconds"
    )
    min_timeout_seconds: int = Field(
        ...,
        description="Minimum allowed timeout in seconds"
    )
    max_memory_mb: int = Field(
        ...,
        description="Maximum allowed memory in MB"
    )
    min_memory_mb: int = Field(
        ...,
        description="Minimum allowed memory in MB"
    )
    default_timeout_seconds: int = Field(
        ...,
        description="Default timeout in seconds"
    )
    default_memory_mb: int = Field(
        ...,
        description="Default memory in MB"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "max_timeout_seconds": 300,
                "min_timeout_seconds": 1,
                "max_memory_mb": 2048,
                "min_memory_mb": 64,
                "default_timeout_seconds": 30,
                "default_memory_mb": 512
            }
        }
