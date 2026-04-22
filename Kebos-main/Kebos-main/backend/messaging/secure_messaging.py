"""
Secure Messaging Module with Post-Quantum Encryption

Supports secure transfer of:
- Text messages
- Images (JPEG, PNG, GIF, WebP)
- Audio files (MP3, WAV, OGG, M4A)
- Video files (MP4, AVI, MOV, WebM)
- Documents (PDF, DOCX, TXT, etc.)
"""

import os
import io
import mimetypes
import hashlib
import base64
import logging
from typing import Dict, Any, List, Optional, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import json

# Set up logging
logger = logging.getLogger(__name__)

# Try to import the production PQC implementation first
try:
    from .lattice_pqc import MessageCrypto, generate_user_keypair, save_keypair, load_keypair
    logger.info("Using production post-quantum cryptography implementation")
except ImportError:
    # Fall back to simulation implementation
    from .crypto_pq import MessageCrypto, generate_user_keypair, save_keypair, load_keypair
    logger.warning("Using simulated post-quantum cryptography implementation")


class MessageType(Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    FILE = "file"


class MessageStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


@dataclass
class MessageMetadata:
    """Metadata for encrypted messages."""
    message_id: str
    sender_id: str
    receiver_id: str
    message_type: MessageType
    filename: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    thumbnail: Optional[str] = None  # Base64 encoded thumbnail for media
    duration: Optional[float] = None  # For audio/video
    dimensions: Optional[Dict[str, int]] = None  # For images/video
    checksum: Optional[str] = None
    created_at: Optional[str] = None
    status: MessageStatus = MessageStatus.PENDING
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self):
        """Convert to dictionary with enum values as strings."""
        data = asdict(self)
        # Convert enums to their string values for JSON serialization
        if isinstance(data['message_type'], MessageType):
            data['message_type'] = data['message_type'].value
        if isinstance(data['status'], MessageStatus):
            data['status'] = data['status'].value
        return data


