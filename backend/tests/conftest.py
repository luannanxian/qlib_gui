"""Pytest configuration and fixtures for the entire test suite."""

import pytest
from datetime import datetime, date, timedelta
from typing import Generator
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def sample_datetime() -> datetime:
    """Return a fixed datetime for testing."""
    return datetime(2024, 1, 15, 10, 30, 45)


@pytest.fixture
def sample_date() -> date:
    """Return a fixed date for testing."""
    return date(2024, 1, 15)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for file operations."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def sample_file(temp_dir: Path) -> Path:
    """Create a sample file for testing."""
    file_path = temp_dir / "test_file.txt"
    file_path.write_text("Sample content for testing")
    return file_path


@pytest.fixture
def mock_current_time(monkeypatch) -> datetime:
    """Mock datetime.now() to return a fixed time."""
    fixed_time = datetime(2024, 1, 15, 12, 0, 0)

    class MockDatetime:
        @classmethod
        def now(cls):
            return fixed_time

    monkeypatch.setattr("datetime.datetime", MockDatetime)
    return fixed_time
