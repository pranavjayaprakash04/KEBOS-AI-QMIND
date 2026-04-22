"""
Unified Secure Messaging Services

Comprehensive async services for secure messaging with storage:
- Post-quantum cryptography
- Multi-media message handling
- Real-time communication
- Encrypted storage and retrieval
- Message lifecycle management
- Audit logging and compliance
"""

import asyncio
import aiofiles
import hashlib
import base64
import json
import mimetypes
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, BinaryIO, AsyncGenerator, Tuple
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, desc
from sqlalchemy.orm import selectinload

from .models import (
    UserKeypairORM, SecureChannelORM, SecureMessageORM, MessageAttachmentORM,
    MessageReactionORM, MessageAuditLogORM, MessageType, MessageStatus, 
    ChannelType, EncryptionAlgorithm, MessagingError, EncryptionError, 
    ChannelError, StorageError, MessageCreate, MessageResponse, ChannelCreate,
    ChannelResponse, ChannelMessageHistory, KeypairResponse
)

logger = logging.getLogger(__name__)

# Import crypto modules with fallback
try:
    from .lattice_pqc import MessageCrypto, generate_user_keypair
    logger.info("Using production post-quantum cryptography")
except ImportError:
    from .crypto_pq import MessageCrypto, generate_user_keypair
    logger.warning("Using simulated post-quantum cryptography")


class CryptoService:
    """Post-quantum cryptography service for secure messaging"""
    
    def __init__(self):
        self.crypto = MessageCrypto()
        self.key_cache = {}  # Cache for frequently used keys
        
    async def generate_keypair(self, user_id: str) -> Tuple[str, str]:
        """Generate new keypair for user"""
        try:
            public_key, private_key = await asyncio.to_thread(generate_user_keypair, user_id)
            return public_key, private_key
        except Exception as e:
            raise EncryptionError(f"Failed to generate keypair: {e}")
    
    async def encrypt_message(self, content: str, public_key: str) -> Tuple[str, str]:
        """Encrypt message content"""
        try:
            encrypted_content, session_key = await asyncio.to_thread(
                self.crypto.encrypt_message, content, public_key
            )
            return encrypted_content, session_key
        except Exception as e:
            raise EncryptionError(f"Failed to encrypt message: {e}")
    
    async def decrypt_message(self, encrypted_content: str, private_key: str, session_key: str) -> str:
        """Decrypt message content"""
        try:
            content = await asyncio.to_thread(
                self.crypto.decrypt_message, encrypted_content, private_key, session_key
            )
            return content
        except Exception as e:
            raise EncryptionError(f"Failed to decrypt message: {e}")
    
    async def encrypt_file(self, file_data: bytes, public_key: str) -> Tuple[bytes, str]:
        """Encrypt file data"""
        try:
            encrypted_data, session_key = await asyncio.to_thread(
                self.crypto.encrypt_file, file_data, public_key
            )
            return encrypted_data, session_key
        except Exception as e:
            raise EncryptionError(f"Failed to encrypt file: {e}")
    
    async def decrypt_file(self, encrypted_data: bytes, private_key: str, session_key: str) -> bytes:
        """Decrypt file data"""
        try:
            file_data = await asyncio.to_thread(
                self.crypto.decrypt_file, encrypted_data, private_key, session_key
            )
            return file_data
        except Exception as e:
            raise EncryptionError(f"Failed to decrypt file: {e}")


