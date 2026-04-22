"""
Messaging module initialization and setup.
"""

import asyncio
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Use absolute imports to avoid relative import issues
try:
    from db import Base, engine, SessionLocal
    DB_AVAILABLE = True
except ImportError:
    # When testing crypto modules independently, database might not be available
    Base = None
    engine = None
    SessionLocal = None
    DB_AVAILABLE = False
    logger.warning("Database components not available - some functions will be limited")

# Import models and crypto only if available
try:
    from .models import (
        UserKeypairORM, SecureChannelORM, SecureMessageORM, 
        MessageAttachmentORM, MessageReactionORM, MessageAuditLogORM,
        MessageType, MessageStatus, ChannelType, EncryptionAlgorithm
    )
    MODELS_AVAILABLE = True
except ImportError:
    # Models depend on database, skip if not available
    MODELS_AVAILABLE = False
    logger.warning("Database models not available")

# Import crypto module - this should work independently
try:
    from .lattice_pqc import LatticePQCrypto
    LATTICE_PQC_AVAILABLE = True
except ImportError:
    LATTICE_PQC_AVAILABLE = False
    logger.warning("Lattice PQC module not available")

# Ensure messaging storage directory exists
MESSAGING_STORAGE_DIR = Path("messaging_storage")
MESSAGING_STORAGE_DIR.mkdir(exist_ok=True)
ENCRYPTED_FILES_DIR = MESSAGING_STORAGE_DIR / "encrypted_files"
ENCRYPTED_FILES_DIR.mkdir(exist_ok=True)

def create_messaging_tables():
    """Create all messaging-related database tables."""
    if not DB_AVAILABLE:
        logger.warning("Database not available - cannot create tables")
        return False
        
    try:
        # Create all tables defined in models
        assert Base is not None and engine is not None, "Database components not properly initialized"
        Base.metadata.create_all(bind=engine)
        logger.info("Messaging tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to create messaging tables: {e}")
        return False

def init_default_pq_config():
    """Initialize default post-quantum cryptographic configuration."""
    try:
        # For now, just return True since we're using simulated PQC
        # In production, this would set up real PQC parameters
        logger.info("Post-quantum configuration ready (using simulation)")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize default PQ config: {e}")
        return False

def init_user_keypairs_and_quotas():
    """Initialize keypairs and quotas for existing users."""
    if not DB_AVAILABLE:
        logger.warning("Database not available - cannot initialize user keypairs")
        return False
        
    try:
        assert SessionLocal is not None, "SessionLocal not properly initialized"
        db = SessionLocal()
        
        # This would typically get users from your auth system
        # For now, we'll just set up the structure
        
        # Example: Create a default quota configuration
        # You would adapt this to your actual user system
        logger.info("User keypairs and quotas initialization ready")
        
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize user keypairs and quotas: {e}")
        return False

def verify_crypto_system():
    """Verify that the post-quantum crypto system is working."""
    if not LATTICE_PQC_AVAILABLE:
        logger.warning("Lattice PQC not available - cannot verify crypto system")
        return False
        
    try:
        # Test the production lattice-based crypto system
        crypto = LatticePQCrypto()
        
        # Generate test keypairs
        kem_public, kem_private = crypto.generate_kem_keypair()
        sig_public, sig_private = crypto.generate_signature_keypair()
        
        # Test KEM
        ciphertext, shared_secret = crypto.encapsulate(kem_public)
        decrypted_secret = crypto.decapsulate(kem_private, ciphertext)
        
        if shared_secret != decrypted_secret:
            raise Exception("KEM test failed")
        
        # Test signatures
        message = b"Test message for signature verification"
        signature = crypto.sign_message(sig_private, message)
        
        if not crypto.verify_signature(sig_public, message, signature):
            raise Exception("Signature verification failed")
        
        # Test hybrid encryption/decryption
        plaintext = b"Test message for encryption"
        encrypted_result = crypto.hybrid_encrypt(plaintext, kem_public, sig_private)
        decrypted_data = crypto.hybrid_decrypt(encrypted_result, kem_private, sig_public)
        
        if plaintext != decrypted_data:
            raise Exception("Message encryption test failed")
        
        logger.info("✅ Production lattice-based PQC system verification successful")
        return True
        
    except Exception as e:
        logger.error(f"Crypto system verification failed: {e}")
        return False

