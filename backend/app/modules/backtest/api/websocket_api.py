"""
WebSocket API for Real-time Backtest Progress

Provides WebSocket endpoints for real-time updates during backtest execution.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import asyncio

from app.database import get_db
from app.database.repositories.backtest_repository import BacktestRepository
from app.modules.backtest.websocket.connection_manager import manager
from app.modules.backtest.exceptions import ResourceNotFoundError

router = APIRouter()


@router.websocket("/ws/backtest/{result_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    result_id: str,
    log_level: Optional[str] = Query(default="INFO"),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time backtest progress updates.

    Args:
        result_id: The backtest result ID to monitor
        log_level: Minimum log level to receive (DEBUG, INFO, WARNING, ERROR)
        db: Database session

    Message Types:
        - progress: Progress updates with percentage and current step
        - log: Log messages with level and message
        - metrics: Real-time metrics updates
        - completion: Backtest completion notification
        - error: Error messages
    """
    repository = BacktestRepository(db)

    # Verify result exists before accepting connection
    try:
        result = await repository.get_result_by_id(result_id)
        if not result:
            await websocket.accept()
            await manager.send_error(
                websocket,
                f"Backtest result {result_id} not found",
                "NOT_FOUND"
            )
            await websocket.close()
            return
    except Exception as e:
        await websocket.accept()
        await manager.send_error(
            websocket,
            f"Error verifying result: {str(e)}",
            "VERIFICATION_ERROR"
        )
        await websocket.close()
        return

    # Accept connection and add to manager
    await manager.connect(websocket, result_id)

    try:
        # Send initial connection confirmation
        await manager.send_personal_message({
            "type": "connected",
            "result_id": result_id,
            "status": result.status
        }, websocket)

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (e.g., ping/pong)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second timeout
                )

                # Handle client messages if needed
                if data == "ping":
                    await manager.send_personal_message({"type": "pong"}, websocket)

            except asyncio.TimeoutError:
                # Send keepalive ping
                await manager.send_personal_message({"type": "ping"}, websocket)

    except WebSocketDisconnect:
        # Client disconnected
        await manager.disconnect(websocket, result_id)
    except Exception as e:
        # Unexpected error
        await manager.send_error(
            websocket,
            f"WebSocket error: {str(e)}",
            "WEBSOCKET_ERROR"
        )
        await manager.disconnect(websocket, result_id)