class StorageService:
    """Secure file storage service with encryption"""
    
    def __init__(self, storage_root: str = "secure_storage"):
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.storage_root / "messages").mkdir(exist_ok=True)
        (self.storage_root / "attachments").mkdir(exist_ok=True)
        (self.storage_root / "thumbnails").mkdir(exist_ok=True)
        
    async def store_encrypted_content(
        self, 
        content: Union[str, bytes], 
        content_type: str = "text",
        subfolder: str = "messages"
    ) -> Tuple[str, str]:
        """Store encrypted content and return storage path and hash"""
        try:
            # Generate unique filename
            content_hash = hashlib.sha256(
                content.encode() if isinstance(content, str) else content
            ).hexdigest()
            filename = f"{uuid.uuid4().hex}_{content_hash[:16]}"
            
            # Determine file path
            file_path = self.storage_root / subfolder / filename
            
            # Store content
            if isinstance(content, str):
                async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                    await f.write(content)
            else:
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(content)
            
            return str(file_path), content_hash
            
        except Exception as e:
            raise StorageError(f"Failed to store content: {e}")
    
    async def retrieve_encrypted_content(self, storage_path: str, content_type: str = "text") -> Union[str, bytes]:
        """Retrieve encrypted content from storage"""
        try:
            file_path = Path(storage_path)
            
            if not file_path.exists():
                raise StorageError(f"File not found: {storage_path}")
            
            if content_type == "text":
                async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                    return await f.read()
            else:
                async with aiofiles.open(file_path, 'rb') as f:
                    return await f.read()
                    
        except Exception as e:
            raise StorageError(f"Failed to retrieve content: {e}")
    
    async def delete_stored_content(self, storage_path: str) -> bool:
        """Securely delete stored content"""
        try:
            file_path = Path(storage_path)
            if file_path.exists():
                # Secure deletion (overwrite before delete)
                file_size = file_path.stat().st_size
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(os.urandom(file_size))
                
                file_path.unlink()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete file {storage_path}: {e}")
            return False
    
    async def generate_thumbnail(self, file_path: str, max_size: Tuple[int, int] = (200, 200)) -> Optional[str]:
        """Generate thumbnail for image/video files"""
        try:
            # This is a placeholder - implement actual thumbnail generation
            # using PIL for images, ffmpeg for videos
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                # Image thumbnail logic here
                thumbnail_path = str(self.storage_root / "thumbnails" / f"{uuid.uuid4().hex}.jpg")
                # Implement actual thumbnail generation
                return thumbnail_path
            elif file_ext in ['.mp4', '.avi', '.mov', '.webm']:
                # Video thumbnail logic here
                thumbnail_path = str(self.storage_root / "thumbnails" / f"{uuid.uuid4().hex}.jpg")
                # Implement actual video thumbnail generation
                return thumbnail_path
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to generate thumbnail: {e}")
            return None


