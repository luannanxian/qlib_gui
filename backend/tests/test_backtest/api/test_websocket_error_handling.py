"""
WebSocket API Error Handling Tests

Comprehensive error handling tests for WebSocket API endpoints using mocking
to inject errors at different layers (repository, connection, timeout).
"""

import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from fastapi import WebSocket, WebSocketDisconnect
from httpx import AsyncClient
import asyncio

from app.modules.backtest.websocket.connection_manager import manager


class TestWebSocketAPIErrorHandling:
    """Test error handling in WebSocket API endpoints."""

    @pytest.mark.asyncio
    async def test_websocket_database_error_during_verification(self, async_client: AsyncClient, mocker):
        """Test WebSocket handles database errors during result verification."""
        # ARRANGE
        with patch('app.modules.backtest.api.websocket_api.BacktestRepository') as mock_repo:
            mock_repo_instance = mock_repo.return_value
            mock_repo_instance.get_result_by_id = AsyncMock(
                side_effect=SQLAlchemyError("Database connection error")
            )

            # Create mock websocket
            mock_ws = MagicMock(spec=WebSocket)
            mock_ws.accept = AsyncMock()
            mock_ws.close = AsyncMock()

            # Mock manager's send_error
            with patch.object(manager, 'send_error', new_callable=AsyncMock) as mock_send_error:
                # Import the endpoint function
                from app.modules.backtest.api.websocket_api import websocket_endpoint

                # ACT
                await websocket_endpoint(
                    websocket=mock_ws,
                    result_id="test_result_id",
                    log_level="INFO",
                    db=None  # Will be mocked
                )

                # ASSERT
                mock_ws.accept.assert_called_once()
                mock_send_error.assert_called_once()
                # Check error message contains verification error
                call_args = mock_send_error.call_args
                assert "Error verifying result" in call_args[0][1]
                assert call_args[0][2] == "VERIFICATION_ERROR"
                mock_ws.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_result_not_found_error(self, async_client: AsyncClient, mocker):
        """Test WebSocket handles result not found error."""
        # ARRANGE
        with patch('app.modules.backtest.api.websocket_api.BacktestRepository') as mock_repo:
            mock_repo_instance = mock_repo.return_value
            mock_repo_instance.get_result_by_id = AsyncMock(return_value=None)

            mock_ws = MagicMock(spec=WebSocket)
            mock_ws.accept = AsyncMock()
            mock_ws.close = AsyncMock()

            with patch.object(manager, 'send_error', new_callable=AsyncMock) as mock_send_error:
                from app.modules.backtest.api.websocket_api import websocket_endpoint

                # ACT
                await websocket_endpoint(
                    websocket=mock_ws,
                    result_id="nonexistent_id",
                    log_level="INFO",
                    db=None
                )

                # ASSERT
                mock_ws.accept.assert_called_once()
                mock_send_error.assert_called_once()
                call_args = mock_send_error.call_args
                assert "not found" in call_args[0][1]
                assert call_args[0][2] == "NOT_FOUND"
                mock_ws.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_handles_disconnect_gracefully(self, mocker):
        """Test WebSocket handles client disconnect gracefully."""
        # ARRANGE
        with patch('app.modules.backtest.api.websocket_api.BacktestRepository') as mock_repo:
            mock_repo_instance = mock_repo.return_value

            # Create mock result
            mock_result = MagicMock()
            mock_result.status = "RUNNING"
            mock_repo_instance.get_result_by_id = AsyncMock(return_value=mock_result)

            mock_ws = MagicMock(spec=WebSocket)
            mock_ws.accept = AsyncMock()

            # Simulate WebSocketDisconnect after initial message
            with patch.object(manager, 'connect', new_callable=AsyncMock):
                with patch.object(manager, 'send_personal_message', new_callable=AsyncMock):
                    # Make receive_text raise WebSocketDisconnect
                    mock_ws.receive_text = AsyncMock(side_effect=WebSocketDisconnect(code=1000))

                    with patch.object(manager, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
                        from app.modules.backtest.api.websocket_api import websocket_endpoint

                        # ACT
                        await websocket_endpoint(
                            websocket=mock_ws,
                            result_id="test_result_id",
                            log_level="INFO",
                            db=None
                        )

                        # ASSERT - disconnect should be called
                        mock_disconnect.assert_called_once_with(mock_ws, "test_result_id")

    @pytest.mark.asyncio
    async def test_websocket_handles_unexpected_exception(self, mocker):
        """Test WebSocket handles unexpected exceptions gracefully."""
        # ARRANGE
        with patch('app.modules.backtest.api.websocket_api.BacktestRepository') as mock_repo:
            mock_repo_instance = mock_repo.return_value
            mock_result = MagicMock()
            mock_result.status = "RUNNING"
            mock_repo_instance.get_result_by_id = AsyncMock(return_value=mock_result)

            mock_ws = MagicMock(spec=WebSocket)
            mock_ws.accept = AsyncMock()

            with patch.object(manager, 'connect', new_callable=AsyncMock):
                with patch.object(manager, 'send_personal_message', new_callable=AsyncMock):
                    # Make receive_text raise unexpected exception
                    mock_ws.receive_text = AsyncMock(side_effect=RuntimeError("Unexpected error"))

                    with patch.object(manager, 'send_error', new_callable=AsyncMock) as mock_send_error:
                        with patch.object(manager, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
                            from app.modules.backtest.api.websocket_api import websocket_endpoint

                            # ACT
                            await websocket_endpoint(
                                websocket=mock_ws,
                                result_id="test_result_id",
                                log_level="INFO",
                                db=None
                            )

                            # ASSERT
                            mock_send_error.assert_called_once()
                            call_args = mock_send_error.call_args
                            assert "WebSocket error" in call_args[0][1]
                            assert call_args[0][2] == "WEBSOCKET_ERROR"
                            mock_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_timeout_sends_keepalive(self, mocker):
        """Test WebSocket sends keepalive ping on timeout."""
        # ARRANGE
        with patch('app.modules.backtest.api.websocket_api.BacktestRepository') as mock_repo:
            mock_repo_instance = mock_repo.return_value
            mock_result = MagicMock()
            mock_result.status = "RUNNING"
            mock_repo_instance.get_result_by_id = AsyncMock(return_value=mock_result)

            mock_ws = MagicMock(spec=WebSocket)
            mock_ws.accept = AsyncMock()

            with patch.object(manager, 'connect', new_callable=AsyncMock):
                with patch.object(manager, 'send_personal_message', new_callable=AsyncMock) as mock_send:
                    # First timeout, then disconnect
                    timeout_count = [0]

                    async def mock_receive_text():
                        timeout_count[0] += 1
                        if timeout_count[0] == 1:
                            raise asyncio.TimeoutError()
                        else:
                            raise WebSocketDisconnect(code=1000)

                    mock_ws.receive_text = mock_receive_text

                    with patch.object(manager, 'disconnect', new_callable=AsyncMock):
                        from app.modules.backtest.api.websocket_api import websocket_endpoint

                        # ACT
                        await websocket_endpoint(
                            websocket=mock_ws,
                            result_id="test_result_id",
                            log_level="INFO",
                            db=None
                        )

                        # ASSERT - Should send keepalive ping and initial connection message
                        assert mock_send.call_count >= 2
                        # Check that ping was sent (should be in the calls)
                        calls = mock_send.call_args_list
                        ping_sent = any(call[0][0].get("type") == "ping" for call in calls if len(call[0]) > 0)
                        assert ping_sent

    @pytest.mark.asyncio
    async def test_websocket_ping_pong_handling(self, mocker):
        """Test WebSocket responds to ping with pong."""
        # ARRANGE
        with patch('app.modules.backtest.api.websocket_api.BacktestRepository') as mock_repo:
            mock_repo_instance = mock_repo.return_value
            mock_result = MagicMock()
            mock_result.status = "RUNNING"
            mock_repo_instance.get_result_by_id = AsyncMock(return_value=mock_result)

            mock_ws = MagicMock(spec=WebSocket)
            mock_ws.accept = AsyncMock()

            with patch.object(manager, 'connect', new_callable=AsyncMock):
                with patch.object(manager, 'send_personal_message', new_callable=AsyncMock) as mock_send:
                    # Simulate receiving ping then disconnect
                    message_count = [0]

                    async def mock_receive_text():
                        message_count[0] += 1
                        if message_count[0] == 1:
                            return "ping"
                        else:
                            raise WebSocketDisconnect(code=1000)

                    mock_ws.receive_text = mock_receive_text

                    with patch.object(manager, 'disconnect', new_callable=AsyncMock):
                        from app.modules.backtest.api.websocket_api import websocket_endpoint

                        # ACT
                        await websocket_endpoint(
                            websocket=mock_ws,
                            result_id="test_result_id",
                            log_level="INFO",
                            db=None
                        )

                        # ASSERT - Should send pong response
                        calls = mock_send.call_args_list
                        pong_sent = any(
                            call[0][0].get("type") == "pong"
                            for call in calls
                            if len(call[0]) > 0 and isinstance(call[0][0], dict)
                        )
                        assert pong_sent


class TestWebSocketAPIEdgeCases:
    """Test edge cases in WebSocket API."""

    @pytest.mark.asyncio
    async def test_websocket_with_empty_result_id(self, mocker):
        """Test WebSocket handles empty result_id."""
        # ARRANGE
        with patch('app.modules.backtest.api.websocket_api.BacktestRepository') as mock_repo:
            mock_repo_instance = mock_repo.return_value
            mock_repo_instance.get_result_by_id = AsyncMock(return_value=None)

            mock_ws = MagicMock(spec=WebSocket)
            mock_ws.accept = AsyncMock()
            mock_ws.close = AsyncMock()

            with patch.object(manager, 'send_error', new_callable=AsyncMock) as mock_send_error:
                from app.modules.backtest.api.websocket_api import websocket_endpoint

                # ACT
                await websocket_endpoint(
                    websocket=mock_ws,
                    result_id="",  # Empty result ID
                    log_level="INFO",
                    db=None
                )

                # ASSERT
                mock_send_error.assert_called_once()
                mock_ws.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_websocket_with_different_log_levels(self, mocker):
        """Test WebSocket accepts different log levels."""
        # ARRANGE
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]

        for log_level in log_levels:
            with patch('app.modules.backtest.api.websocket_api.BacktestRepository') as mock_repo:
                mock_repo_instance = mock_repo.return_value
                mock_result = MagicMock()
                mock_result.status = "COMPLETED"
                mock_repo_instance.get_result_by_id = AsyncMock(return_value=mock_result)

                mock_ws = MagicMock(spec=WebSocket)
                mock_ws.accept = AsyncMock()
                mock_ws.receive_text = AsyncMock(side_effect=WebSocketDisconnect(code=1000))

                with patch.object(manager, 'connect', new_callable=AsyncMock):
                    with patch.object(manager, 'send_personal_message', new_callable=AsyncMock):
                        with patch.object(manager, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
                            from app.modules.backtest.api.websocket_api import websocket_endpoint

                            # ACT - Should not raise exception
                            await websocket_endpoint(
                                websocket=mock_ws,
                                result_id="test_result_id",
                                log_level=log_level,
                                db=None
                            )

                            # ASSERT - Should complete without error (disconnect should be called)
                            mock_disconnect.assert_called_once_with(mock_ws, "test_result_id")

    @pytest.mark.asyncio
    async def test_websocket_connection_after_manager_error(self, mocker):
        """Test WebSocket handles manager.connect errors."""
        # ARRANGE
        with patch('app.modules.backtest.api.websocket_api.BacktestRepository') as mock_repo:
            mock_repo_instance = mock_repo.return_value
            mock_result = MagicMock()
            mock_result.status = "RUNNING"
            mock_repo_instance.get_result_by_id = AsyncMock(return_value=mock_result)

            mock_ws = MagicMock(spec=WebSocket)
            mock_ws.accept = AsyncMock()

            # Make manager.connect raise exception
            with patch.object(manager, 'connect', new_callable=AsyncMock, side_effect=RuntimeError("Connection error")):
                with patch.object(manager, 'send_error', new_callable=AsyncMock) as mock_send_error:
                    with patch.object(manager, 'disconnect', new_callable=AsyncMock):
                        from app.modules.backtest.api.websocket_api import websocket_endpoint

                        # ACT - Should raise exception (not caught in this case)
                        with pytest.raises(RuntimeError):
                            await websocket_endpoint(
                                websocket=mock_ws,
                                result_id="test_result_id",
                                log_level="INFO",
                                db=None
                            )

    @pytest.mark.asyncio
    async def test_websocket_send_personal_message_error(self, mocker):
        """Test WebSocket handles send_personal_message errors."""
        # ARRANGE
        with patch('app.modules.backtest.api.websocket_api.BacktestRepository') as mock_repo:
            mock_repo_instance = mock_repo.return_value
            mock_result = MagicMock()
            mock_result.status = "RUNNING"
            mock_repo_instance.get_result_by_id = AsyncMock(return_value=mock_result)

            mock_ws = MagicMock(spec=WebSocket)
            mock_ws.accept = AsyncMock()

            with patch.object(manager, 'connect', new_callable=AsyncMock):
                # Make send_personal_message raise exception
                with patch.object(manager, 'send_personal_message', new_callable=AsyncMock, side_effect=RuntimeError("Send error")):
                    mock_ws.receive_text = AsyncMock(side_effect=WebSocketDisconnect(code=1000))

                    with patch.object(manager, 'send_error', new_callable=AsyncMock):
                        with patch.object(manager, 'disconnect', new_callable=AsyncMock):
                            from app.modules.backtest.api.websocket_api import websocket_endpoint

                            # ACT - Should handle error gracefully
                            await websocket_endpoint(
                                websocket=mock_ws,
                                result_id="test_result_id",
                                log_level="INFO",
                                db=None
                            )

                            # Test completes without raising exception
