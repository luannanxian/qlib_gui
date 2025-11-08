"""
Test fixtures for code security API tests.
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from app.main import app
from app.modules.code_security.simple_executor import SimpleCodeExecutor, ExecutionResult


@pytest.fixture
def client():
    """
    FastAPI test client.
    """
    return TestClient(app)


@pytest.fixture
def mock_user_id():
    """
    Mock user ID for authentication.
    """
    return "test_user_123"


@pytest.fixture
def mock_correlation_id():
    """
    Mock correlation ID for request tracking.
    """
    return "test_correlation_id_456"


@pytest.fixture
def mock_executor():
    """
    Mock SimpleCodeExecutor instance.
    """
    return Mock(spec=SimpleCodeExecutor)


@pytest.fixture
def successful_execution_result():
    """
    Mock successful execution result.
    """
    return ExecutionResult(
        success=True,
        stdout="Hello, World!\n",
        stderr="",
        error=None,
        execution_time=0.001,
        memory_used_mb=12.5,
        locals_dict=None
    )


@pytest.fixture
def failed_execution_result():
    """
    Mock failed execution result with error.
    """
    return ExecutionResult(
        success=False,
        stdout="",
        stderr="Traceback...",
        error=ValueError("Division by zero"),
        execution_time=0.001,
        memory_used_mb=10.0,
        locals_dict=None
    )


@pytest.fixture
def execution_with_locals():
    """
    Mock execution result with captured locals.
    """
    return ExecutionResult(
        success=True,
        stdout="",
        stderr="",
        error=None,
        execution_time=0.002,
        memory_used_mb=15.0,
        locals_dict={"x": 42, "y": "test"}
    )


def make_async_return(value):
    """
    Helper to create an async function that returns a value.
    Used for mocking asyncio.to_thread.
    """
    async def async_func(*args, **kwargs):
        return value
    return async_func
