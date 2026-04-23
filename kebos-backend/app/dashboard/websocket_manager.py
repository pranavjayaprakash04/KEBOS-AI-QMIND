import asyncio, logging, json
from collections import defaultdict
from fastapi import WebSocket
from uuid import UUID

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Manages WebSocket connections per tenant.
    Allows broadcasting threat updates to all connected analysts.
    """
    def __init__(self):
        # tenant_id (str) -> list of active WebSocket connections
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, tenant_id: str):
        await websocket.accept()
        self._connections[tenant_id].append(websocket)
        logger.info(f"WebSocket connected: tenant={tenant_id}, "
                    f"total_connections={len(self._connections[tenant_id])}")

    def disconnect(self, websocket: WebSocket, tenant_id: str):
        conns = self._connections.get(tenant_id, [])
        if websocket in conns:
            conns.remove(websocket)
        logger.info(f"WebSocket disconnected: tenant={tenant_id}")

    async def broadcast_to_tenant(self, tenant_id: str, data: dict):
        """Send a JSON message to all analyst dashboards for a tenant."""
        message = json.dumps(data)
        dead = []
        for ws in self._connections.get(str(tenant_id), []):
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.warning(f"WebSocket send failed: {e} — marking for removal")
                dead.append(ws)
        # Clean up dead connections
        for ws in dead:
            self.disconnect(ws, str(tenant_id))

# Singleton instance used across the app
websocket_manager = WebSocketManager()
