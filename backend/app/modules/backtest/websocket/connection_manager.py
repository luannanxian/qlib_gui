"""
WebSocket Connection Manager

Manages WebSocket connections for real-time backtest progress updates.
"""

from typing import Dict, Set
from fastapi import WebSocket
import asyncio
import json
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections for backtest progress updates."""

    def __init__(self):
        # Map of result_id to set of active connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, result_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()

        async with self._lock:
            if result_id not in self.active_connections:
                self.active_connections[result_id] = set()
            self.active_connections[result_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, result_id: str):
        """Remove a WebSocket connection."""
        async with self._lock:
            if result_id in self.active_connections:
                self.active_connections[result_id].discard(websocket)
                # Clean up empty sets
                if not self.active_connections[result_id]:
                    del self.active_connections[result_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            # Connection might be closed
            pass

    async def broadcast_to_result(self, message: dict, result_id: str):
        """Broadcast a message to all connections watching a specific result."""
        async with self._lock:
            if result_id in self.active_connections:
                # Create a copy to avoid modification during iteration
                connections = self.active_connections[result_id].copy()

        # Send to all connections (outside the lock to avoid blocking)
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Mark for removal if send fails
                disconnected.append(connection)

        # Clean up disconnected connections
        if disconnected:
            async with self._lock:
                if result_id in self.active_connections:
                    for conn in disconnected:
                        self.active_connections[result_id].discard(conn)

    async def send_progress_update(
        self,
        result_id: str,
        percentage: float,
        current_step: int,
        total_steps: int,
        message: str = ""
    ):
        """Send progress update to all connections watching a result."""
        await self.broadcast_to_result({
            "type": "progress",
            "percentage": percentage,
            "current_step": current_step,
            "total_steps": total_steps,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }, result_id)

    async def send_log_message(
        self,
        result_id: str,
        level: str,
        message: str
    ):
        """Send log message to all connections watching a result."""
        await self.broadcast_to_result({
            "type": "log",
            "level": level,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }, result_id)

    async def send_metrics_update(
        self,
        result_id: str,
        metrics: dict
    ):
        """Send metrics update to all connections watching a result."""
        await self.broadcast_to_result({
            "type": "metrics",
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }, result_id)

    async def send_completion(
        self,
        result_id: str,
        status: str
    ):
        """Send completion notification to all connections watching a result."""
        await self.broadcast_to_result({
            "type": "completion",
            "status": status,
            "result_id": result_id,
            "timestamp": datetime.utcnow().isoformat()
        }, result_id)

    async def send_error(
        self,
        websocket: WebSocket,
        message: str,
        code: str = "ERROR"
    ):
        """Send error message to a specific connection."""
        await self.send_personal_message({
            "type": "error",
            "message": message,
            "code": code,
            "timestamp": datetime.utcnow().isoformat()
        }, websocket)

    def get_connection_count(self, result_id: str) -> int:
        """Get the number of active connections for a result."""
        return len(self.active_connections.get(result_id, set()))


# Global connection manager instance
manager = ConnectionManager()
