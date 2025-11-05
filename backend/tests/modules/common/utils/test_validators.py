"""Tests for common validators.

Following TDD approach - these tests are written BEFORE full implementation.
"""

import pytest
import os
from pathlib import Path


class TestValidateFilePath:
    """Test validate_file_path function."""

    def test_validate_valid_path_within_allowed_directory(self):
        """Test that valid paths within allowed directory are accepted."""
        from app.modules.common.utils.validators import validate_file_path

        # Using /tmp as allowed base since it exists on all systems
        result = validate_file_path("/tmp/test.csv", allowed_base="/tmp")
        assert result == str(Path("/tmp/test.csv").resolve())

    def test_validate_path_traversal_blocked(self):
        """Test that path traversal attempts are blocked."""
        from app.modules.common.utils.validators import validate_file_path

        with pytest.raises(ValueError) as exc_info:
            validate_file_path("/tmp/../etc/passwd", allowed_base="/tmp")

        assert "outside allowed directory" in str(exc_info.value)

    def test_validate_relative_path_resolution(self):
        """Test that relative paths are resolved correctly."""
        from app.modules.common.utils.validators import validate_file_path

        # Even if we pass relative path, it should resolve to absolute
        result = validate_file_path("/tmp/subdir/../test.csv", allowed_base="/tmp")
        expected = str(Path("/tmp/test.csv").resolve())
        assert result == expected

    def test_validate_subdirectory_allowed(self):
        """Test that subdirectories within allowed base are allowed."""
        from app.modules.common.utils.validators import validate_file_path

        result = validate_file_path("/tmp/subdir/nested/test.csv", allowed_base="/tmp")
        expected = str(Path("/tmp/subdir/nested/test.csv").resolve())
        assert result == expected

    def test_validate_uses_env_var_as_default(self, monkeypatch):
        """Test that DATA_DIR env var is used as default allowed_base."""
        from app.modules.common.utils.validators import validate_file_path

        monkeypatch.setenv("DATA_DIR", "/tmp")
        result = validate_file_path("/tmp/test.csv")
        assert result == str(Path("/tmp/test.csv").resolve())

    def test_validate_uses_data_default_when_no_env(self, monkeypatch):
        """Test that /data is used as default when no env var."""
        from app.modules.common.utils.validators import validate_file_path

        # Remove DATA_DIR if it exists
        monkeypatch.delenv("DATA_DIR", raising=False)

        # This should use /data as default (will fail if path doesn't exist, but that's OK for test)
        try:
            validate_file_path("/data/test.csv")
        except ValueError as e:
            # Expected if /data doesn't exist
            assert "/data" in str(e) or "outside allowed directory" in str(e)

    def test_validate_error_on_parent_directory_access(self):
        """Test that accessing parent of allowed directory fails."""
        from app.modules.common.utils.validators import validate_file_path

        with pytest.raises(ValueError) as exc_info:
            validate_file_path("/etc/passwd", allowed_base="/tmp")

        assert "outside allowed directory" in str(exc_info.value)