class AuditService:
    """Audit logging service for compliance and security"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def log_event(
        self, 
        event_type: str,
        user_id: str,
        message_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        event_data: Dict[str, Any] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> str:
        """Log messaging event for audit trail"""
        try:
            log_entry = MessageAuditLogORM(
                log_id=str(uuid.uuid4()),
                event_type=event_type,
                user_id=user_id,
                message_id=message_id,
                channel_id=channel_id,
                event_data=event_data or {},
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                error_message=error_message,
                timestamp=datetime.utcnow()
            )
            
            self.db.add(log_entry)
            await self.db.commit()
            
            return log_entry.log_id
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            raise
    
    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[MessageAuditLogORM]:
        """Retrieve audit logs with filtering"""
        try:
            query = select(MessageAuditLogORM)
            
            filters = []
            if user_id:
                filters.append(MessageAuditLogORM.user_id == user_id)
            if event_type:
                filters.append(MessageAuditLogORM.event_type == event_type)
            if start_date:
                filters.append(MessageAuditLogORM.timestamp >= start_date)
            if end_date:
                filters.append(MessageAuditLogORM.timestamp <= end_date)
            
            if filters:
                query = query.where(and_(*filters))
            
            query = query.order_by(desc(MessageAuditLogORM.timestamp)).limit(limit)
            
            result = await self.db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Failed to retrieve audit logs: {e}")
            return []


class UnifiedMessagingService:
    """Main unified messaging service combining messaging and storage"""
    
    def __init__(self, db_session: AsyncSession, storage_root: str = "secure_storage"):
        self.db = db_session
        self.crypto_service = CryptoService()
        self.storage_service = StorageService(storage_root)
        self.audit_service = AuditService(db_session)
        
    # === USER KEYPAIR MANAGEMENT ===
    
    async def create_user_keypair(self, user_id: str) -> KeypairResponse:
        """Create new keypair for user"""
        try:
            # Check if user already has a keypair
            existing = await self.db.execute(
                select(UserKeypairORM).where(UserKeypairORM.user_id == user_id)
            )
            if existing.scalar_one_or_none():
                raise MessagingError(f"User {user_id} already has a keypair")
            
            # Generate new keypair
            public_key, private_key = await self.crypto_service.generate_keypair(user_id)
            
            # Store public key in database
            keypair = UserKeypairORM(
                user_id=user_id,
                public_key=public_key,
                algorithm="Kyber-1024",
                created_at=datetime.utcnow()
            )
            
            self.db.add(keypair)
            await self.db.commit()
            
            # Log the event
            await self.audit_service.log_event("keypair_created", user_id)
            
            return KeypairResponse(
                user_id=user_id,
                public_key=public_key,
                algorithm="Kyber-1024",
                created_at=keypair.created_at
            )
            
        except Exception as e:
            await self.db.rollback()
            if isinstance(e, MessagingError):
                raise
            raise MessagingError(f"Failed to create keypair: {e}")
    
    async def get_user_public_key(self, user_id: str) -> Optional[str]:
        """Get user's public key"""
        try:
            result = await self.db.execute(
                select(UserKeypairORM.public_key).where(
                    and_(
                        UserKeypairORM.user_id == user_id,
                        UserKeypairORM.is_active == True
                    )
                )
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get public key for {user_id}: {e}")
            return None
    
    # === CHANNEL MANAGEMENT ===
    
    async def create_channel(self, channel_data: ChannelCreate, creator_id: str) -> ChannelResponse:
        """Create new secure communication channel"""
        try:
            channel_id = str(uuid.uuid4())
            
            # Prepare participants list
            participants = []
            if channel_data.channel_type == ChannelType.DIRECT:
                if not channel_data.receiver_id:
                    raise ChannelError("Direct channel requires receiver_id")
                participants = [creator_id, channel_data.receiver_id]
                receiver_id = channel_data.receiver_id
            elif channel_data.channel_type == ChannelType.GROUP:
                participants = [creator_id] + (channel_data.participants or [])
                receiver_id = None
            else:
                participants = [creator_id]
                receiver_id = None
            
            # Create channel
            channel = SecureChannelORM(
                channel_id=channel_id,
                channel_name=channel_data.channel_name,
                channel_type=channel_data.channel_type.value,
                sender_id=creator_id,
                receiver_id=receiver_id,
                participants=participants,
                is_ephemeral=channel_data.is_ephemeral,
                message_retention_hours=channel_data.message_retention_hours,
                created_at=datetime.utcnow()
            )
            
            self.db.add(channel)
            await self.db.commit()
            
            # Log the event
            await self.audit_service.log_event(
                "channel_created", 
                creator_id, 
                channel_id=channel_id,
                event_data={"channel_type": channel_data.channel_type.value}
            )
            
            return ChannelResponse(
                channel_id=channel_id,
                channel_type=ChannelType(channel.channel_type),
                channel_name=channel.channel_name,
                participants=participants,
                created_at=channel.created_at,
                last_activity=channel.last_activity,
                message_count=0,
                is_active=True
            )
            
        except Exception as e:
            await self.db.rollback()
            if isinstance(e, MessagingError):
                raise
            raise ChannelError(f"Failed to create channel: {e}")
    
    async def get_user_channels(self, user_id: str) -> List[ChannelResponse]:
        """Get all channels for a user"""
        try:
            result = await self.db.execute(
                select(SecureChannelORM).where(
                    and_(
                        or_(
                            SecureChannelORM.sender_id == user_id,
                            SecureChannelORM.receiver_id == user_id,
                            SecureChannelORM.participants.contains([user_id])
                        ),
                        SecureChannelORM.is_active == True
                    )
                ).order_by(desc(SecureChannelORM.last_activity))
            )
            
            channels = result.scalars().all()
            
            return [
                ChannelResponse(
                    channel_id=ch.channel_id,
                    channel_type=ChannelType(ch.channel_type),
                    channel_name=ch.channel_name,
                    participants=ch.participants or [ch.sender_id, ch.receiver_id],
                    created_at=ch.created_at,
                    last_activity=ch.last_activity,
                    message_count=ch.message_count,
                    is_active=ch.is_active
                )
                for ch in channels
            ]
            
        except Exception as e:
            logger.error(f"Failed to get channels for {user_id}: {e}")
            return []
    
    # === MESSAGE HANDLING ===
    
    async def send_message(
        self, 
        message_data: MessageCreate, 
        sender_id: str,
        file_data: Optional[bytes] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> MessageResponse:
        """Send encrypted message with optional file attachment"""
        try:
            message_id = str(uuid.uuid4())
            
            # Get or create channel
            if message_data.channel_id:
                channel = await self._get_channel(message_data.channel_id)
                if not channel:
                    raise ChannelError(f"Channel {message_data.channel_id} not found")
            else:
                # Create direct channel
                channel_data = ChannelCreate(
                    channel_type=ChannelType.DIRECT,
                    receiver_id=message_data.receiver_id
                )
                channel_response = await self.create_channel(channel_data, sender_id)
                channel_id = channel_response.channel_id
                channel = await self._get_channel(channel_id)
            
            # Get receiver's public key
            receiver_public_key = await self.get_user_public_key(message_data.receiver_id)
            if not receiver_public_key:
                raise EncryptionError(f"No public key found for receiver {message_data.receiver_id}")
            
            # Encrypt message content
            encrypted_content = None
            session_key = None
            content_hash = None
            
            if message_data.content:
                encrypted_content, session_key = await self.crypto_service.encrypt_message(
                    message_data.content, receiver_public_key
                )
                content_hash = hashlib.sha256(message_data.content.encode()).hexdigest()
            
            # Handle file attachment
            attachment_id = None
            file_size = None
            mime_type = None
            
            if file_data and message_data.filename:
                file_size = len(file_data)
                mime_type = mimetypes.guess_type(message_data.filename)[0] or 'application/octet-stream'
                
                # Encrypt file
                encrypted_file_data, file_session_key = await self.crypto_service.encrypt_file(
                    file_data, receiver_public_key
                )
                
                # Store encrypted file
                storage_path, file_hash = await self.storage_service.store_encrypted_content(
                    encrypted_file_data, "binary", "attachments"
                )
                
                # Create attachment record
                attachment = MessageAttachmentORM(
                    attachment_id=str(uuid.uuid4()),
                    message_id=message_id,
                    filename=message_data.filename,
                    original_filename=message_data.filename,
                    file_size=file_size,
                    mime_type=mime_type,
                    storage_path=storage_path,
                    encryption_key=file_session_key,
                    content_hash=file_hash,
                    created_at=datetime.utcnow()
                )
                
                self.db.add(attachment)
                attachment_id = attachment.attachment_id
                
                # Generate thumbnail if applicable
                thumbnail_path = await self.storage_service.generate_thumbnail(storage_path)
                if thumbnail_path:
                    attachment.thumbnail_path = thumbnail_path
            
            # Store encrypted content
            if encrypted_content:
                storage_path, _ = await self.storage_service.store_encrypted_content(
                    encrypted_content, "text", "messages"
                )
            else:
                storage_path = None
            
            # Create message record
            message = SecureMessageORM(
                message_id=message_id,
                channel_id=channel.channel_id,
                sender_id=sender_id,
                receiver_id=message_data.receiver_id,
                message_type=message_data.message_type.value,
                content_preview=message_data.content[:100] if message_data.content else None,
                filename=message_data.filename,
                file_size=file_size,
                mime_type=mime_type,
                content_hash=content_hash or hashlib.sha256(file_data or b'').hexdigest(),
                encryption_key_id=session_key,
                status=MessageStatus.SENT.value,
                created_at=datetime.utcnow(),
                sent_at=datetime.utcnow()
            )
            
            # Set auto-delete if specified
            if message_data.auto_delete_hours:
                message.auto_delete_at = datetime.utcnow() + timedelta(hours=message_data.auto_delete_hours)
            
            self.db.add(message)
            
            # Update channel stats
            await self._update_channel_activity(channel.channel_id, file_size or len(message_data.content or ''))
            
            await self.db.commit()
            
            # Log the event
            await self.audit_service.log_event(
                "message_sent",
                sender_id,
                message_id=message_id,
                channel_id=channel.channel_id,
                event_data={
                    "message_type": message_data.message_type.value,
                    "has_attachment": file_data is not None,
                    "file_size": file_size
                },
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return MessageResponse(
                message_id=message_id,
                channel_id=channel.channel_id,
                sender_id=sender_id,
                receiver_id=message_data.receiver_id,
                message_type=message_data.message_type,
                content=message_data.content,
                filename=message_data.filename,
                file_size=file_size,
                status=MessageStatus.SENT,
                created_at=message.created_at,
                delivered_at=None,
                read_at=None
            )
            
        except Exception as e:
            await self.db.rollback()
            if isinstance(e, MessagingError):
                raise
            raise MessagingError(f"Failed to send message: {e}")
    
    async def get_message(self, message_id: str, user_id: str, private_key: str) -> Optional[MessageResponse]:
        """Get and decrypt a specific message"""
        try:
            # Get message with attachments
            result = await self.db.execute(
                select(SecureMessageORM)
                .options(selectinload(SecureMessageORM.attachments))
                .where(SecureMessageORM.message_id == message_id)
            )
            message = result.scalar_one_or_none()
            
            if not message:
                return None
            
            # Check if user has access to this message
            if user_id not in [message.sender_id, message.receiver_id]:
                # Check if it's a group message
                channel = await self._get_channel(message.channel_id)
                if not channel or user_id not in (channel.participants or []):
                    raise MessagingError("Access denied to message")
            
            # Decrypt content if available
            decrypted_content = None
            if message.encryption_key_id:
                try:
                    encrypted_content = await self.storage_service.retrieve_encrypted_content(
                        f"secure_storage/messages/{message_id}_content", "text"
                    )
                    decrypted_content = await self.crypto_service.decrypt_message(
                        encrypted_content, private_key, message.encryption_key_id
                    )
                except Exception as e:
                    logger.error(f"Failed to decrypt message {message_id}: {e}")
            
            # Mark as read if it's the receiver
            if user_id == message.receiver_id and not message.read_at:
                await self._mark_message_read(message_id)
            
            return MessageResponse(
                message_id=message.message_id,
                channel_id=message.channel_id,
                sender_id=message.sender_id,
                receiver_id=message.receiver_id,
                message_type=MessageType(message.message_type),
                content=decrypted_content,
                filename=message.filename,
                file_size=message.file_size,
                status=MessageStatus(message.status),
                created_at=message.created_at,
                delivered_at=message.delivered_at,
                read_at=message.read_at
            )
            
        except Exception as e:
            if isinstance(e, MessagingError):
                raise
            raise MessagingError(f"Failed to get message: {e}")
    
    async def get_channel_messages(
        self, 
        channel_id: str, 
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        before_timestamp: Optional[datetime] = None
    ) -> ChannelMessageHistory:
        """Get message history for a channel"""
        try:
            # Verify user has access to channel
            channel = await self._get_channel(channel_id)
            if not channel:
                raise ChannelError(f"Channel {channel_id} not found")
            
            if user_id not in [channel.sender_id, channel.receiver_id] and \
               user_id not in (channel.participants or []):
                raise ChannelError("Access denied to channel")
            
            # Build query
            query = select(SecureMessageORM).where(
                and_(
                    SecureMessageORM.channel_id == channel_id,
                    SecureMessageORM.is_deleted_by_sender == False,
                    SecureMessageORM.is_deleted_by_receiver == False
                )
            )
            
            if before_timestamp:
                query = query.where(SecureMessageORM.created_at < before_timestamp)
            
            query = query.order_by(desc(SecureMessageORM.created_at)).offset(offset).limit(limit + 1)
            
            result = await self.db.execute(query)
            messages = result.scalars().all()
            
            has_more = len(messages) > limit
            if has_more:
                messages = messages[:-1]
            
            # Convert to response format (without decrypting content for performance)
            message_responses = [
                MessageResponse(
                    message_id=msg.message_id,
                    channel_id=msg.channel_id,
                    sender_id=msg.sender_id,
                    receiver_id=msg.receiver_id,
                    message_type=MessageType(msg.message_type),
                    content=msg.content_preview,  # Only preview for list view
                    filename=msg.filename,
                    file_size=msg.file_size,
                    status=MessageStatus(msg.status),
                    created_at=msg.created_at,
                    delivered_at=msg.delivered_at,
                    read_at=msg.read_at
                )
                for msg in messages
            ]
            
            # Get total count
            count_result = await self.db.execute(
                select(SecureMessageORM).where(
                    and_(
                        SecureMessageORM.channel_id == channel_id,
                        SecureMessageORM.is_deleted_by_sender == False,
                        SecureMessageORM.is_deleted_by_receiver == False
                    )
                )
            )
            total_count = len(count_result.scalars().all())
            
            return ChannelMessageHistory(
                channel_id=channel_id,
                messages=message_responses,
                total_count=total_count,
                has_more=has_more
            )
            
        except Exception as e:
            if isinstance(e, MessagingError):
                raise
            raise MessagingError(f"Failed to get channel messages: {e}")
    
    async def delete_message(self, message_id: str, user_id: str) -> bool:
        """Delete message (soft delete)"""
        try:
            message = await self.db.get(SecureMessageORM, message_id)
            if not message:
                return False
            
            # Mark as deleted by appropriate user
            if user_id == message.sender_id:
                message.is_deleted_by_sender = True
            elif user_id == message.receiver_id:
                message.is_deleted_by_receiver = True
            else:
                raise MessagingError("Access denied")
            
            # If both users deleted, schedule for permanent deletion
            if message.is_deleted_by_sender and message.is_deleted_by_receiver:
                message.auto_delete_at = datetime.utcnow() + timedelta(days=30)
            
            await self.db.commit()
            
            # Log the event
            await self.audit_service.log_event(
                "message_deleted",
                user_id,
                message_id=message_id,
                channel_id=message.channel_id
            )
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            if isinstance(e, MessagingError):
                raise
            raise MessagingError(f"Failed to delete message: {e}")
    
    # === FILE HANDLING ===
    
    async def download_attachment(
        self, 
        attachment_id: str, 
        user_id: str, 
        private_key: str
    ) -> Tuple[bytes, str, str]:
        """Download and decrypt file attachment"""
        try:
            # Get attachment
            result = await self.db.execute(
                select(MessageAttachmentORM)
                .join(SecureMessageORM)
                .where(MessageAttachmentORM.attachment_id == attachment_id)
            )
            attachment = result.scalar_one_or_none()
            
            if not attachment:
                raise StorageError(f"Attachment {attachment_id} not found")
            
            # Check access
            message = attachment.message
            if user_id not in [message.sender_id, message.receiver_id]:
                raise MessagingError("Access denied to attachment")
            
            # Retrieve encrypted file
            encrypted_data = await self.storage_service.retrieve_encrypted_content(
                attachment.storage_path, "binary"
            )
            
            # Decrypt file
            file_data = await self.crypto_service.decrypt_file(
                encrypted_data, private_key, attachment.encryption_key
            )
            
            # Log download
            await self.audit_service.log_event(
                "attachment_downloaded",
                user_id,
                message_id=message.message_id,
                event_data={"attachment_id": attachment_id, "filename": attachment.filename}
            )
            
            return file_data, attachment.filename, attachment.mime_type
            
        except Exception as e:
            if isinstance(e, MessagingError):
                raise
            raise StorageError(f"Failed to download attachment: {e}")
    
    # === HELPER METHODS ===
    
    async def _get_channel(self, channel_id: str) -> Optional[SecureChannelORM]:
        """Get channel by ID"""
        result = await self.db.execute(
            select(SecureChannelORM).where(SecureChannelORM.channel_id == channel_id)
        )
        return result.scalar_one_or_none()
    
    async def _update_channel_activity(self, channel_id: str, bytes_added: int = 0):
        """Update channel activity and stats"""
        await self.db.execute(
            update(SecureChannelORM)
            .where(SecureChannelORM.channel_id == channel_id)
            .values(
                last_activity=datetime.utcnow(),
                message_count=SecureChannelORM.message_count + 1,
                total_bytes=SecureChannelORM.total_bytes + bytes_added
            )
        )
    
    async def _mark_message_read(self, message_id: str):
        """Mark message as read"""
        await self.db.execute(
            update(SecureMessageORM)
            .where(SecureMessageORM.message_id == message_id)
            .values(
                status=MessageStatus.READ.value,
                read_at=datetime.utcnow()
            )
        )
    
    # === CLEANUP AND MAINTENANCE ===
    
    async def cleanup_expired_messages(self) -> int:
        """Clean up expired messages and files"""
        try:
            # Find expired messages
            expired_messages = await self.db.execute(
                select(SecureMessageORM)
                .options(selectinload(SecureMessageORM.attachments))
                .where(
                    and_(
                        SecureMessageORM.auto_delete_at.isnot(None),
                        SecureMessageORM.auto_delete_at <= datetime.utcnow()
                    )
                )
            )
            
            messages = expired_messages.scalars().all()
            cleaned_count = 0
            
            for message in messages:
                # Delete attachment files
                for attachment in message.attachments:
                    await self.storage_service.delete_stored_content(attachment.storage_path)
                    if attachment.thumbnail_path:
                        await self.storage_service.delete_stored_content(attachment.thumbnail_path)
                
                # Delete message content file
                if message.encryption_key_id:
                    content_path = f"secure_storage/messages/{message.message_id}_content"
                    await self.storage_service.delete_stored_content(content_path)
                
                # Delete database records
                await self.db.delete(message)
                cleaned_count += 1
            
            await self.db.commit()
            
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} expired messages")
            
            return cleaned_count
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to cleanup expired messages: {e}")
            return 0
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            # Message stats
            message_stats = await self.db.execute(
                select(
                    SecureMessageORM.message_type,
                    SecureMessageORM.status
                ).where(SecureMessageORM.auto_delete_at.is_(None))
            )
            
            # Channel stats  
            channel_stats = await self.db.execute(
                select(SecureChannelORM.channel_type, SecureChannelORM.is_active)
            )
            
            # Calculate storage usage
            storage_usage = {
                "total_messages": len(message_stats.all()),
                "total_channels": len(channel_stats.all()),
                "storage_root": str(self.storage_service.storage_root),
                "message_types": {},
                "channel_types": {}
            }
            
            return storage_usage
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {}
