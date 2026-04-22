"""
WebSocket handler for real-time secure messaging.
"""

import json
import asyncio
from typing import Dict, Set, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.routing import APIRouter
from jose import jwt, JWTError

from .secure_messaging import SecureMessaging
from auth.dependencies import SECRET_KEY, ALGORITHM

# WebSocket router
websocket_router = APIRouter()

# Connection manager for WebSocket connections
class ConnectionManager:
    """Manages WebSocket connections for real-time messaging."""
    
    def __init__(self):
        # user_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # websocket -> user_id mapping
        self.connection_users: Dict[WebSocket, str] = {}
        # User presence status
        self.user_presence: Dict[str, dict] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept new WebSocket connection."""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        self.connection_users[websocket] = user_id
        
        # Update user presence
        self.user_presence[user_id] = {
            "status": "online",
            "last_seen": datetime.now().isoformat(),
            "connections": len(self.active_connections[user_id])
        }
        
        # Notify other users about presence change
        await self.broadcast_presence_update(user_id)
    
    def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection."""
        if websocket in self.connection_users:
            user_id = self.connection_users[websocket]
            
            # Remove connection
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                
                # If no more connections, mark as offline
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    self.user_presence[user_id] = {
                        "status": "offline",
                        "last_seen": datetime.now().isoformat(),
                        "connections": 0
                    }
                else:
                    # Update connection count
                    self.user_presence[user_id]["connections"] = len(self.active_connections[user_id])
            
            del self.connection_users[websocket]
            
            # Notify about presence change
            asyncio.create_task(self.broadcast_presence_update(user_id))
    
    async def send_personal_message(self, message: dict, user_id: str):
        """Send message to a specific user."""
        if user_id in self.active_connections:
            disconnected = set()
            
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(json.dumps(message))
                except:
                    disconnected.add(websocket)
            
            # Clean up disconnected websockets
            for ws in disconnected:
                self.active_connections[user_id].discard(ws)
                if ws in self.connection_users:
                    del self.connection_users[ws]
    
    async def broadcast_presence_update(self, user_id: str):
        """Broadcast user presence update to all connected users."""
        if user_id not in self.user_presence:
            return
        
        presence_message = {
            "type": "presence_update",
            "user_id": user_id,
            "presence": self.user_presence[user_id],
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all connected users
        for connected_user_id in self.active_connections:
            if connected_user_id != user_id:  # Don't send to the user themselves
                await self.send_personal_message(presence_message, connected_user_id)
    
    async def notify_new_message(self, sender_id: str, receiver_id: str, message_info: dict):
        """Notify receiver about new message."""
        notification = {
            "type": "new_message",
            "sender_id": sender_id,
            "message_id": message_info["message_id"],
            "message_type": message_info.get("message_type", "text"),
            "filename": message_info.get("filename"),
            "timestamp": message_info["timestamp"]
        }
        
        await self.send_personal_message(notification, receiver_id)
    
    async def notify_message_status(self, user_id: str, message_id: str, status: str):
        """Notify about message status change (delivered, read, etc.)."""
        status_update = {
            "type": "message_status",
            "message_id": message_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.send_personal_message(status_update, user_id)
    
    def get_user_presence(self, user_id: str) -> Optional[dict]:
        """Get presence information for a user."""
        return self.user_presence.get(user_id)
    
    def get_online_users(self) -> list:
        """Get list of online users."""
        return [
            {"user_id": user_id, "presence": presence}
            for user_id, presence in self.user_presence.items()
            if presence["status"] == "online"
        ]


# Global connection manager
manager = ConnectionManager()

# Initialize messaging system
messaging = SecureMessaging()


async def get_user_from_token(websocket: WebSocket, token: str) -> Optional[str]:
    """Extract user ID from JWT token for WebSocket authentication."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        return user_id
    except JWTError:
        await websocket.close(code=4001, reason="Invalid token")
        return None


@websocket_router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for real-time messaging.
    
    Clients connect with JWT token for authentication.
    """
    # Authenticate user
    user_id = await get_user_from_token(websocket, token)
    if not user_id:
        return
    
    # Connect user
    await manager.connect(websocket, user_id)
    
    try:
        # Send initial presence information
        online_users = manager.get_online_users()
        await websocket.send_text(json.dumps({
            "type": "initial_presence",
            "online_users": online_users,
            "your_user_id": user_id
        }))
        
        # Listen for messages
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle different message types
                await handle_websocket_message(websocket, user_id, message_data)
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error", 
                    "message": f"Error processing message: {str(e)}"
                }))
    
    finally:
        manager.disconnect(websocket)


async def handle_websocket_message(websocket: WebSocket, user_id: str, message_data: dict):
    """Handle incoming WebSocket messages."""
    
    message_type = message_data.get("type")
    
    if message_type == "typing_start":
        # Notify receiver that user is typing
        receiver_id = message_data.get("receiver_id")
        if receiver_id:
            await manager.send_personal_message({
                "type": "typing_start",
                "sender_id": user_id,
                "timestamp": datetime.now().isoformat()
            }, receiver_id)
    
    elif message_type == "typing_stop":
        # Notify receiver that user stopped typing
        receiver_id = message_data.get("receiver_id")
        if receiver_id:
            await manager.send_personal_message({
                "type": "typing_stop",
                "sender_id": user_id,
                "timestamp": datetime.now().isoformat()
            }, receiver_id)
    
    elif message_type == "mark_read":
        # Mark message as read
        message_id = message_data.get("message_id")
        if message_id:
            try:
                # Here you would update the message status in database
                # For now, just notify the sender
                await manager.notify_message_status(user_id, message_id, "read")
                
                await websocket.send_text(json.dumps({
                    "type": "message_marked_read",
                    "message_id": message_id,
                    "timestamp": datetime.now().isoformat()
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Failed to mark message as read: {str(e)}"
                }))
    
    elif message_type == "get_presence":
        # Get presence for specific user
        target_user_id = message_data.get("user_id")
        if target_user_id:
            presence = manager.get_user_presence(target_user_id)
            await websocket.send_text(json.dumps({
                "type": "presence_info",
                "user_id": target_user_id,
                "presence": presence,
                "timestamp": datetime.now().isoformat()
            }))
    
    elif message_type == "get_online_users":
        # Get list of online users
        online_users = manager.get_online_users()
        await websocket.send_text(json.dumps({
            "type": "online_users",
            "users": online_users,
            "timestamp": datetime.now().isoformat()
        }))
    
    elif message_type == "ping":
        # Heartbeat/keepalive
        await websocket.send_text(json.dumps({
            "type": "pong",
            "timestamp": datetime.now().isoformat()
        }))
    
    else:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }))


# Message notification functions for use by messaging API
async def notify_new_message_via_websocket(sender_id: str, receiver_id: str, message_info: dict):
    """Called by messaging API to notify about new messages."""
    await manager.notify_new_message(sender_id, receiver_id, message_info)


async def notify_message_delivered(sender_id: str, message_id: str):
    """Notify sender that message was delivered."""
    await manager.notify_message_status(sender_id, message_id, "delivered")


async def notify_message_read(sender_id: str, message_id: str):
    """Notify sender that message was read."""
    await manager.notify_message_status(sender_id, message_id, "read")


# Health check for WebSocket connections
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "total_connections": sum(len(connections) for connections in manager.active_connections.values()),
        "unique_users": len(manager.active_connections),
        "online_users": len([p for p in manager.user_presence.values() if p["status"] == "online"]),
        "presence_data": manager.user_presence
    }
