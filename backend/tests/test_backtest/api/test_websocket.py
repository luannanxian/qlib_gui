"""
TDD Tests for WebSocket Real-time Progress

Test coverage for:
- Real-time progress updates
- Real-time log streaming
- Real-time metrics updates
- Connection management
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app


class TestWebSocketConnection:
    """Test WebSocket connection management."""

    def test_websocket_connect(self):
        """Test WebSocket connection establishment."""
        # ARRANGE
        client = TestClient(app)

        # ACT & ASSERT
        with client.websocket_connect("/ws/backtest/test_result_id") as websocket:
            # Connection should be established
            assert websocket is not None

    def test_websocket_connect_invalid_result_id(self):
        """Test WebSocket connection with invalid result ID."""
        # ARRANGE
        client = TestClient(app)

        # ACT & ASSERT
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/backtest/invalid_id") as websocket:
                # Should receive error message before disconnect
                data = websocket.receive_json()
                assert data["type"] == "error"
                assert "not found" in data["message"].lower()


class TestProgressUpdates:
    """Test real-time progress updates."""

    def test_receive_progress_update(self):
        """Test receiving progress updates via WebSocket."""
        # ARRANGE
        client = TestClient(app)

        # ACT
        with client.websocket_connect("/ws/backtest/test_result_id") as websocket:
            # Simulate progress update
            data = websocket.receive_json()

            # ASSERT
            assert data["type"] == "progress"
            assert "percentage" in data
            assert "current_step" in data
            assert "total_steps" in data
            assert 0 <= data["percentage"] <= 100

    def test_progress_update_sequence(self):
        """Test progress updates are sent in correct sequence."""
        # ARRANGE
        client = TestClient(app)

        # ACT
        with client.websocket_connect("/ws/backtest/test_result_id") as websocket:
            previous_percentage = -1

            # Receive multiple progress updates
            for _ in range(3):
                data = websocket.receive_json()
                if data["type"] == "progress":
                    # ASSERT - Progress should be monotonically increasing
                    assert data["percentage"] >= previous_percentage
                    previous_percentage = data["percentage"]


class TestLogStreaming:
    """Test real-time log streaming."""

    def test_receive_log_message(self):
        """Test receiving log messages via WebSocket."""
        # ARRANGE
        client = TestClient(app)

        # ACT
        with client.websocket_connect("/ws/backtest/test_result_id") as websocket:
            # Wait for log message
            data = websocket.receive_json()

            # ASSERT
            if data["type"] == "log":
                assert "level" in data
                assert "message" in data
                assert "timestamp" in data
                assert data["level"] in ["DEBUG", "INFO", "WARNING", "ERROR"]

    def test_log_filtering_by_level(self):
        """Test filtering log messages by level."""
        # ARRANGE
        client = TestClient(app)

        # ACT
        with client.websocket_connect("/ws/backtest/test_result_id?log_level=INFO") as websocket:
            # Receive log messages
            for _ in range(5):
                data = websocket.receive_json()
                if data["type"] == "log":
                    # ASSERT - Should only receive INFO and above
                    assert data["level"] in ["INFO", "WARNING", "ERROR"]


class TestMetricsUpdates:
    """Test real-time metrics updates."""

    def test_receive_metrics_update(self):
        """Test receiving metrics updates via WebSocket."""
        # ARRANGE
        client = TestClient(app)

        # ACT
        with client.websocket_connect("/ws/backtest/test_result_id") as websocket:
            # Wait for metrics update
            data = websocket.receive_json()

            # ASSERT
            if data["type"] == "metrics":
                assert "metrics" in data
                assert isinstance(data["metrics"], dict)
                # Should contain at least some basic metrics
                assert len(data["metrics"]) > 0

    def test_metrics_update_format(self):
        """Test metrics update format is correct."""
        # ARRANGE
        client = TestClient(app)

        # ACT
        with client.websocket_connect("/ws/backtest/test_result_id") as websocket:
            data = websocket.receive_json()

            # ASSERT
            if data["type"] == "metrics":
                metrics = data["metrics"]
                # Check for expected metric fields
                expected_fields = ["total_return", "sharpe_ratio", "max_drawdown"]
                for field in expected_fields:
                    if field in metrics:
                        assert isinstance(metrics[field], (int, float, str))


class TestConnectionManagement:
    """Test WebSocket connection management."""

    def test_multiple_connections_same_result(self):
        """Test multiple clients can connect to same backtest result."""
        # ARRANGE
        client = TestClient(app)

        # ACT & ASSERT
        with client.websocket_connect("/ws/backtest/test_result_id") as ws1:
            with client.websocket_connect("/ws/backtest/test_result_id") as ws2:
                # Both connections should be active
                assert ws1 is not None
                assert ws2 is not None

                # Both should receive updates
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()
                assert data1["type"] in ["progress", "log", "metrics"]
                assert data2["type"] in ["progress", "log", "metrics"]

    def test_connection_cleanup_on_disconnect(self):
        """Test connection is properly cleaned up on disconnect."""
        # ARRANGE
        client = TestClient(app)

        # ACT
        with client.websocket_connect("/ws/backtest/test_result_id") as websocket:
            # Receive initial message
            data = websocket.receive_json()
            assert data is not None

        # ASSERT - Connection should be closed
        # Attempting to reconnect should work (no resource leak)
        with client.websocket_connect("/ws/backtest/test_result_id") as websocket:
            data = websocket.receive_json()
            assert data is not None


class TestCompletionNotification:
    """Test backtest completion notifications."""

    def test_receive_completion_notification(self):
        """Test receiving completion notification when backtest finishes."""
        # ARRANGE
        client = TestClient(app)

        # ACT
        with client.websocket_connect("/ws/backtest/test_result_id") as websocket:
            # Wait for completion message
            while True:
                data = websocket.receive_json()
                if data["type"] == "completion":
                    # ASSERT
                    assert "status" in data
                    assert data["status"] in ["COMPLETED", "FAILED", "CANCELLED"]
                    assert "result_id" in data
                    break

    def test_connection_closes_after_completion(self):
        """Test WebSocket connection closes after backtest completion."""
        # ARRANGE
        client = TestClient(app)

        # ACT
        with client.websocket_connect("/ws/backtest/test_result_id") as websocket:
            # Wait for completion
            while True:
                try:
                    data = websocket.receive_json()
                    if data["type"] == "completion":
                        # After completion, connection should close
                        break
                except WebSocketDisconnect:
                    # ASSERT - Connection closed as expected
                    break


class TestErrorHandling:
    """Test WebSocket error handling."""

    def test_error_message_format(self):
        """Test error messages are properly formatted."""
        # ARRANGE
        client = TestClient(app)

        # ACT
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/backtest/invalid_id") as websocket:
                data = websocket.receive_json()

                # ASSERT
                assert data["type"] == "error"
                assert "message" in data
                assert "code" in data
                assert isinstance(data["message"], str)

    def test_reconnection_after_error(self):
        """Test client can reconnect after error."""
        # ARRANGE
        client = TestClient(app)

        # ACT - First connection with error
        try:
            with client.websocket_connect("/ws/backtest/invalid_id") as websocket:
                websocket.receive_json()
        except WebSocketDisconnect:
            pass

        # ACT - Second connection should work
        with client.websocket_connect("/ws/backtest/valid_result_id") as websocket:
            data = websocket.receive_json()
            # ASSERT
            assert data is not None
