"""
ws.py – WebSocket connection manager.

Manages a pool of active WebSocket connections and broadcasts
StoredEvent payloads to every connected client in real-time.

Usage (inside a FastAPI route):
    from gateway.ws import manager

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket):
        await manager.connect(ws)
        try:
            while True:
                await ws.receive_text()  # keep-alive ping
        except WebSocketDisconnect:
            manager.disconnect(ws)
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect  # noqa: F401 (re-exported)

log = logging.getLogger(__name__)


class ConnectionManager:
    """Thread-safe (asyncio-safe) WebSocket broadcast pool."""

    def __init__(self) -> None:
        self._active: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._active.append(websocket)
        log.info("WS client connected  (total=%d)", len(self._active))

    def disconnect(self, websocket: WebSocket) -> None:
        try:
            self._active.remove(websocket)
        except ValueError:
            pass
        log.info("WS client disconnected (total=%d)", len(self._active))

    async def broadcast(self, event_type: str, payload: dict[str, Any]) -> None:
        """Send a JSON message to every connected client.

        Clients that fail to receive the message are silently removed.
        """
        message = json.dumps({"event": event_type, "data": payload})
        dead: list[WebSocket] = []
        async with self._lock:
            targets = list(self._active)

        for ws in targets:
            try:
                await ws.send_text(message)
            except Exception as exc:  # noqa: BLE001
                log.warning("WS send failed (%s) – removing client", exc)
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._active.remove(ws)


# Singleton shared across the app
manager = ConnectionManager()
