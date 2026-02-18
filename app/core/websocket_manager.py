"""
WebSocket connection manager.
Tracks active connections by user_id for real-time messaging.
"""
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        total = sum(len(v) for v in self.active_connections.values())
        logger.info(f"WS connected: user_id={user_id}, total_connections={total}")

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logger.info(f"WS disconnected: user_id={user_id}")

    def is_online(self, user_id: int) -> bool:
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

    async def send_to_user(self, user_id: int, message: dict):
        """Send a JSON message to all connections of a user."""
        connections = self.active_connections.get(user_id, set())
        dead = []
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            connections.discard(ws)


manager = ConnectionManager()