class SecureMessaging:
    """
    Main messaging class with post-quantum encryption support.
    """
    
    def __init__(self, storage_path: str = "./secure_messages"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize crypto
        self.crypto = MessageCrypto()
        
        # Supported file types
        self.supported_types = {
            MessageType.IMAGE: {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'},
            MessageType.AUDIO: {'.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac'},
            MessageType.VIDEO: {'.mp4', '.avi', '.mov', '.webm', '.mkv', '.wmv', '.flv'},
            MessageType.DOCUMENT: {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.ppt', '.pptx', '.xls', '.xlsx'}
        }
        
        # File size limits (in bytes)
        self.size_limits = {
            MessageType.TEXT: 10 * 1024,        # 10 KB
            MessageType.IMAGE: 50 * 1024 * 1024, # 50 MB
            MessageType.AUDIO: 100 * 1024 * 1024, # 100 MB
            MessageType.VIDEO: 500 * 1024 * 1024, # 500 MB
            MessageType.DOCUMENT: 100 * 1024 * 1024, # 100 MB
            MessageType.FILE: 200 * 1024 * 1024   # 200 MB
        }
    
    def generate_user_keypair(self, user_id: str) -> Dict[str, str]:
        """Generate and save new keypair for user."""
        private_key, public_key = generate_user_keypair()
        
        # Save to secure storage
        key_storage = self.storage_path / "keys"
        save_keypair(user_id, private_key, public_key, str(key_storage))
        
        return {
            'user_id': user_id,
            'public_key': public_key,
            'private_key': private_key,  # Return for initial setup only
            'created_at': datetime.now().isoformat()
        }
    
    def get_public_key(self, user_id: str) -> str:
        """Get public key for a user."""
        try:
            _, public_key = load_keypair(user_id, str(self.storage_path / "keys"))
            return public_key
        except ValueError:
            raise ValueError(f"No keypair found for user {user_id}")
    
    def create_secure_channel(self, sender_id: str, receiver_id: str) -> str:
        """Create a secure communication channel between two users."""
        # Load keys
        sender_private_key_str, _ = load_keypair(sender_id, str(self.storage_path / "keys"))
        receiver_public_key = self.get_public_key(receiver_id)
        
        # Decode keys
        sender_private_key = base64.b64decode(sender_private_key_str)
        receiver_public_key_bytes = receiver_public_key.encode('utf-8')
        
        # Create channel
        channel_info = self.crypto.create_secure_channel(sender_private_key, receiver_public_key_bytes)
        
        # Save channel info
        channel_file = self.storage_path / "channels" / f"{channel_info['channel_id']}.json"
        channel_file.parent.mkdir(parents=True, exist_ok=True)
        
        channel_data = {
            'channel_id': channel_info['channel_id'],
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'channel_info': channel_info,
            'created_at': datetime.now().isoformat()
        }
        
        with open(channel_file, 'w') as f:
            json.dump(channel_data, f, indent=2)
        
        return channel_info['channel_id']
    
    def establish_channel(self, channel_id: str, receiver_id: str) -> bool:
        """Establish channel on receiver side."""
        try:
            # Load channel info
            channel_file = self.storage_path / "channels" / f"{channel_id}.json"
            with open(channel_file, 'r') as f:
                channel_data = json.load(f)
            
            # Load receiver private key
            receiver_private_key_str, _ = load_keypair(receiver_id, str(self.storage_path / "keys"))
            receiver_private_key = base64.b64decode(receiver_private_key_str)
            
            # Establish channel
            established_channel_id = self.crypto.establish_channel(
                channel_data['channel_info'], 
                receiver_private_key
            )
            
            return established_channel_id == channel_id
        except Exception as e:
            print(f"Failed to establish channel: {e}")
            return False
    
    def detect_message_type(self, filename: Optional[str] = None, content: Optional[bytes] = None) -> MessageType:
        """Detect message type based on filename or content."""
        if filename:
            file_ext = Path(filename).suffix.lower()
            
            for msg_type, extensions in self.supported_types.items():
                if file_ext in extensions:
                    return msg_type
        
        # If no filename or extension not recognized, try to detect from content
        if content:
            # Simple magic number detection
            if content.startswith(b'\xff\xd8\xff'):  # JPEG
                return MessageType.IMAGE
            elif content.startswith(b'\x89PNG'):  # PNG
                return MessageType.IMAGE
            elif content.startswith(b'GIF8'):  # GIF
                return MessageType.IMAGE
            elif content.startswith(b'\x00\x00\x00\x20ftypmp4') or content.startswith(b'\x00\x00\x00\x18ftypmp4'):  # MP4
                return MessageType.VIDEO
            elif content.startswith(b'ID3') or content.startswith(b'\xff\xfb'):  # MP3
                return MessageType.AUDIO
            elif content.startswith(b'%PDF'):  # PDF
                return MessageType.DOCUMENT
        
        return MessageType.FILE
    
    def validate_file(self, content: bytes, message_type: MessageType, filename: Optional[str] = None) -> bool:
        """Validate file size and type."""
        # Check file size
        if len(content) > self.size_limits.get(message_type, self.size_limits[MessageType.FILE]):
            raise ValueError(f"File too large for {message_type.value} (max {self.size_limits[message_type] // 1024 // 1024} MB)")
        
        # Additional validation based on type
        if message_type == MessageType.IMAGE:
            # Validate image format
            if not (content.startswith(b'\xff\xd8\xff') or  # JPEG
                   content.startswith(b'\x89PNG') or        # PNG
                   content.startswith(b'GIF8') or           # GIF
                   content.startswith(b'RIFF') and b'WEBP' in content[:20]):  # WebP
                raise ValueError("Invalid image format")
        
        return True
    
    def calculate_checksum(self, content: bytes) -> str:
        """Calculate SHA-256 checksum of content."""
        return hashlib.sha256(content).hexdigest()
    
    def send_text_message(self, 
                         sender_id: str, 
                         receiver_id: str, 
                         text: str,
                         channel_id: Optional[str] = None) -> Dict[str, Any]:
        """Send encrypted text message."""
        if len(text.encode('utf-8')) > self.size_limits[MessageType.TEXT]:
            raise ValueError("Text message too long")
        
        # Create channel if not provided
        if not channel_id:
            channel_id = self.create_secure_channel(sender_id, receiver_id)
        
        # Create message metadata
        message_id = hashlib.sha256(f"{sender_id}{receiver_id}{text}{datetime.now()}".encode()).hexdigest()[:16]
        metadata = MessageMetadata(
            message_id=message_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=MessageType.TEXT,
            file_size=len(text.encode('utf-8')),
            checksum=self.calculate_checksum(text.encode('utf-8'))
        )
        
        # Encrypt message
        sender_private_key_str, _ = load_keypair(sender_id, str(self.storage_path / "keys"))
        sender_private_key = base64.b64decode(sender_private_key_str)
        
        encrypted_message = self.crypto.encrypt_and_sign(
            text.encode('utf-8'),
            channel_id,
            sender_private_key,
            MessageType.TEXT.value
        )
        
        # Save message
        message_data = {
            'metadata': metadata.to_dict(),  # Convert to dict for JSON serialization
            'encrypted_message': encrypted_message,
            'channel_id': channel_id
        }
        
        self._save_message(message_id, message_data)
        
        return {
            'message_id': message_id,
            'channel_id': channel_id,
            'status': MessageStatus.SENT.value,
            'timestamp': metadata.created_at
        }
    
    def send_file_message(self,
                         sender_id: str,
                         receiver_id: str,
                         file_content: bytes,
                         filename: str,
                         channel_id: Optional[str] = None,
                         message_type: Optional[MessageType] = None) -> Dict[str, Any]:
        """Send encrypted file message (image, audio, video, document)."""
        
        # Detect message type if not provided
        if message_type is None:
            message_type = self.detect_message_type(filename, file_content)
        
        # Validate file
        self.validate_file(file_content, message_type, filename)
        
        # Create channel if not provided
        if not channel_id:
            channel_id = self.create_secure_channel(sender_id, receiver_id)
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        
        # Create message metadata
        message_id = hashlib.sha256(f"{sender_id}{receiver_id}{filename}{datetime.now()}".encode()).hexdigest()[:16]
        metadata = MessageMetadata(
            message_id=message_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=message_type,
            filename=filename,
            file_size=len(file_content),
            mime_type=mime_type,
            checksum=self.calculate_checksum(file_content)
        )
        
        # Add media-specific metadata
        if message_type in [MessageType.IMAGE, MessageType.VIDEO]:
            # In production, you'd use PIL/OpenCV to get actual dimensions
            metadata.dimensions = {'width': 1920, 'height': 1080}  # Placeholder
        
        if message_type in [MessageType.AUDIO, MessageType.VIDEO]:
            # In production, you'd use ffmpeg/mutagen to get actual duration
            metadata.duration = 120.0  # Placeholder duration in seconds
        
        # Encrypt file
        sender_private_key_str, _ = load_keypair(sender_id, str(self.storage_path / "keys"))
        sender_private_key = base64.b64decode(sender_private_key_str)
        
        encrypted_message = self.crypto.encrypt_and_sign(
            file_content,
            channel_id,
            sender_private_key,
            message_type.value
        )
        
        # Save message
        message_data = {
            'metadata': metadata.to_dict(),  # Convert to dict for JSON serialization
            'encrypted_message': encrypted_message,
            'channel_id': channel_id
        }
        
        self._save_message(message_id, message_data)
        
        return {
            'message_id': message_id,
            'channel_id': channel_id,
            'filename': filename,
            'file_size': len(file_content),
            'message_type': message_type.value,
            'status': MessageStatus.SENT.value,
            'timestamp': metadata.created_at
        }
    
    def receive_message(self, message_id: str, receiver_id: str) -> Dict[str, Any]:
        """Receive and decrypt a message."""
        # Load message
        message_data = self._load_message(message_id)
        
        metadata = MessageMetadata(**message_data['metadata'])
        
        # Verify receiver
        if metadata.receiver_id != receiver_id:
            raise ValueError("Not authorized to receive this message")
        
        # Get sender public key
        sender_public_key = self.get_public_key(metadata.sender_id).encode('utf-8')
        
        # Decrypt message
        decrypted_content = self.crypto.verify_and_decrypt(
            message_data['encrypted_message'],
            message_data['channel_id'],
            sender_public_key
        )
        
        # Verify checksum
        calculated_checksum = self.calculate_checksum(decrypted_content)
        if calculated_checksum != metadata.checksum:
            raise ValueError("Message integrity check failed")
        
        # Update message status
        metadata.status = MessageStatus.READ
        message_data['metadata'] = asdict(metadata)
        self._save_message(message_id, message_data)
        
        result = {
            'message_id': message_id,
            'sender_id': metadata.sender_id,
            'message_type': metadata.message_type.value,
            'timestamp': metadata.created_at,
            'checksum_verified': True
        }
        
        if metadata.message_type == MessageType.TEXT:
            result['text'] = decrypted_content.decode('utf-8')
        else:
            result['filename'] = metadata.filename
            result['file_content'] = decrypted_content
            result['file_size'] = metadata.file_size
            result['mime_type'] = metadata.mime_type
            
            if metadata.dimensions:
                result['dimensions'] = metadata.dimensions
            if metadata.duration:
                result['duration'] = metadata.duration
        
        return result
    
    def list_messages(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """List messages for a user (sent or received)."""
        messages = []
        message_dir = self.storage_path / "messages"
        
        if not message_dir.exists():
            return messages
        
        for message_file in message_dir.glob("*.json"):
            try:
                with open(message_file, 'r') as f:
                    message_data = json.load(f)
                
                metadata = MessageMetadata(**message_data['metadata'])
                
                if metadata.sender_id == user_id or metadata.receiver_id == user_id:
                    messages.append({
                        'message_id': metadata.message_id,
                        'sender_id': metadata.sender_id,
                        'receiver_id': metadata.receiver_id,
                        'message_type': metadata.message_type.value,
                        'filename': metadata.filename,
                        'file_size': metadata.file_size,
                        'status': metadata.status.value,
                        'created_at': metadata.created_at
                    })
            except Exception as e:
                continue  # Skip corrupted messages
        
        # Sort by timestamp (newest first)
        messages.sort(key=lambda x: x['created_at'], reverse=True)
        
        return messages[:limit]
    
    def delete_message(self, message_id: str, user_id: str) -> bool:
        """Delete a message (only sender can delete)."""
        try:
            message_data = self._load_message(message_id)
            metadata = MessageMetadata(**message_data['metadata'])
            
            if metadata.sender_id != user_id:
                raise ValueError("Only sender can delete message")
            
            # Delete message file
            message_file = self.storage_path / "messages" / f"{message_id}.json"
            if message_file.exists():
                message_file.unlink()
                return True
            
            return False
        except Exception:
            return False
    
    def _save_message(self, message_id: str, message_data: Dict[str, Any]):
        """Save encrypted message to storage."""
        message_dir = self.storage_path / "messages"
        message_dir.mkdir(parents=True, exist_ok=True)
        
        # Convert MessageMetadata to dict for JSON serialization
        if 'metadata' in message_data and isinstance(message_data['metadata'], MessageMetadata):
            message_data['metadata'] = message_data['metadata'].to_dict()
        
        # Use Path object for cross-platform path handling
        message_file = message_dir / f"{message_id}.json"
        with open(message_file, 'w') as f:
            json.dump(message_data, f, indent=2)
    
    def _load_message(self, message_id: str) -> Dict[str, Any]:
        """Load message from storage."""
        # Use Path object for cross-platform path handling
        message_file = self.storage_path / "messages" / f"{message_id}.json"
        
        if not message_file.exists():
            raise ValueError(f"Message {message_id} not found")
        
        with open(message_file, 'r') as f:
            return json.load(f)
    
    def cleanup_old_messages(self, days: int = 30):
        """Clean up messages older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        message_dir = self.storage_path / "messages"
        
        if not message_dir.exists():
            return
        
        deleted_count = 0
        for message_file in message_dir.glob("*.json"):
            try:
                with open(message_file, 'r') as f:
                    message_data = json.load(f)
                
                metadata = MessageMetadata(**message_data['metadata'])
                
                if metadata.created_at:
                    message_date = datetime.fromisoformat(metadata.created_at)
                    
                    if message_date < cutoff_date:
                        message_file.unlink()
                        deleted_count += 1
            except Exception:
                continue
        
        return deleted_count
