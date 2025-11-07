"""
TDD Tests for WebSocket Service

Test coverage for:
- Connection management
- Message broadcasting
- Progress updates
- Log streaming
- Metrics updates
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.modules.backtest.websocket.connection_manager import ConnectionManager


class TestConnectionManager:
    """Test WebSocket connection manager."""

    @pytest.fixture
    def manager(self):
        """Create a ConnectionManager instance for testing."""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket connection."""
        ws = Mock()
        ws.send_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect_websocket(self, manager: ConnectionManager, mock_websocket):
        """Test connecting a WebSocket."""
        # ARRANGE
        result_id = "test_result_id"
        mock_websocket.accept = AsyncMock()

        # ACT
        await manager.connect(mock_websocket, result_id)

        # ASSERT
        mock_websocket.accept.assert_called_once()
        assert result_id in manager.active_connections
        assert mock_websocket in manager.active_connections[result_id]

    @pytest.mark.asyncio
    async def test_disconnect_websocket(self, manager: ConnectionManager, mock_websocket):
        """Test disconnecting a WebSocket."""
        # ARRANGE
        result_id = "test_result_id"
        mock_websocket.accept = AsyncMock()
        await manager.connect(mock_websocket, result_id)

        # ACT
        await manager.disconnect(mock_websocket, result_id)

        # ASSERT
        assert result_id not in manager.active_connections

    @pytest.mark.asyncio
    async def test_send_personal_message(self, manager: ConnectionManager, mock_websocket):
        """Test sending a personal message to a WebSocket."""
        # ARRANGE
        message = {"type": "test", "data": "hello"}

        # ACT
        await manager.send_personal_message(message, mock_websocket)

        # ASSERT
        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_result(self, manager: ConnectionManager):
        """Test broadcasting a message to all connections for a result."""
        # ARRANGE
        result_id = "test_result_id"
        ws1 = Mock()
        ws1.send_json = AsyncMock()
        ws1.accept = AsyncMock()
        ws2 = Mock()
        ws2.send_json = AsyncMock()
        ws2.accept = AsyncMock()

        await manager.connect(ws1, result_id)
        await manager.connect(ws2, result_id)

        message = {"type": "test", "data": "broadcast"}

        # ACT
        await manager.broadcast_to_result(message, result_id)

        # ASSERT
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_progress_update(self, manager: ConnectionManager, mock_websocket):
        """Test sending progress update."""
        # ARRANGE
        result_id = "test_result_id"
        mock_websocket.accept = AsyncMock()
        await manager.connect(mock_websocket, result_id)

        # ACT
        await manager.send_progress_update(
            result_id=result_id,
            percentage=50.0,
            current_step=5,
            total_steps=10,
            message="Processing..."
        )

        # ASSERT
        assert mock_websocket.send_json.called
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "progress"
        assert call_args["percentage"] == 50.0
        assert call_args["current_step"] == 5
        assert call_args["total_steps"] == 10

    @pytest.mark.asyncio
    async def test_send_log_message(self, manager: ConnectionManager, mock_websocket):
        """Test sending log message."""
        # ARRANGE
        result_id = "test_result_id"
        mock_websocket.accept = AsyncMock()
        await manager.connect(mock_websocket, result_id)

        # ACT
        await manager.send_log_message(
            result_id=result_id,
            level="INFO",
            message="Test log message"
        )

        # ASSERT
        assert mock_websocket.send_json.called
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "log"
        assert call_args["level"] == "INFO"
        assert call_args["message"] == "Test log message"

    @pytest.mark.asyncio
    async def test_send_metrics_update(self, manager: ConnectionManager, mock_websocket):
        """Test sending metrics update."""
        # ARRANGE
        result_id = "test_result_id"
        mock_websocket.accept = AsyncMock()
        await manager.connect(mock_websocket, result_id)

        metrics = {
            "total_return": 0.15,
            "sharpe_ratio": 1.5
        }

        # ACT
        await manager.send_metrics_update(result_id=result_id, metrics=metrics)

        # ASSERT
        assert mock_websocket.send_json.called
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "metrics"
        assert call_args["metrics"] == metrics

    @pytest.mark.asyncio
    async def test_send_completion(self, manager: ConnectionManager, mock_websocket):
        """Test sending completion notification."""
        # ARRANGE
        result_id = "test_result_id"
        mock_websocket.accept = AsyncMock()
        await manager.connect(mock_websocket, result_id)

        # ACT
        await manager.send_completion(result_id=result_id, status="COMPLETED")

        # ASSERT
        assert mock_websocket.send_json.called
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "completion"
        assert call_args["status"] == "COMPLETED"
        assert call_args["result_id"] == result_id

    @pytest.mark.asyncio
    async def test_send_error(self, manager: ConnectionManager, mock_websocket):
        """Test sending error message."""
        # ARRANGE
        error_message = "Test error"
        error_code = "TEST_ERROR"

        # ACT
        await manager.send_error(mock_websocket, error_message, error_code)

        # ASSERT
        assert mock_websocket.send_json.called
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert call_args["message"] == error_message
        assert call_args["code"] == error_code

    def test_get_connection_count(self, manager: ConnectionManager):
        """Test getting connection count."""
        # ARRANGE
        result_id = "test_result_id"

        # ACT
        count_before = manager.get_connection_count(result_id)

        # ASSERT
        assert count_before == 0

    @pytest.mark.asyncio
    async def test_multiple_connections_same_result(self, manager: ConnectionManager):
        """Test multiple connections to the same result."""
        # ARRANGE
        result_id = "test_result_id"
        ws1 = Mock()
        ws1.accept = AsyncMock()
        ws2 = Mock()
        ws2.accept = AsyncMock()

        # ACT
        await manager.connect(ws1, result_id)
        await manager.connect(ws2, result_id)

        # ASSERT
        assert manager.get_connection_count(result_id) == 2

    @pytest.mark.asyncio
    async def test_connection_cleanup(self, manager: ConnectionManager, mock_websocket):
        """Test connection cleanup after disconnect."""
        # ARRANGE
        result_id = "test_result_id"
        mock_websocket.accept = AsyncMock()
        await manager.connect(mock_websocket, result_id)

        # ACT
        await manager.disconnect(mock_websocket, result_id)

        # ASSERT
        assert manager.get_connection_count(result_id) == 0
        assert result_id not in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_handles_failed_connections(self, manager: ConnectionManager):
        """Test broadcast handles failed connections gracefully."""
        # ARRANGE
        result_id = "test_result_id"
        ws_good = Mock()
        ws_good.send_json = AsyncMock()
        ws_good.accept = AsyncMock()
        ws_bad = Mock()
        ws_bad.send_json = AsyncMock(side_effect=Exception("Connection failed"))
        ws_bad.accept = AsyncMock()

        await manager.connect(ws_good, result_id)
        await manager.connect(ws_bad, result_id)

        message = {"type": "test", "data": "broadcast"}

        # ACT
        await manager.broadcast_to_result(message, result_id)

        # ASSERT
        # Good connection should receive message
        ws_good.send_json.assert_called_once_with(message)
        # Bad connection should be attempted but fail gracefully
        ws_bad.send_json.assert_called_once_with(message)
        # Bad connection should be cleaned up
        assert manager.get_connection_count(result_id) == 1
