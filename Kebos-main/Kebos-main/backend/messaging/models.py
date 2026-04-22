"""
Unified Secure Messaging Module

Combines secure messaging and storage capabilities with:
- Post-quantum cryptography
- Multi-media support (text, images, audio, video, documents)
- Real-time WebSocket communication
- Comprehensive storage and retrieval
- End-to-end encryption
- Audit logging and compliance
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, BinaryIO, AsyncGenerator
from enum import Enum
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, LargeBinary, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
import uuid
import hashlib
import base64
import mimetypes
import asyncio
import logging

from common.models import Base

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Message content types"""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    FILE = "file"
    SYSTEM = "system"


class MessageStatus(str, Enum):
    """Message delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    DELETED = "deleted"


class ChannelType(str, Enum):
    """Channel types"""
    DIRECT = "direct"
    GROUP = "group"
    BROADCAST = "broadcast"
    SYSTEM = "system"


class EncryptionAlgorithm(str, Enum):
    """Supported encryption algorithms"""
    KYBER_1024 = "Kyber-1024"
    DILITHIUM_3 = "Dilithium-3"
    AES_256_GCM = "AES-256-GCM"
    CHACHA20_POLY1305 = "ChaCha20-Poly1305"


# === DATABASE MODELS ===

class UserKeypairORM(Base):
    """User cryptographic keypairs for post-quantum encryption"""
    __tablename__ = "user_keypairs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    public_key = Column(Text, nullable=False)
    algorithm = Column(String, default="Kyber-1024")
    key_version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    sent_channels = relationship("SecureChannelORM", foreign_keys="SecureChannelORM.sender_id", back_populates="sender")
    received_channels = relationship("SecureChannelORM", foreign_keys="SecureChannelORM.receiver_id", back_populates="receiver")


class SecureChannelORM(Base):
    """Secure communication channels between users"""
    __tablename__ = "secure_channels"
    
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(String, unique=True, index=True, nullable=False)
    channel_name = Column(String)
    channel_type = Column(String, default="direct")
    
    # Participants
    sender_id = Column(String, ForeignKey("user_keypairs.user_id"), nullable=False)
    receiver_id = Column(String, ForeignKey("user_keypairs.user_id"))
    participants = Column(JSON)  # For group channels
    
    # Encryption data
    key_encapsulation_data = Column(LargeBinary)
    shared_secret_hash = Column(String)
    encryption_algorithm = Column(String, default="Kyber-1024")
    
    # Channel settings
    is_ephemeral = Column(Boolean, default=False)
    auto_delete_messages = Column(Boolean, default=False)
    message_retention_hours = Column(Integer, default=24*7)  # 1 week default
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Statistics
    message_count = Column(Integer, default=0)
    total_bytes = Column(Integer, default=0)
    
    # Relationships
    sender = relationship("UserKeypairORM", foreign_keys=[sender_id], back_populates="sent_channels")
    receiver = relationship("UserKeypairORM", foreign_keys=[receiver_id], back_populates="received_channels")
    messages = relationship("SecureMessageORM", back_populates="channel")


class SecureMessageORM(Base):
    """Secure message metadata and storage"""
    __tablename__ = "secure_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, index=True, nullable=False)
    channel_id = Column(String, ForeignKey("secure_channels.channel_id"), nullable=False)
    
    # Message details
    sender_id = Column(String, nullable=False)
    receiver_id = Column(String)
    message_type = Column(String, nullable=False)
    
    # Content metadata
    content_preview = Column(Text)  # First 100 chars for search
    filename = Column(String)
    file_size = Column(Integer)
    mime_type = Column(String)
    
    # Media metadata
    dimensions = Column(JSON)  # Width/height for images/videos
    duration = Column(Float)   # Duration for audio/video
    thumbnail_path = Column(String)
    
    # Security
    content_hash = Column(String, nullable=False)
    encryption_key_id = Column(String)
    signature = Column(Text)
    encryption_algorithm = Column(String, default="AES-256-GCM")
    
    # Status and delivery
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    
    # Privacy and cleanup
    is_deleted_by_sender = Column(Boolean, default=False)
    is_deleted_by_receiver = Column(Boolean, default=False)
    auto_delete_at = Column(DateTime)
    
    # Relationships
    channel = relationship("SecureChannelORM", back_populates="messages")
    attachments = relationship("MessageAttachmentORM", back_populates="message")
    reactions = relationship("MessageReactionORM", back_populates="message")


class MessageAttachmentORM(Base):
    """Message file attachments and media"""
    __tablename__ = "message_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    attachment_id = Column(String, unique=True, index=True, nullable=False)
    message_id = Column(String, ForeignKey("secure_messages.message_id"), nullable=False)
    
    # File details
    filename = Column(String, nullable=False)
    original_filename = Column(String)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    
    # Storage
    storage_path = Column(String, nullable=False)
    storage_type = Column(String, default="encrypted_file")  # encrypted_file, s3, azure_blob
    
    # Security
    encryption_key = Column(String)
    content_hash = Column(String, nullable=False)
    
    # Media processing
    is_processed = Column(Boolean, default=False)
    thumbnail_path = Column(String)
    preview_path = Column(String)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Relationships
    message = relationship("SecureMessageORM", back_populates="attachments")


class MessageReactionORM(Base):
    """Message reactions and interactions"""
    __tablename__ = "message_reactions"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, ForeignKey("secure_messages.message_id"), nullable=False)
    user_id = Column(String, nullable=False)
    reaction_type = Column(String, nullable=False)  # like, love, laugh, angry, etc.
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("SecureMessageORM", back_populates="reactions")


class MessageAuditLogORM(Base):
    """Comprehensive audit logging for compliance"""
    __tablename__ = "message_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(String, unique=True, index=True, nullable=False)
    
    # Event details
    event_type = Column(String, nullable=False)  # send, receive, read, delete, etc.
    user_id = Column(String, nullable=False)
    message_id = Column(String)
    channel_id = Column(String)
    
    # Context
    ip_address = Column(String)
    user_agent = Column(String)
    client_info = Column(JSON)
    
    # Details
    event_data = Column(JSON)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    
    # Compliance
    retention_category = Column(String)
    compliance_tags = Column(JSON)
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)


# === PYDANTIC MODELS ===

class MessageBase(BaseModel):
    """Base message model"""
    message_type: MessageType
    content: Optional[str] = None
    filename: Optional[str] = None


class MessageCreate(MessageBase):
    """Message creation request"""
    receiver_id: str
    channel_id: Optional[str] = None
    auto_delete_hours: Optional[int] = None


class MessageResponse(BaseModel):
    """Message response model"""
    message_id: str
    channel_id: str
    sender_id: str
    receiver_id: Optional[str]
    message_type: MessageType
    content: Optional[str]
    filename: Optional[str]
    file_size: Optional[int]
    status: MessageStatus
    created_at: datetime
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ChannelCreate(BaseModel):
    """Channel creation request"""
    channel_type: ChannelType = ChannelType.DIRECT
    receiver_id: Optional[str] = None
    participants: Optional[List[str]] = None
    channel_name: Optional[str] = None
    is_ephemeral: bool = False
    message_retention_hours: int = 24*7


class ChannelResponse(BaseModel):
    """Channel response model"""
    channel_id: str
    channel_type: ChannelType
    channel_name: Optional[str]
    participants: List[str]
    created_at: datetime
    last_activity: datetime
    message_count: int
    is_active: bool
    
    class Config:
        from_attributes = True


class ChannelMessageHistory(BaseModel):
    """Channel message history"""
    channel_id: str
    messages: List[MessageResponse]
    total_count: int
    has_more: bool


class CreateKeypairRequest(BaseModel):
    """Request to create a new keypair"""
    user_id: str
    algorithm: Optional[str] = "kyber1024"


class KeypairResponse(BaseModel):
    """User keypair response"""
    user_id: str
    public_key: str
    algorithm: str
    created_at: datetime
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# === SERVICE EXCEPTIONS ===

class MessagingError(Exception):
    """Base messaging exception"""
    def __init__(self, message: str, error_code: str = "MESSAGING_ERROR", details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class EncryptionError(MessagingError):
    """Encryption/decryption errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "ENCRYPTION_ERROR", details)


class ChannelError(MessagingError):
    """Channel management errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "CHANNEL_ERROR", details)


class StorageError(MessagingError):
    """Storage operation errors"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "STORAGE_ERROR", details)

# Create indexes for better performance
def create_messaging_indexes(engine):
    """Create additional indexes for messaging tables."""
    from sqlalchemy import text
    
    with engine.connect() as conn:
        # Message queries by user and date
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_secure_messages_sender_created 
            ON secure_messages(sender_id, created_at DESC);
        """))
        
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_secure_messages_receiver_created 
            ON secure_messages(receiver_id, created_at DESC);
        """))
        
        # Channel activity tracking
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_secure_channels_activity 
            ON secure_channels(last_activity DESC) WHERE is_active = true;
        """))
        
        # Audit log queries
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_message_audit_logs_user_timestamp 
            ON message_audit_logs(user_id, timestamp DESC);
        """))
        
        # Quota tracking
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_message_quotas_user_reset 
            ON message_quotas(user_id, daily_reset_at);
        """))
        
        conn.commit()