async def init_messaging_system():
    """Initialize the complete messaging system."""
    logger.info("Initializing secure messaging system...")
    
    steps = [
        ("Creating database tables", create_messaging_tables),
        ("Initializing PQ configuration", init_default_pq_config),
        ("Setting up user system", init_user_keypairs_and_quotas),
        ("Verifying crypto system", verify_crypto_system)
    ]
    
    for step_name, step_func in steps:
        logger.info(f"Step: {step_name}")
        try:
            success = step_func()
            if not success:
                logger.error(f"Failed: {step_name}")
                return False
            logger.info(f"Completed: {step_name}")
        except Exception as e:
            logger.error(f"Error in {step_name}: {e}")
            return False
    
    logger.info("Secure messaging system initialized successfully!")
    return True

def cleanup_expired_data():
    """Clean up expired messages, files, and audit logs."""
    if not DB_AVAILABLE or not MODELS_AVAILABLE:
        logger.warning("Database or models not available - cannot cleanup data")
        return False
        
    try:
        from datetime import datetime, timedelta
        assert SessionLocal is not None, "SessionLocal not properly initialized"
        db = SessionLocal()
        
        # Example cleanup - adjust retention periods as needed
        cutoff_date = datetime.now() - timedelta(days=30)  # 30 days retention
        
        # Clean up old audit logs
        old_logs = db.query(MessageAuditLogORM).filter(MessageAuditLogORM.timestamp < cutoff_date).count()
        if old_logs > 0:
            db.query(MessageAuditLogORM).filter(MessageAuditLogORM.timestamp < cutoff_date).delete()
            logger.info(f"Cleaned up {old_logs} old audit log entries")
        
        # Clean up expired attachments (if message is deleted)
        message_ids = [msg_id for msg_id, in db.query(SecureMessageORM.id).all()]
        orphaned_attachments = db.query(MessageAttachmentORM).filter(
            ~MessageAttachmentORM.message_id.in_(message_ids)
        ).count()
        
        if orphaned_attachments > 0:
            db.query(MessageAttachmentORM).filter(
                ~MessageAttachmentORM.message_id.in_(message_ids)
            ).delete(synchronize_session=False)
            logger.info(f"Cleaned up {orphaned_attachments} orphaned attachments")
        
        db.commit()
        db.close()
        
        logger.info("Data cleanup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}")
        return False

# Database health check
def check_messaging_db_health():
    """Check the health of messaging database components."""
    if not DB_AVAILABLE or not MODELS_AVAILABLE:
        return {
            "overall_health": "unavailable",
            "error": "Database components not available for testing"
        }
        
    try:
        assert SessionLocal is not None, "SessionLocal not properly initialized"
        db = SessionLocal()
        
        # Check if we can query each table
        tables_to_check = [
            UserKeypairORM, SecureChannelORM, SecureMessageORM, MessageAuditLogORM, 
            MessageAttachmentORM
        ]
        
        health_status = {}
        
        for table in tables_to_check:
            try:
                count = db.query(table).count()
                health_status[table.__tablename__] = {
                    "status": "healthy",
                    "record_count": count
                }
            except Exception as e:
                health_status[table.__tablename__] = {
                    "status": "error",
                    "error": str(e)
                }
        
        db.close()
        
        # Overall health
        all_healthy = all(
            status["status"] == "healthy" 
            for status in health_status.values()
        )
        
        return {
            "overall_health": "healthy" if all_healthy else "degraded",
            "tables": health_status,
            "storage_directory": str(MESSAGING_STORAGE_DIR),
            "encrypted_files_directory": str(ENCRYPTED_FILES_DIR)
        }
        
    except Exception as e:
        return {
            "overall_health": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    # Run initialization if script is executed directly
    import asyncio
    asyncio.run(init_messaging_system())
