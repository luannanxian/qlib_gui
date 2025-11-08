"""
Pytest configuration for Code Security tests.

Provides fixtures for testing code execution with security constraints.
"""

import pytest


@pytest.fixture
def sample_safe_code():
    """Sample safe Python code for testing."""
    return """
result = 1 + 1
print(f"Result: {result}")
"""


@pytest.fixture
def sample_code_with_return():
    """Sample code that returns a value."""
    return """
def calculate():
    return 42

result = calculate()
"""


@pytest.fixture
def sample_infinite_loop():
    """Sample code with infinite loop for timeout testing."""
    return """
while True:
    pass
"""


@pytest.fixture
def sample_memory_intensive():
    """Sample code that consumes large memory."""
    return """
# Allocate large list (approximately 100MB)
large_list = [0] * (100 * 1024 * 1024 // 8)
"""


@pytest.fixture
def sample_code_with_error():
    """Sample code that raises an error."""
    return """
raise ValueError("Test error message")
"""


@pytest.fixture
def sample_code_with_import():
    """Sample code that imports modules."""
    return """
import math
result = math.sqrt(16)
"""
