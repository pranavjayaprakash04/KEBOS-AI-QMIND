"""
Production-Grade Lattice-Based Post-Quantum Cryptography Module

This module implements NIST-standardized post-quantum cryptographic algorithms using
the pqcrypto library which provides ML-KEM (Kyber) and ML-DSA (Dilithium) implementations.
"""

import os
import base64
import hashlib
import secrets
import json
from typing import Tuple, Dict, Any, Optional, Union, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Production PQC imports using pqcrypto library
try:
    import pqcrypto.kem.ml_kem_512 as ml_kem_512
    import pqcrypto.kem.ml_kem_768 as ml_kem_768
    import pqcrypto.kem.ml_kem_1024 as ml_kem_1024
    import pqcrypto.sign.ml_dsa_44 as ml_dsa_44
    import pqcrypto.sign.ml_dsa_65 as ml_dsa_65
    import pqcrypto.sign.ml_dsa_87 as ml_dsa_87
    PQCRYPTO_AVAILABLE = True
    logger.info("Using pqcrypto library for production lattice-based PQC")
except ImportError as e:
    PQCRYPTO_AVAILABLE = False
    logger.warning(f"pqcrypto library not available: {e}")

# Classical cryptography for hybrid encryption
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

class SecurityLevel(Enum):
    """Security levels for different PQC algorithms"""
    LEVEL_1 = "NIST_Level_1"  # 128-bit classical security
    LEVEL_3 = "NIST_Level_3"  # 192-bit classical security  
    LEVEL_5 = "NIST_Level_5"  # 256-bit classical security

class KEMAlgorithm(Enum):
    """Key Encapsulation Mechanism algorithms available in pqcrypto"""
    ML_KEM_512 = "ML-KEM-512"    # NIST Level 1 (128-bit security)
    ML_KEM_768 = "ML-KEM-768"    # NIST Level 3 (192-bit security) - RECOMMENDED
    ML_KEM_1024 = "ML-KEM-1024"  # NIST Level 5 (256-bit security)

class SignatureAlgorithm(Enum):
    """Digital signature algorithms available in pqcrypto"""
    ML_DSA_44 = "ML-DSA-44"     # NIST Level 2 (equivalent to 128-bit security)
    ML_DSA_65 = "ML-DSA-65"     # NIST Level 3 (192-bit security) - RECOMMENDED
    ML_DSA_87 = "ML-DSA-87"     # NIST Level 5 (256-bit security)

@dataclass
class PQCConfiguration:
    """Configuration for post-quantum cryptographic operations"""
    security_level: SecurityLevel
    kem_algorithm: KEMAlgorithm
    signature_algorithm: SignatureAlgorithm
    hybrid_mode: bool = True  # Use hybrid classical+PQ encryption
    key_rotation_interval: timedelta = timedelta(days=30)
    compression_enabled: bool = True  # Enable data compression before encryption
    
    @classmethod
    def get_recommended(cls) -> 'PQCConfiguration':
        """Get recommended production configuration (NIST Level 3)"""
        return cls(
            security_level=SecurityLevel.LEVEL_3,
            kem_algorithm=KEMAlgorithm.ML_KEM_768,
            signature_algorithm=SignatureAlgorithm.ML_DSA_65,
            hybrid_mode=True,
            compression_enabled=True
        )
    
    @classmethod
    def get_high_security(cls) -> 'PQCConfiguration':
        """Get high security configuration (NIST Level 5)"""
        return cls(
            security_level=SecurityLevel.LEVEL_5,
            kem_algorithm=KEMAlgorithm.ML_KEM_1024,
            signature_algorithm=SignatureAlgorithm.ML_DSA_87,
            hybrid_mode=True,
            compression_enabled=True
        )
    
    @classmethod
    def get_performance_optimized(cls) -> 'PQCConfiguration':
        """Get performance-optimized configuration (NIST Level 1)"""
        return cls(
            security_level=SecurityLevel.LEVEL_1,
            kem_algorithm=KEMAlgorithm.ML_KEM_512,
            signature_algorithm=SignatureAlgorithm.ML_DSA_44,
            hybrid_mode=True,
            compression_enabled=False  # Skip compression for better performance
        )

