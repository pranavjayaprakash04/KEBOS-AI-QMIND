"""Test messaging models import"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

try:
    print("Testing common.models import...")
    from common.models import Base
    print("✅ common.models import successful")
    
    print("\nTesting messaging models import...")
    from messaging.models import (
        UserKeypairORM, SecureChannelORM, SecureMessageORM, 
        MessageAttachmentORM, MessageReactionORM, MessageAuditLogORM,
        MessageType, MessageStatus, ChannelType, EncryptionAlgorithm
    )
    print("✅ All messaging models imported successfully!")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
