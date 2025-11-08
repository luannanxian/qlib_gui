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
from datetime import datetime

from app.modules.backtest.websocket.connection_manager import ConnectionManager


class TestConnectionManager:
    """Test WebSocket connection manager."""

    @pytest.fixture
    def manager(self):
        """Create a ConnectionManager instance for testing."""
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self, mocker):
        """Create a mock WebSocket connection."""
        ws = mocker.Mock()
        ws.send_json = mocker.AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect_websocket(self, manager: ConnectionManager, mock_websocket, mocker):
        """Test connecting a WebSocket."""
        # ARRANGE
        result_id = "test_result_id"
        mock_websocket.accept = mocker.AsyncMock()

        # ACT
        await manager.connect(mock_websocket, result_id)

        # ASSERT
        mock_websocket.accept.assert_called_once()
        assert result_id in manager.active_connections
        assert mock_websocket in manager.active_connections[result_id]

    @pytest.mark.asyncio
    async def test_disconnect_websocket(self, manager: ConnectionManager, mock_websocket, mocker):
        """Test disconnecting a WebSocket."""
        # ARRANGE
        result_id = "test_result_id"
        mock_websocket.accept = mocker.AsyncMock()
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
    async def test_broadcast_to_result(self, manager: ConnectionManager, mocker):
        """Test broadcasting a message to all connections for a result."""
        # ARRANGE
        result_id = "test_result_id"
        ws1 = mocker.Mock()
        ws1.send_json = mocker.AsyncMock()
        ws1.accept = mocker.AsyncMock()
        ws2 = mocker.Mock()
        ws2.send_json = mocker.AsyncMock()
        ws2.accept = mocker.AsyncMock()

        await manager.connect(ws1, result_id)
        await manager.connect(ws2, result_id)

        message = {"type": "test", "data": "broadcast"}

        # ACT
        await manager.broadcast_to_result(message, result_id)

        # ASSERT
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_send_progress_update(self, manager: ConnectionManager, mock_websocket, mocker):
        """Test sending progress update."""
        # ARRANGE
        result_id = "test_result_id"
        mock_websocket.accept = mocker.AsyncMock()
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
    async def test_send_log_message(self, manager: ConnectionManager, mock_websocket, mocker):
        """Test sending log message."""
        # ARRANGE
        result_id = "test_result_id"
        mock_websocket.accept = mocker.AsyncMock()
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
    async def test_send_metrics_update(self, manager: ConnectionManager, mock_websocket, mocker):
        """Test sending metrics update."""
        # ARRANGE
        result_id = "test_result_id"
        mock_websocket.accept = mocker.AsyncMock()
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
    async def test_send_completion(self, manager: ConnectionManager, mock_websocket, mocker):
        """Test sending completion notification."""
        # ARRANGE
        result_id = "test_result_id"
        mock_websocket.accept = mocker.AsyncMock()
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
    async def test_multiple_connections_same_result(self, manager: ConnectionManager, mocker):
        """Test multiple connections to the same result."""
        # ARRANGE
        result_id = "test_result_id"
        ws1 = mocker.Mock()
        ws1.accept = mocker.AsyncMock()
        ws2 = mocker.Mock()
        ws2.accept = mocker.AsyncMock()

        # ACT
        await manager.connect(ws1, result_id)
        await manager.connect(ws2, result_id)

        # ASSERT
        assert manager.get_connection_count(result_id) == 2

    @pytest.mark.asyncio
    async def test_connection_cleanup(self, manager: ConnectionManager, mock_websocket, mocker):
        """Test connection cleanup after disconnect."""
        # ARRANGE
        result_id = "test_result_id"
        mock_websocket.accept = mocker.AsyncMock()
        await manager.connect(mock_websocket, result_id)

        # ACT
        await manager.disconnect(mock_websocket, result_id)

        # ASSERT
        assert manager.get_connection_count(result_id) == 0
        assert result_id not in manager.active_connections

    @pytest.mark.asyncio
    async def test_broadcast_handles_failed_connections(self, manager: ConnectionManager, mocker):
        """Test broadcast handles failed connections gracefully."""
        # ARRANGE
        result_id = "test_result_id"
        ws_good = mocker.Mock()
        ws_good.send_json = mocker.AsyncMock()
        ws_good.accept = mocker.AsyncMock()
        ws_bad = mocker.Mock()
        ws_bad.send_json = mocker.AsyncMock(side_effect=Exception("Connection failed"))
        ws_bad.accept = mocker.AsyncMock()

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