class LatticePQCrypto:
    """
    Production-grade lattice-based post-quantum cryptography implementation.
    
    Features:
    - NIST-standardized ML-KEM (Kyber) for key encapsulation
    - NIST-standardized ML-DSA (Dilithium) for digital signatures
    - Hybrid encryption combining PQ and classical algorithms
    - Multiple security levels (NIST Level 1, 3, 5)
    - Performance optimizations and error handling
    - Comprehensive logging and monitoring
    """
    
    def __init__(self, config: Optional[PQCConfiguration] = None):
        self.config = config or PQCConfiguration.get_recommended()
        self.backend = default_backend()
        
        # Validate pqcrypto library availability
        if not PQCRYPTO_AVAILABLE:
            raise RuntimeError("pqcrypto library is required for production PQC operations. Install with: pip install pqcrypto")
        
        # Initialize algorithm modules
        self._init_algorithms()
        
        logger.info(f"Initialized LatticePQCrypto with {self.config.security_level.value}")
        logger.info(f"KEM: {self.config.kem_algorithm.value}, Signature: {self.config.signature_algorithm.value}")
    
    def _init_algorithms(self):
        """Initialize the selected PQC algorithms"""
        # KEM algorithm selection
        if self.config.kem_algorithm == KEMAlgorithm.ML_KEM_512:
            self.kem_module = ml_kem_512
        elif self.config.kem_algorithm == KEMAlgorithm.ML_KEM_768:
            self.kem_module = ml_kem_768
        elif self.config.kem_algorithm == KEMAlgorithm.ML_KEM_1024:
            self.kem_module = ml_kem_1024
        else:
            raise ValueError(f"Unsupported KEM algorithm: {self.config.kem_algorithm}")
        
        # Signature algorithm selection
        if self.config.signature_algorithm == SignatureAlgorithm.ML_DSA_44:
            self.sig_module = ml_dsa_44
        elif self.config.signature_algorithm == SignatureAlgorithm.ML_DSA_65:
            self.sig_module = ml_dsa_65
        elif self.config.signature_algorithm == SignatureAlgorithm.ML_DSA_87:
            self.sig_module = ml_dsa_87
        else:
            raise ValueError(f"Unsupported signature algorithm: {self.config.signature_algorithm}")
    
    def generate_kem_keypair(self) -> Tuple[bytes, bytes]:
        """
        Generate a key encapsulation mechanism keypair.
        
        Returns:
            Tuple[bytes, bytes]: (public_key, private_key)
        """
        try:
            public_key, private_key = self.kem_module.generate_keypair()
            
            logger.debug(f"Generated KEM keypair using {self.config.kem_algorithm.value}")
            logger.debug(f"Public key size: {len(public_key)} bytes, Private key size: {len(private_key)} bytes")
            
            return public_key, private_key
        except Exception as e:
            logger.error(f"Failed to generate KEM keypair: {e}")
            raise RuntimeError(f"KEM keypair generation failed: {e}")
    
    def generate_signature_keypair(self) -> Tuple[bytes, bytes]:
        """
        Generate a digital signature keypair.
        
        Returns:
            Tuple[bytes, bytes]: (public_key, private_key)
        """
        try:
            public_key, private_key = self.sig_module.generate_keypair()
            
            logger.debug(f"Generated signature keypair using {self.config.signature_algorithm.value}")
            logger.debug(f"Public key size: {len(public_key)} bytes, Private key size: {len(private_key)} bytes")
            
            return public_key, private_key
        except Exception as e:
            logger.error(f"Failed to generate signature keypair: {e}")
            raise RuntimeError(f"Signature keypair generation failed: {e}")
    
    def generate_full_keypair(self) -> Dict[str, bytes]:
        """
        Generate complete keypair set for both KEM and signatures.
        
        Returns:
            Dict containing all public and private keys with metadata
        """
        kem_public, kem_private = self.generate_kem_keypair()
        sig_public, sig_private = self.generate_signature_keypair()
        
        return {
            'kem_public_key': kem_public,
            'kem_private_key': kem_private,
            'sig_public_key': sig_public,
            'sig_private_key': sig_private,
            'generated_at': datetime.now().isoformat().encode(),
            'algorithm_config': json.dumps({
                'kem': {
                    'name': self.config.kem_algorithm.value,
                    'public_key_size': len(kem_public),
                    'private_key_size': len(kem_private)
                },
                'signature': {
                    'name': self.config.signature_algorithm.value,
                    'public_key_size': len(sig_public),
                    'private_key_size': len(sig_private)
                },
                'config_security_level': self.config.security_level.value
            }).encode()
        }
    
    def encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes]:
        """
        Perform key encapsulation to establish shared secret.
        
        Args:
            public_key: Recipient's KEM public key
            
        Returns:
            Tuple[bytes, bytes]: (ciphertext, shared_secret)
        """
        try:
            ciphertext, shared_secret = self.kem_module.encrypt(public_key)
            
            logger.debug(f"Successfully performed key encapsulation")
            logger.debug(f"Ciphertext size: {len(ciphertext)} bytes, Shared secret size: {len(shared_secret)} bytes")
            
            return ciphertext, shared_secret
        except Exception as e:
            logger.error(f"Key encapsulation failed: {e}")
            raise RuntimeError(f"Encapsulation failed: {e}")
    
    def decapsulate(self, private_key: bytes, ciphertext: bytes) -> bytes:
        """
        Perform key decapsulation to recover shared secret.
        
        Args:
            private_key: Recipient's KEM private key
            ciphertext: Encapsulated key ciphertext
            
        Returns:
            bytes: Shared secret
        """
        try:
            shared_secret = self.kem_module.decrypt(private_key, ciphertext)
            
            logger.debug("Successfully performed key decapsulation")
            logger.debug(f"Recovered shared secret size: {len(shared_secret)} bytes")
            
            return shared_secret
        except Exception as e:
            logger.error(f"Key decapsulation failed: {e}")
            raise RuntimeError(f"Decapsulation failed: {e}")
    
    def sign_message(self, private_key: bytes, message: bytes) -> bytes:
        """
        Sign a message using post-quantum digital signatures.
        
        Args:
            private_key: Signer's private key
            message: Message to sign
            
        Returns:
            bytes: Digital signature
        """
        try:
            signature = self.sig_module.sign(private_key, message)
            
            logger.debug(f"Successfully signed message of {len(message)} bytes")
            logger.debug(f"Signature size: {len(signature)} bytes")
            
            return signature
        except Exception as e:
            logger.error(f"Message signing failed: {e}")
            raise RuntimeError(f"Signing failed: {e}")
    
    def verify_signature(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        """
        Verify a digital signature.
        
        Args:
            public_key: Signer's public key
            message: Original message
            signature: Digital signature to verify
            
        Returns:
            bool: True if signature is valid
        """
        try:
            # pqcrypto verify functions raise exception if invalid
            self.sig_module.verify(public_key, message, signature)
            logger.debug("Signature verification successful")
            return True
        except Exception as e:
            logger.debug(f"Signature verification failed: {e}")
            return False
    
    def derive_symmetric_key(self, shared_secret: bytes, context: bytes = b"lattice_pqc_messaging") -> bytes:
        """
        Derive a symmetric encryption key from the shared secret using HKDF.
        
        Args:
            shared_secret: Post-quantum shared secret
            context: Key derivation context
            
        Returns:
            bytes: 256-bit symmetric key
        """
        try:
            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,  # 256 bits for AES-256
                salt=None,
                info=context,
                backend=self.backend
            )
            symmetric_key = hkdf.derive(shared_secret)
            
            logger.debug("Successfully derived 256-bit symmetric key from PQ shared secret")
            return symmetric_key
        except Exception as e:
            logger.error(f"Key derivation failed: {e}")
            raise RuntimeError(f"Symmetric key derivation failed: {e}")
    
    def _compress_data(self, data: bytes) -> bytes:
        """Compress data before encryption if enabled"""
        if not self.config.compression_enabled:
            return data
        
        try:
            import zlib
            compressed = zlib.compress(data, level=6)  # Balanced compression
            logger.debug(f"Compressed data from {len(data)} to {len(compressed)} bytes")
            return compressed
        except Exception as e:
            logger.warning(f"Compression failed, using uncompressed data: {e}")
            return data
    
    def _decompress_data(self, data: bytes) -> bytes:
        """Decompress data after decryption if compression was enabled"""
        if not self.config.compression_enabled:
            return data
        
        try:
            import zlib
            decompressed = zlib.decompress(data)
            logger.debug(f"Decompressed data from {len(data)} to {len(decompressed)} bytes")
            return decompressed
        except Exception as e:
            logger.warning(f"Decompression failed, returning raw data: {e}")
            return data
    
    def hybrid_encrypt(self, 
                      plaintext: bytes, 
                      recipient_kem_public: bytes,
                      sender_sig_private: bytes) -> Dict[str, Any]:
        """
        Perform hybrid encryption combining PQ-KEM and classical symmetric encryption.
        
        Args:
            plaintext: Data to encrypt
            recipient_kem_public: Recipient's KEM public key
            sender_sig_private: Sender's signature private key
            
        Returns:
            Dict containing encrypted data and comprehensive metadata
        """
        try:
            start_time = datetime.now()
            
            # Step 1: Optional compression
            processed_data = self._compress_data(plaintext)
            
            # Step 2: Encapsulate to get shared secret
            kem_ciphertext, shared_secret = self.encapsulate(recipient_kem_public)
            
            # Step 3: Derive symmetric key
            symmetric_key = self.derive_symmetric_key(shared_secret)
            
            # Step 4: Encrypt data with AES-GCM
            aesgcm = AESGCM(symmetric_key)
            nonce = os.urandom(12)  # 96-bit nonce for GCM
            encrypted_data = aesgcm.encrypt(nonce, processed_data, None)
            
            # Step 5: Create authenticated data package
            metadata = {
                'algorithm': self.config.kem_algorithm.value,
                'signature_algorithm': self.config.signature_algorithm.value,
                'compression': self.config.compression_enabled,
                'timestamp': datetime.now().isoformat()
            }
            metadata_bytes = json.dumps(metadata).encode()
            
            # Step 6: Sign the entire package for authenticity
            message_to_sign = (
                kem_ciphertext + 
                nonce + 
                encrypted_data + 
                metadata_bytes
            )
            signature = self.sign_message(sender_sig_private, message_to_sign)
            
            # Step 7: Create final package
            processing_time = (datetime.now() - start_time).total_seconds()
            
            result = {
                'version': '1.0',
                'kem_ciphertext': base64.b64encode(kem_ciphertext).decode(),
                'nonce': base64.b64encode(nonce).decode(),
                'encrypted_data': base64.b64encode(encrypted_data).decode(),
                'signature': base64.b64encode(signature).decode(),
                'metadata': base64.b64encode(metadata_bytes).decode(),
                'algorithm_info': {
                    'kem': self.config.kem_algorithm.value,
                    'signature': self.config.signature_algorithm.value,
                    'symmetric': 'AES-256-GCM',
                    'security_level': self.config.security_level.value,
                    'compression_enabled': self.config.compression_enabled
                },
                'performance_metrics': {
                    'original_size': len(plaintext),
                    'compressed_size': len(processed_data),
                    'total_encrypted_size': len(kem_ciphertext) + len(encrypted_data) + len(signature),
                    'processing_time_seconds': processing_time
                },
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully encrypted {len(plaintext)} bytes using lattice-based hybrid PQC")
            logger.info(f"Compression ratio: {len(processed_data)/len(plaintext):.2f}, Processing time: {processing_time:.3f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Hybrid encryption failed: {e}")
            raise RuntimeError(f"Encryption failed: {e}")
    
    def hybrid_decrypt(self, 
                      encrypted_package: Dict[str, Any],
                      recipient_kem_private: bytes,
                      sender_sig_public: bytes) -> bytes:
        """
        Perform hybrid decryption and signature verification.
        
        Args:
            encrypted_package: Encrypted data package from hybrid_encrypt
            recipient_kem_private: Recipient's KEM private key
            sender_sig_public: Sender's signature public key
            
        Returns:
            bytes: Decrypted plaintext
        """
        try:
            start_time = datetime.now()
            
            # Validate package version
            if encrypted_package.get('version') != '1.0':
                raise ValueError("Unsupported encrypted package version")
            
            # Step 1: Decode base64 components
            kem_ciphertext = base64.b64decode(encrypted_package['kem_ciphertext'])
            nonce = base64.b64decode(encrypted_package['nonce'])
            encrypted_data = base64.b64decode(encrypted_package['encrypted_data'])
            signature = base64.b64decode(encrypted_package['signature'])
            metadata_bytes = base64.b64decode(encrypted_package['metadata'])
            
            # Step 2: Verify signature for authenticity
            message_to_verify = kem_ciphertext + nonce + encrypted_data + metadata_bytes
            if not self.verify_signature(sender_sig_public, message_to_verify, signature):
                raise RuntimeError("Signature verification failed - message may be tampered")
            
            # Step 3: Decapsulate to get shared secret
            shared_secret = self.decapsulate(recipient_kem_private, kem_ciphertext)
            
            # Step 4: Derive symmetric key
            symmetric_key = self.derive_symmetric_key(shared_secret)
            
            # Step 5: Decrypt data
            aesgcm = AESGCM(symmetric_key)
            decrypted_data = aesgcm.decrypt(nonce, encrypted_data, None)
            
            # Step 6: Parse metadata and handle decompression
            metadata = json.loads(metadata_bytes.decode())
            compression_was_used = metadata.get('compression', False)
            
            # Step 7: Optional decompression
            if compression_was_used:
                plaintext = self._decompress_data(decrypted_data)
            else:
                plaintext = decrypted_data
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Successfully decrypted {len(plaintext)} bytes using lattice-based hybrid PQC")
            logger.info(f"Processing time: {processing_time:.3f}s")
            
            return plaintext
            
        except Exception as e:
            logger.error(f"Hybrid decryption failed: {e}")
            raise RuntimeError(f"Decryption failed: {e}")

# Factory function for easy instantiation
def create_lattice_pqc(security_level: str = "recommended") -> LatticePQCrypto:
    """
    Factory function to create LatticePQCrypto instances.
    
    Args:
        security_level: "recommended", "high", "performance"
        
    Returns:
        LatticePQCrypto instance
    """
    if security_level == "high":
        config = PQCConfiguration.get_high_security()
    elif security_level == "performance":
        config = PQCConfiguration.get_performance_optimized()
    else:  # recommended
        config = PQCConfiguration.get_recommended()
    
    return LatticePQCrypto(config)

def get_available_algorithms() -> Dict[str, List[str]]:
    """Get list of available PQC algorithms from pqcrypto library."""
    if not PQCRYPTO_AVAILABLE:
        return {'error': ['pqcrypto library not available']}
    
    return {
        'kem_algorithms': [
            KEMAlgorithm.ML_KEM_512.value,
            KEMAlgorithm.ML_KEM_768.value,
            KEMAlgorithm.ML_KEM_1024.value
        ],
        'signature_algorithms': [
            SignatureAlgorithm.ML_DSA_44.value,
            SignatureAlgorithm.ML_DSA_65.value,
            SignatureAlgorithm.ML_DSA_87.value
        ]
    }

# Compatibility layer for secure_messaging.py
# These functions provide the same interface as the original crypto_pq module

def generate_user_keypair() -> Tuple[str, str]:
    """
    Generate a new user keypair for messaging using production lattice-based PQC.
    
    Returns:
        Tuple[str, str]: (private_key_b64, public_key_b64)
    """
    try:
        pqc = create_lattice_pqc("recommended")
        keypair = pqc.generate_full_keypair()
        
        # Encode the full keypair as JSON and then base64 for compatibility
        private_key_data = {
            'kem_private_key': base64.b64encode(keypair['kem_private_key']).decode('utf-8'),
            'sig_private_key': base64.b64encode(keypair['sig_private_key']).decode('utf-8'),
            'algorithm_config': keypair['algorithm_config'].decode('utf-8'),
            'generated_at': keypair['generated_at'].decode('utf-8')
        }
        
        public_key_data = {
            'kem_public_key': base64.b64encode(keypair['kem_public_key']).decode('utf-8'),
            'sig_public_key': base64.b64encode(keypair['sig_public_key']).decode('utf-8'),
            'algorithm_config': keypair['algorithm_config'].decode('utf-8'),
            'generated_at': keypair['generated_at'].decode('utf-8')
        }
        
        private_key_json = json.dumps(private_key_data)
        public_key_json = json.dumps(public_key_data)
        
        return (
            base64.b64encode(private_key_json.encode()).decode('utf-8'),
            base64.b64encode(public_key_json.encode()).decode('utf-8')
        )
        
    except Exception as e:
        logger.error(f"Failed to generate user keypair: {e}")
        raise RuntimeError(f"User keypair generation failed: {e}")

def save_keypair(user_id: str, private_key: str, public_key: str, key_storage_path: str = "./keys"):
    """
    Save user keypair to secure storage.
    
    Args:
        user_id: Unique identifier for the user
        private_key: Base64-encoded private key JSON
        public_key: Base64-encoded public key JSON
        key_storage_path: Directory to store keys
    """
    try:
        os.makedirs(key_storage_path, exist_ok=True)
        
        # Decode the keys to get the original JSON
        private_key_json = base64.b64decode(private_key).decode('utf-8')
        public_key_json = base64.b64decode(public_key).decode('utf-8')
        
        keypair_data = {
            'user_id': user_id,
            'private_key': private_key,  # Store as base64-encoded JSON
            'public_key': public_key,    # Store as base64-encoded JSON
            'private_key_decoded': json.loads(private_key_json),  # Store decoded for debugging
            'public_key_decoded': json.loads(public_key_json),    # Store decoded for debugging
            'created_at': datetime.now().isoformat(),
            'algorithm': 'Production-ML-KEM-768+ML-DSA-65',
            'version': '1.0.0'
        }
        
        keypair_file = os.path.join(key_storage_path, f"{user_id}_keypair.json")
        with open(keypair_file, 'w') as f:
            json.dump(keypair_data, f, indent=2)
            
        logger.info(f"Saved keypair for user {user_id} to {keypair_file}")
        
    except Exception as e:
        logger.error(f"Failed to save keypair for user {user_id}: {e}")
        raise RuntimeError(f"Keypair save failed: {e}")

def load_keypair(user_id: str, key_storage_path: str = "./keys") -> Tuple[str, str]:
    """
    Load user keypair from storage.
    
    Args:
        user_id: Unique identifier for the user
        key_storage_path: Directory containing keys
        
    Returns:
        Tuple[str, str]: (private_key_b64, public_key_b64)
    """
    try:
        keypair_file = os.path.join(key_storage_path, f"{user_id}_keypair.json")
        
        with open(keypair_file, 'r') as f:
            keypair_data = json.load(f)
            
        private_key = keypair_data['private_key']
        public_key = keypair_data['public_key']
        
        logger.info(f"Loaded keypair for user {user_id} from {keypair_file}")
        
        return private_key, public_key
        
    except FileNotFoundError:
        raise ValueError(f"Keypair not found for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to load keypair for user {user_id}: {e}")
        raise RuntimeError(f"Keypair load failed: {e}")

# Create a MessageCrypto class for compatibility with secure_messaging.py
class MessageCrypto:
    """
    Compatibility wrapper for the original MessageCrypto interface.
    Uses production lattice-based PQC internally.
    """
    
    def __init__(self, security_level: str = "recommended"):
        """Initialize with production lattice-based PQC."""
        self.pqc = create_lattice_pqc(security_level)
        self.key_cache = {}  # Store shared secrets for channels
        logger.info(f"Initialized MessageCrypto with production lattice-based PQC")
    
    def create_secure_channel(self, sender_private_key: bytes, receiver_public_key: bytes) -> Dict[str, Any]:
        """
        Create a secure communication channel between sender and receiver.
        
        Args:
            sender_private_key: Not used in current implementation (for compatibility)
            receiver_public_key: Raw KEM public key bytes or encoded public key
            
        Returns:
            Dict containing channel info with encapsulated shared secret
        """
        try:
            # If receiver_public_key is a string (base64 encoded JSON), decode it
            if isinstance(receiver_public_key, str):
                receiver_public_json = json.loads(base64.b64decode(receiver_public_key).decode('utf-8'))
                receiver_kem_public = base64.b64decode(receiver_public_json['kem_public_key'])
            else:
                # Assume it's raw bytes from the secure_messaging module context
                receiver_kem_public = receiver_public_key
            
            # Perform key encapsulation using production PQC
            ciphertext, shared_secret = self.pqc.encapsulate(receiver_kem_public)
            
            # Create channel identifier
            channel_id = hashlib.sha256(
                ciphertext + shared_secret + os.urandom(16)
            ).hexdigest()[:16]
            
            # Store shared secret securely
            self.key_cache[channel_id] = shared_secret
            
            logger.info(f"Created secure channel {channel_id} using production lattice PQC")
            
            return {
                'channel_id': channel_id,
                'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
                'algorithm': f'Production-{self.pqc.config.kem_algorithm.value}',
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create secure channel: {e}")
            raise RuntimeError(f"Secure channel creation failed: {e}")
    
    def establish_channel(self, channel_info: Dict[str, Any], receiver_private_key: bytes) -> str:
        """
        Establish secure channel on receiver side.
        
        Args:
            channel_info: Channel information from create_secure_channel
            receiver_private_key: Raw KEM private key bytes or encoded private key
            
        Returns:
            str: Channel ID for communication
        """
        try:
            ciphertext = base64.b64decode(channel_info['ciphertext'])
            
            # If receiver_private_key is a string (base64 encoded JSON), decode it
            if isinstance(receiver_private_key, str):
                receiver_private_json = json.loads(base64.b64decode(receiver_private_key).decode('utf-8'))
                receiver_kem_private = base64.b64decode(receiver_private_json['kem_private_key'])
            else:
                # Assume it's raw bytes
                receiver_kem_private = receiver_private_key
            
            # Decapsulate shared secret using production PQC
            shared_secret = self.pqc.decapsulate(receiver_kem_private, ciphertext)
            
            # Store shared secret
            channel_id = channel_info['channel_id']
            self.key_cache[channel_id] = shared_secret
            
            logger.info(f"Established secure channel {channel_id}")
            
            return channel_id
            
        except Exception as e:
            logger.error(f"Failed to establish channel: {e}")
            raise RuntimeError(f"Channel establishment failed: {e}")
    
    def encrypt_and_sign(self, 
                        data: bytes, 
                        channel_id: str, 
                        sender_private_key: bytes,
                        message_type: str = 'text') -> Dict[str, Any]:
        """
        Encrypt message and create digital signature using production PQC.
        
        Args:
            data: Message bytes to encrypt
            channel_id: Established channel identifier
            sender_private_key: Raw signature private key bytes or encoded private key
            message_type: Type of message (text, image, etc.)
            
        Returns:
            Dict containing encrypted and signed message
        """
        try:
            if channel_id not in self.key_cache:
                raise ValueError(f"Channel {channel_id} not established")
            
            shared_secret = self.key_cache[channel_id]
            
            # Encrypt the message using AES-GCM with the shared secret
            aesgcm = AESGCM(shared_secret)
            nonce = os.urandom(12)  # 96-bit nonce for GCM
            encrypted_data = aesgcm.encrypt(nonce, data, None)
            
            # Create message payload
            message_payload = {
                'channel_id': channel_id,
                'message_type': message_type,
                'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8'),
                'nonce': base64.b64encode(nonce).decode('utf-8'),
                'timestamp': datetime.now().isoformat()
            }
            
            # Sign the entire payload
            payload_bytes = json.dumps(message_payload, sort_keys=True).encode('utf-8')
            
            # If sender_private_key is a string (base64 encoded JSON), decode it
            if isinstance(sender_private_key, str):
                sender_private_json = json.loads(base64.b64decode(sender_private_key).decode('utf-8'))
                sender_sig_private = base64.b64decode(sender_private_json['sig_private_key'])
            else:
                # Assume it's raw bytes
                sender_sig_private = sender_private_key
            
            signature = self.pqc.sign_message(sender_sig_private, payload_bytes)
            
            logger.debug(f"Encrypted and signed {len(data)} bytes for channel {channel_id}")
            
            return {
                'payload': message_payload,
                'signature': base64.b64encode(signature).decode('utf-8'),
                'signature_algorithm': f'Production-{self.pqc.config.signature_algorithm.value}'
            }
            
        except Exception as e:
            logger.error(f"Failed to encrypt and sign message: {e}")
            raise RuntimeError(f"Encryption and signing failed: {e}")
    
    def verify_and_decrypt(self, 
                          signed_message: Dict[str, Any],
                          channel_id: str,
                          sender_public_key: bytes) -> bytes:
        """
        Verify signature and decrypt message using production PQC.
        
        Args:
            signed_message: Signed and encrypted message from encrypt_and_sign
            channel_id: Channel identifier
            sender_public_key: Raw signature public key bytes or encoded public key
            
        Returns:
            bytes: Decrypted message
        """
        try:
            if channel_id not in self.key_cache:
                raise ValueError(f"Channel {channel_id} not established")
            
            # Verify signature
            payload = signed_message['payload']
            signature = base64.b64decode(signed_message['signature'])
            payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
            
            # If sender_public_key is a string (base64 encoded JSON), decode it
            if isinstance(sender_public_key, str):
                sender_public_json = json.loads(base64.b64decode(sender_public_key).decode('utf-8'))
                sender_sig_public = base64.b64decode(sender_public_json['sig_public_key'])
            else:
                # Assume it's raw bytes
                sender_sig_public = sender_public_key
            
            if not self.pqc.verify_signature(sender_sig_public, payload_bytes, signature):
                raise ValueError("Signature verification failed")
            
            # Decrypt message
            shared_secret = self.key_cache[channel_id]
            encrypted_data = base64.b64decode(payload['encrypted_data'])
            nonce = base64.b64decode(payload['nonce'])
            
            aesgcm = AESGCM(shared_secret)
            decrypted_data = aesgcm.decrypt(nonce, encrypted_data, None)
            
            logger.debug(f"Verified and decrypted {len(decrypted_data)} bytes for channel {channel_id}")
            
            return decrypted_data
            
        except Exception as e:
            logger.error(f"Failed to verify and decrypt message: {e}")
            raise RuntimeError(f"Verification and decryption failed: {e}")
    
    def cleanup_channel(self, channel_id: str):
        """
        Clean up channel and remove shared secrets.
        """
        if channel_id in self.key_cache:
            del self.key_cache[channel_id]
            logger.info(f"Cleaned up channel {channel_id}")
    
    def encrypt_message(self, message: bytes, receiver_public_key: str, sender_private_key: str) -> Dict[str, Any]:
        """
        Encrypt a message using the production PQC system.
        
        Args:
            message: Message bytes to encrypt
            receiver_public_key: Base64-encoded receiver public key JSON
            sender_private_key: Base64-encoded sender private key JSON
            
        Returns:
            Dict containing encrypted message and metadata
        """
        try:
            # Decode the keys
            receiver_public_json = json.loads(base64.b64decode(receiver_public_key).decode('utf-8'))
            sender_private_json = json.loads(base64.b64decode(sender_private_key).decode('utf-8'))
            
            # Extract the raw key bytes
            receiver_kem_public = base64.b64decode(receiver_public_json['kem_public_key'])
            sender_sig_private = base64.b64decode(sender_private_json['sig_private_key'])
            
            # Encrypt using production PQC
            encrypted_result = self.pqc.hybrid_encrypt(message, receiver_kem_public, sender_sig_private)
            
            # Convert to string format for compatibility
            return {
                'encrypted_data': base64.b64encode(json.dumps(encrypted_result).encode()).decode('utf-8'),
                'algorithm': 'Production-Lattice-PQC',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Message encryption failed: {e}")
            raise RuntimeError(f"Encryption failed: {e}")
    
    def decrypt_message(self, encrypted_data: str, receiver_private_key: str, sender_public_key: str) -> bytes:
        """
        Decrypt a message using the production PQC system.
        
        Args:
            encrypted_data: Base64-encoded encrypted message JSON
            receiver_private_key: Base64-encoded receiver private key JSON
            sender_public_key: Base64-encoded sender public key JSON
            
        Returns:
            bytes: Decrypted message
        """
        try:
            # Decode the encrypted data
            encrypted_result = json.loads(base64.b64decode(encrypted_data).decode('utf-8'))
            
            # Decode the keys
            receiver_private_json = json.loads(base64.b64decode(receiver_private_key).decode('utf-8'))
            sender_public_json = json.loads(base64.b64decode(sender_public_key).decode('utf-8'))
            
            # Extract the raw key bytes
            receiver_kem_private = base64.b64decode(receiver_private_json['kem_private_key'])
            sender_sig_public = base64.b64decode(sender_public_json['sig_public_key'])
            
            # Decrypt using production PQC
            decrypted_message = self.pqc.hybrid_decrypt(encrypted_result, receiver_kem_private, sender_sig_public)
            
            return decrypted_message
            
        except Exception as e:
            logger.error(f"Message decryption failed: {e}")
            raise RuntimeError(f"Decryption failed: {e}")

if __name__ == "__main__":
    # Test the production lattice-based PQC implementation
    print("=" * 60)
    print("Testing Production Lattice-Based PQC Implementation")
    print("=" * 60)
    
    if not PQCRYPTO_AVAILABLE:
        print("❌ pqcrypto library not available")
        print("Install with: pip install pqcrypto")
        exit(1)
    
    try:
        # Show available algorithms
        algorithms = get_available_algorithms()
        print(f"\n🔍 Available Algorithms:")
        print(f"KEM Algorithms: {algorithms['kem_algorithms']}")
        print(f"Signature Algorithms: {algorithms['signature_algorithms']}")
        
        # Test recommended configuration
        config = PQCConfiguration.get_recommended()
        pqc = LatticePQCrypto(config)
        
        print(f"\n🧪 Testing {config.kem_algorithm.value} + {config.signature_algorithm.value}")
        
        # Performance test
        test_message = b"Testing production lattice-based PQC with NIST-standardized algorithms!" * 50
        start_time = datetime.now()
        
        # Generate test keypairs
        alice_keys = pqc.generate_full_keypair()
        bob_keys = pqc.generate_full_keypair()
        
        print(f"✅ Generated keypairs")
        
        # Test encryption/decryption
        encrypted = pqc.hybrid_encrypt(
            test_message,
            bob_keys['kem_public_key'],
            alice_keys['sig_private_key']
        )
        
        print(f"✅ Encrypted {len(test_message)} bytes")
        
        decrypted = pqc.hybrid_decrypt(
            encrypted,
            bob_keys['kem_private_key'],
            alice_keys['sig_public_key']
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Validate results
        test_passed = test_message == decrypted
        print(f"{'✅' if test_passed else '❌'} Encryption/Decryption: {'PASSED' if test_passed else 'FAILED'}")
        print(f"📊 Total Processing Time: {processing_time:.3f}s")
        print(f"📈 Compression Ratio: {encrypted['performance_metrics']['compressed_size'] / len(test_message):.2f}")
        print(f"⚡ Throughput: {(len(test_message) / 1024 / 1024) / processing_time:.2f} MB/s")
        
        if test_passed:
            print(f"\n🎉 Production lattice-based PQC is working correctly!")
            print(f"🔐 Using NIST-standardized {config.kem_algorithm.value} and {config.signature_algorithm.value}")
        else:
            print(f"\n❌ Test failed!")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
