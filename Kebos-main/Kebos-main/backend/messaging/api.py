"""
Unified Secure Messaging API

FastAPI routes for the unified secure messaging system with:
- Post-quantum encryption
- Multi-media support
- Real-time WebSocket communication
- Comprehensive storage and retrieval
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Request
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import io
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from .services import UnifiedMessagingService
from .models import (
    MessageCreate, MessageResponse, ChannelCreate, ChannelResponse,
    ChannelMessageHistory, KeypairResponse, MessageType, ChannelType,
    CreateKeypairRequest
)
from auth.dependencies import get_current_user
from common.db import get_async_session
from common.models import UserORM

router = APIRouter(prefix="/messaging", tags=["unified_messaging"])
security = HTTPBearer()


# === DEPENDENCY INJECTION ===

async def get_messaging_service(
    db: AsyncSession = Depends(get_async_session)
) -> UnifiedMessagingService:
    """Get messaging service instance"""
    return UnifiedMessagingService(db)


# === REQUEST/RESPONSE MODELS ===

class SendTextMessageRequest(BaseModel):
    receiver_id: str = Field(..., description="Message recipient user ID")
    content: str = Field(..., max_length=10240, description="Message content")
    channel_id: Optional[str] = Field(None, description="Existing channel ID (optional)")
    auto_delete_hours: Optional[int] = Field(None, ge=1, le=168, description="Auto-delete after hours")


class SendFileMessageRequest(BaseModel):
    receiver_id: str = Field(..., description="Message recipient user ID")
    channel_id: Optional[str] = Field(None, description="Existing channel ID (optional)")
    auto_delete_hours: Optional[int] = Field(None, ge=1, le=168, description="Auto-delete after hours")


class MessageSearchRequest(BaseModel):
    query: Optional[str] = Field(None, description="Search query")
    channel_id: Optional[str] = Field(None, description="Specific channel")
    message_type: Optional[MessageType] = Field(None, description="Message type filter")
    start_date: Optional[datetime] = Field(None, description="Start date filter")
    end_date: Optional[datetime] = Field(None, description="End date filter")
    limit: int = Field(50, ge=1, le=100, description="Results limit")
    offset: int = Field(0, ge=0, description="Results offset")


class ChannelStatsResponse(BaseModel):
    channel_id: str
    total_messages: int
    total_bytes: int
    last_activity: datetime
    active_participants: int


# === KEYPAIR MANAGEMENT ===

@router.post("/keypair", response_model=KeypairResponse)
async def create_keypair(
    current_user = Depends(get_current_user),
    messaging_service: UnifiedMessagingService = Depends(get_messaging_service)
):
    """Create cryptographic keypair for secure messaging"""
    try:
        return await messaging_service.create_user_keypair(current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create keypair: {str(e)}"
        )


@router.get("/keypair", response_model=KeypairResponse)
async def get_keypair(
    current_user = Depends(get_current_user),
    messaging_service: UnifiedMessagingService = Depends(get_messaging_service)
):
    """Get user's public key information"""
    try:
        public_key = await messaging_service.get_user_public_key(current_user.id)
        if not public_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No keypair found for user"
            )
        
        return KeypairResponse(
            user_id=current_user.id,
            public_key=public_key,
            algorithm="Kyber-1024",
            created_at=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get keypair: {str(e)}"
        )


# === CHANNEL MANAGEMENT ===

@router.post("/channels", response_model=ChannelResponse)
async def create_channel(
    channel_data: ChannelCreate,
    current_user = Depends(get_current_user),
    messaging_service: UnifiedMessagingService = Depends(get_messaging_service)
):
    """Create new secure communication channel"""
    try:
        return await messaging_service.create_channel(channel_data, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create channel: {str(e)}"
        )


@router.get("/channels", response_model=List[ChannelResponse])
async def get_user_channels(
    current_user = Depends(get_current_user),
    messaging_service: UnifiedMessagingService = Depends(get_messaging_service)
):
    """Get all channels for the current user"""
    try:
        return await messaging_service.get_user_channels(current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get channels: {str(e)}"
        )


@router.get("/channels/{channel_id}/messages", response_model=ChannelMessageHistory)
async def get_channel_messages(
    channel_id: str,
    limit: int = 50,
    offset: int = 0,
    before: Optional[datetime] = None,
    current_user = Depends(get_current_user),
    messaging_service: UnifiedMessagingService = Depends(get_messaging_service)
):
    """Get message history for a channel"""
    try:
        return await messaging_service.get_channel_messages(
            channel_id, current_user.id, limit, offset, before
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get messages: {str(e)}"
        )