class TestConnectionManagerErrorHandling:
    """Test error handling in ConnectionManager."""

    @pytest.fixture
    def manager(self):
        """Create a ConnectionManager instance for testing."""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_send_personal_message_with_failed_connection(self, manager: ConnectionManager, mocker):
        """Test send_personal_message handles connection errors gracefully."""
        # ARRANGE
        ws = mocker.Mock()
        ws.send_json = mocker.AsyncMock(side_effect=Exception("Connection closed"))
        message = {"type": "test", "data": "message"}

        # ACT - Should not raise exception
        await manager.send_personal_message(message, ws)

        # ASSERT
        ws.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_nonexistent_result(self, manager: ConnectionManager):
        """Test broadcasting to nonexistent result_id."""
        # ARRANGE
        message = {"type": "test", "data": "broadcast"}

        # ACT - Should not raise exception
        await manager.broadcast_to_result(message, "nonexistent_id")

        # ASSERT - Should complete without error
        assert "nonexistent_id" not in manager.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_connection(self, manager: ConnectionManager, mocker):
        """Test disconnecting a connection that doesn't exist."""
        # ARRANGE
        ws = mocker.Mock()
        result_id = "test_result_id"

        # ACT - Should not raise exception
        await manager.disconnect(ws, result_id)

        # ASSERT
        assert result_id not in manager.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_from_nonexistent_result(self, manager: ConnectionManager, mocker):
        """Test disconnecting from a result_id that has no connections."""
        # ARRANGE
        ws = mocker.Mock()
        ws.accept = mocker.AsyncMock()
        await manager.connect(ws, "result_1")

        # ACT - Disconnect from different result_id
        await manager.disconnect(ws, "result_2")

        # ASSERT - Original connection should still exist
        assert manager.get_connection_count("result_1") == 1
        assert manager.get_connection_count("result_2") == 0

    @pytest.mark.asyncio
    async def test_multiple_disconnects_same_connection(self, manager: ConnectionManager, mocker):
        """Test disconnecting the same connection multiple times."""
        # ARRANGE
        ws = mocker.Mock()
        ws.accept = mocker.AsyncMock()
        result_id = "test_result_id"
        await manager.connect(ws, result_id)

        # ACT
        await manager.disconnect(ws, result_id)
        await manager.disconnect(ws, result_id)  # Second disconnect

        # ASSERT - Should handle gracefully
        assert manager.get_connection_count(result_id) == 0

    @pytest.mark.asyncio
    async def test_broadcast_with_all_failed_connections(self, manager: ConnectionManager, mocker):
        """Test broadcast when all connections fail."""
        # ARRANGE
        result_id = "test_result_id"
        ws1 = mocker.Mock()
        ws1.send_json = mocker.AsyncMock(side_effect=Exception("Connection 1 failed"))
        ws1.accept = mocker.AsyncMock()
        ws2 = mocker.Mock()
        ws2.send_json = mocker.AsyncMock(side_effect=Exception("Connection 2 failed"))
        ws2.accept = mocker.AsyncMock()

        await manager.connect(ws1, result_id)
        await manager.connect(ws2, result_id)

        message = {"type": "test", "data": "broadcast"}

        # ACT
        await manager.broadcast_to_result(message, result_id)

        # ASSERT - All connections should be cleaned up
        assert manager.get_connection_count(result_id) == 0

    @pytest.mark.asyncio
    async def test_concurrent_connect_disconnect(self, manager: ConnectionManager, mocker):
        """Test concurrent connection and disconnection operations."""
        # ARRANGE
        import asyncio
        result_id = "test_result_id"
        connections = []

        for i in range(5):
            ws = mocker.Mock()
            ws.accept = mocker.AsyncMock()
            connections.append(ws)

        # ACT - Connect all concurrently
        await asyncio.gather(*[
            manager.connect(ws, result_id) for ws in connections
        ])

        # ASSERT
        assert manager.get_connection_count(result_id) == 5

        # ACT - Disconnect all concurrently
        await asyncio.gather(*[
            manager.disconnect(ws, result_id) for ws in connections
        ])

        # ASSERT
        assert manager.get_connection_count(result_id) == 0

    @pytest.mark.asyncio
    async def test_send_progress_update_with_no_connections(self, manager: ConnectionManager):
        """Test sending progress update when no connections exist."""
        # ACT - Should not raise exception
        await manager.send_progress_update(
            result_id="nonexistent_id",
            percentage=50.0,
            current_step=5,
            total_steps=10,
            message="Test"
        )

        # ASSERT - Should complete without error
        assert manager.get_connection_count("nonexistent_id") == 0

    @pytest.mark.asyncio
    async def test_send_log_message_with_no_connections(self, manager: ConnectionManager):
        """Test sending log message when no connections exist."""
        # ACT - Should not raise exception
        await manager.send_log_message(
            result_id="nonexistent_id",
            level="INFO",
            message="Test log"
        )

        # ASSERT - Should complete without error
        assert manager.get_connection_count("nonexistent_id") == 0

    @pytest.mark.asyncio
    async def test_send_metrics_update_with_no_connections(self, manager: ConnectionManager):
        """Test sending metrics update when no connections exist."""
        # ACT - Should not raise exception
        await manager.send_metrics_update(
            result_id="nonexistent_id",
            metrics={"return": 0.15}
        )

        # ASSERT - Should complete without error
        assert manager.get_connection_count("nonexistent_id") == 0

    @pytest.mark.asyncio
    async def test_send_completion_with_no_connections(self, manager: ConnectionManager):
        """Test sending completion when no connections exist."""
        # ACT - Should not raise exception
        await manager.send_completion(
            result_id="nonexistent_id",
            status="COMPLETED"
        )

        # ASSERT - Should complete without error
        assert manager.get_connection_count("nonexistent_id") == 0

    @pytest.mark.asyncio
    async def test_broadcast_partial_connection_failure(self, manager: ConnectionManager, mocker):
        """Test broadcast with some connections failing mid-transmission."""
        # ARRANGE
        result_id = "test_result_id"
        ws1 = mocker.Mock()
        ws1.send_json = mocker.AsyncMock()
        ws1.accept = mocker.AsyncMock()
        ws2 = mocker.Mock()
        ws2.send_json = mocker.AsyncMock(side_effect=RuntimeError("Network error"))
        ws2.accept = mocker.AsyncMock()
        ws3 = mocker.Mock()
        ws3.send_json = mocker.AsyncMock()
        ws3.accept = mocker.AsyncMock()

        await manager.connect(ws1, result_id)
        await manager.connect(ws2, result_id)
        await manager.connect(ws3, result_id)

        message = {"type": "test", "data": "broadcast"}

        # ACT
        await manager.broadcast_to_result(message, result_id)

        # ASSERT
        # Good connections should receive message
        ws1.send_json.assert_called_once_with(message)
        ws3.send_json.assert_called_once_with(message)
        # Failed connection should be cleaned up
        assert manager.get_connection_count(result_id) == 2

    def test_get_connection_count_for_nonexistent_result(self, manager: ConnectionManager):
        """Test getting connection count for nonexistent result."""
        # ACT
        count = manager.get_connection_count("nonexistent_id")

        # ASSERT
        assert count == 0

    @pytest.mark.asyncio
    async def test_connection_manager_isolation_between_results(self, manager: ConnectionManager, mocker):
        """Test that connections are properly isolated between different result_ids."""
        # ARRANGE
        ws1 = mocker.Mock()
        ws1.accept = mocker.AsyncMock()
        ws1.send_json = mocker.AsyncMock()
        ws2 = mocker.Mock()
        ws2.accept = mocker.AsyncMock()
        ws2.send_json = mocker.AsyncMock()

        # ACT - Connect to different results
        await manager.connect(ws1, "result_1")
        await manager.connect(ws2, "result_2")

        # Broadcast to result_1 only
        message = {"type": "test", "data": "message"}
        await manager.broadcast_to_result(message, "result_1")

        # ASSERT
        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_not_called()  # Should not receive message

    @pytest.mark.asyncio
    async def test_send_error_with_failed_connection(self, manager: ConnectionManager, mocker):
        """Test send_error handles connection failures gracefully."""
        # ARRANGE
        ws = mocker.Mock()
        ws.send_json = mocker.AsyncMock(side_effect=Exception("Connection closed"))

        # ACT - Should not raise exception
        await manager.send_error(ws, "Test error", "ERROR_CODE")

        # ASSERT
        ws.send_json.assert_called_once()