@router.get("/channels/{channel_id}/stats", response_model=ChannelStatsResponse)
async def get_channel_stats(
    channel_id: str,
    current_user = Depends(get_current_user),
    messaging_service: UnifiedMessagingService = Depends(get_messaging_service)
):
    """Get channel statistics"""
    try:
        # This would be implemented in the service
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Channel stats not yet implemented"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get channel stats: {str(e)}"
        )


# === MESSAGE HANDLING ===

@router.post("/messages/text", response_model=MessageResponse)
async def send_text_message(
    message_data: SendTextMessageRequest,
    request: Request,
    current_user = Depends(get_current_user),
    messaging_service: UnifiedMessagingService = Depends(get_messaging_service)
):
    """Send encrypted text message"""
    try:
        message_create = MessageCreate(
            receiver_id=message_data.receiver_id,
            channel_id=message_data.channel_id,
            message_type=MessageType.TEXT,
            content=message_data.content,
            auto_delete_hours=message_data.auto_delete_hours
        )
        
        return await messaging_service.send_message(
            message_create,
            current_user.id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send message: {str(e)}"
        )


@router.post("/messages/file", response_model=MessageResponse)
async def send_file_message(
    file: UploadFile = File(...),
    receiver_id: str = Form(...),
    channel_id: Optional[str] = Form(None),
    auto_delete_hours: Optional[int] = Form(None),
    request: Request = None,
    current_user = Depends(get_current_user),
    messaging_service: UnifiedMessagingService = Depends(get_messaging_service)
):
    """Send encrypted file message"""
    try:
        # Validate file size (50MB limit)
        MAX_FILE_SIZE = 50 * 1024 * 1024
        if file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE} bytes"
            )
        
        # Read file data
        file_data = await file.read()
        
        # Determine message type based on file
        message_type = MessageType.FILE
        if file.content_type:
            if file.content_type.startswith("image/"):
                message_type = MessageType.IMAGE
            elif file.content_type.startswith("audio/"):
                message_type = MessageType.AUDIO
            elif file.content_type.startswith("video/"):
                message_type = MessageType.VIDEO
            elif file.content_type in ["application/pdf", "application/msword", 
                                     "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                message_type = MessageType.DOCUMENT
        
        message_create = MessageCreate(
            receiver_id=receiver_id,
            channel_id=channel_id,
            message_type=message_type,
            filename=file.filename,
            auto_delete_hours=auto_delete_hours
        )
        
        return await messaging_service.send_message(
            message_create,
            current_user.id,
            file_data=file_data,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to send file: {str(e)}"
        )


@router.get("/messages/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: str,
    private_key: str = Form(..., description="User's private key for decryption"),
    current_user = Depends(get_current_user),
    messaging_service: UnifiedMessagingService = Depends(get_messaging_service)
):
    """Get and decrypt a specific message"""
    try:
        message = await messaging_service.get_message(message_id, current_user.id, private_key)
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        return message
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to get message: {str(e)}"
        )


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    current_user = Depends(get_current_user),
    messaging_service: UnifiedMessagingService = Depends(get_messaging_service)
):
    """Delete message (soft delete)"""
    try:
        success = await messaging_service.delete_message(message_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        return {"status": "deleted", "message_id": message_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete message: {str(e)}"
        )


# === FILE DOWNLOADS ===

@router.get("/attachments/{attachment_id}")
async def download_attachment(
    attachment_id: str,
    private_key: str = Form(..., description="User's private key for decryption"),
    current_user = Depends(get_current_user),
    messaging_service: UnifiedMessagingService = Depends(get_messaging_service)
):
    """Download and decrypt file attachment"""
    try:
        file_data, filename, mime_type = await messaging_service.download_attachment(
            attachment_id, current_user.id, private_key
        )
        
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download attachment: {str(e)}"
        )


# === ADMIN ENDPOINTS ===

@router.post("/admin/cleanup")
async def cleanup_expired_messages(
    current_user = Depends(get_current_user),
    messaging_service: UnifiedMessagingService = Depends(get_messaging_service)
):
    """Clean up expired messages (admin only)"""
    try:
        # Add admin check here
        cleaned_count = await messaging_service.cleanup_expired_messages()
        return {"status": "success", "cleaned_messages": cleaned_count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.get("/admin/stats")
async def get_storage_stats(
    current_user = Depends(get_current_user),
    messaging_service: UnifiedMessagingService = Depends(get_messaging_service)
):
    """Get storage statistics (admin only)"""
    try:
        # Add admin check here
        return await messaging_service.get_storage_stats()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )
