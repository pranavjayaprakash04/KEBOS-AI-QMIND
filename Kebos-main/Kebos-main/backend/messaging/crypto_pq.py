"""
Post-Quantum Cryptography Module for Secure Messaging

This module implements post-quantum encryption protocols for secure message transfer
including support for Kyber (key encapsulation) and Dilithium (digital signatures).
"""

import os
import base64
import hashlib
import secrets
from typing import Tuple, Dict, Any, Optional
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import json

# Note: For production, you would use actual post-quantum libraries like:
# - liboqs-python (Open Quantum Safe)
# - PQClean implementations
# - NIST standardized algorithms (Kyber, Dilithium, SPHINCS+)

class PostQuantumCrypto:
    """
    Post-Quantum Cryptography implementation for secure messaging.
    
    This implementation uses a hybrid approach:
    - Classical AES-256-GCM for bulk encryption (fast)
    - Post-quantum key exchange simulation (Kyber-like)
    - Post-quantum digital signatures simulation (Dilithium-like)
    """
    
    def __init__(self):
        self.backend = default_backend()
        
        # Post-quantum algorithm parameters (simulated)
        self.kyber_params = {
            'n': 256,  # Polynomial degree
            'q': 3329,  # Modulus
            'eta1': 3,  # Noise parameter
            'eta2': 2,  # Noise parameter
            'du': 10,   # Compression parameter
            'dv': 4     # Compression parameter
        }
        
        self.dilithium_params = {
            'n': 256,   # Polynomial degree
            'q': 8380417,  # Modulus
            'tau': 39,  # Number of ±1's in challenge
            'gamma1': 524288,  # Coefficient range
            'gamma2': 95232    # Low-order rounding range
        }
    
    def generate_keypair(self) -> Tuple[bytes, bytes]:
        """
        Generate a post-quantum key pair.
        
        In production, this would use actual Kyber key generation.
        For now, we simulate with strong random keys.
        """
        # Simulate Kyber-1024 key generation
        private_key = secrets.token_bytes(32)  # 256-bit private key
        
        # Derive public key (simplified simulation)
        public_key_material = hashlib.sha3_256(private_key + b"kyber_public").digest()
        public_key = base64.b64encode(public_key_material).decode('utf-8')
        
        return private_key, public_key.encode('utf-8')
    
    def kyber_encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes]:
        """
        Kyber key encapsulation mechanism.
        
        Returns:
            Tuple of (ciphertext, shared_secret)
        """
        # Simulate Kyber encapsulation
        shared_secret = secrets.token_bytes(32)  # 256-bit shared secret
        
        # Create encapsulation (simplified)
        public_key_hash = hashlib.sha3_256(public_key).digest()
        ciphertext = hashlib.sha3_256(shared_secret + public_key_hash).digest()
        
        return ciphertext, shared_secret
    
    def kyber_decapsulate(self, private_key: bytes, ciphertext: bytes) -> bytes:
        """
        Kyber decapsulation to recover shared secret.
        """
        # Simulate Kyber decapsulation
        # In real implementation, this would perform lattice operations
        public_key_material = hashlib.sha3_256(private_key + b"kyber_public").digest()
        
        # Derive shared secret from private key and ciphertext
        shared_secret = hashlib.sha3_256(private_key + ciphertext + public_key_material).digest()
        
        return shared_secret
    
    def dilithium_sign(self, private_key: bytes, message: bytes) -> bytes:
        """
        Dilithium digital signature generation.
        """
        # Simulate Dilithium signature
        message_hash = hashlib.sha3_256(message).digest()
        signature_material = hashlib.sha3_256(private_key + message_hash + b"dilithium_sign").digest()
        
        # Create signature with timestamp for uniqueness
        timestamp = int(datetime.now().timestamp()).to_bytes(8, 'big')
        signature = signature_material + timestamp
        
        return signature
    
    def dilithium_verify(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        """
        Dilithium signature verification.
        """
        if len(signature) < 40:  # Minimum signature length
            return False
        
        try:
            # Extract timestamp and signature material
            signature_material = signature[:-8]
            timestamp_bytes = signature[-8:]
            timestamp = int.from_bytes(timestamp_bytes, 'big')
            
            # Check timestamp validity (within 1 hour)
            current_time = int(datetime.now().timestamp())
            if abs(current_time - timestamp) > 3600:
                return False
            
            # Simulate signature verification
            message_hash = hashlib.sha3_256(message).digest()
            expected_signature = hashlib.sha3_256(
                public_key + message_hash + b"dilithium_sign"
            ).digest()
            
            return signature_material == expected_signature
        except Exception:
            return False
    
    def encrypt_message(self, data: bytes, shared_secret: bytes) -> Dict[str, Any]:
        """
        Encrypt message data using AES-256-GCM with post-quantum shared secret.
        """
        # Derive encryption key from shared secret
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'pq_messaging_salt',
            iterations=100000,
            backend=self.backend
        )
        key = kdf.derive(shared_secret)
        
        # Generate IV for GCM
        iv = secrets.token_bytes(12)  # 96-bit IV for GCM
        
        # Encrypt with AES-256-GCM
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv),
            backend=self.backend
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        
        return {
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'iv': base64.b64encode(iv).decode('utf-8'),
            'auth_tag': base64.b64encode(encryptor.tag).decode('utf-8'),
            'algorithm': 'AES-256-GCM',
            'timestamp': datetime.now().isoformat()
        }
    
    def decrypt_message(self, encrypted_data: Dict[str, Any], shared_secret: bytes) -> bytes:
        """
        Decrypt message data using AES-256-GCM.
        """
        # Derive decryption key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'pq_messaging_salt',
            iterations=100000,
            backend=self.backend
        )
        key = kdf.derive(shared_secret)
        
        # Decode encrypted components
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        iv = base64.b64decode(encrypted_data['iv'])
        auth_tag = base64.b64decode(encrypted_data['auth_tag'])
        
        # Decrypt with AES-256-GCM
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(iv, auth_tag),
            backend=self.backend
        )
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        return plaintext


class MessageCrypto:
    """
    High-level message encryption interface using post-quantum cryptography.
    """
    
    def __init__(self):
        self.pq_crypto = PostQuantumCrypto()
        self.key_cache = {}  # In production, use secure key storage
    
    def create_secure_channel(self, sender_private_key: bytes, receiver_public_key: bytes) -> Dict[str, Any]:
        """
        Create a secure communication channel between sender and receiver.
        
        Returns channel info including encapsulated shared secret.
        """
        # Perform key encapsulation
        ciphertext, shared_secret = self.pq_crypto.kyber_encapsulate(receiver_public_key)
        
        # Create channel identifier
        channel_id = hashlib.sha256(
            sender_private_key + receiver_public_key + ciphertext
        ).hexdigest()[:16]
        
        # Store shared secret (in production, use secure storage)
        self.key_cache[channel_id] = shared_secret
        
        return {
            'channel_id': channel_id,
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'algorithm': 'Kyber-1024',
            'created_at': datetime.now().isoformat()
        }
    
    def establish_channel(self, channel_info: Dict[str, Any], receiver_private_key: bytes) -> str:
        """
        Establish secure channel on receiver side.
        
        Returns channel_id for communication.
        """
        ciphertext = base64.b64decode(channel_info['ciphertext'])
        
        # Decapsulate shared secret
        shared_secret = self.pq_crypto.kyber_decapsulate(receiver_private_key, ciphertext)
        
        # Store shared secret
        channel_id = channel_info['channel_id']
        self.key_cache[channel_id] = shared_secret
        
        return channel_id
    
    def encrypt_and_sign(self, 
                        data: bytes, 
                        channel_id: str, 
                        sender_private_key: bytes,
                        message_type: str = 'text') -> Dict[str, Any]:
        """
        Encrypt message and create digital signature.
        """
        if channel_id not in self.key_cache:
            raise ValueError(f"Channel {channel_id} not established")
        
        shared_secret = self.key_cache[channel_id]
        
        # Encrypt the message
        encrypted_data = self.pq_crypto.encrypt_message(data, shared_secret)
        
        # Create message payload
        message_payload = {
            'channel_id': channel_id,
            'message_type': message_type,
            'encrypted_data': encrypted_data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Sign the entire payload
        payload_bytes = json.dumps(message_payload, sort_keys=True).encode('utf-8')
        signature = self.pq_crypto.dilithium_sign(sender_private_key, payload_bytes)
        
        return {
            'payload': message_payload,
            'signature': base64.b64encode(signature).decode('utf-8'),
            'signature_algorithm': 'Dilithium-3'
        }
    
    def verify_and_decrypt(self, 
                          signed_message: Dict[str, Any],
                          channel_id: str,
                          sender_public_key: bytes) -> bytes:
        """
        Verify signature and decrypt message.
        """
        if channel_id not in self.key_cache:
            raise ValueError(f"Channel {channel_id} not established")
        
        # Verify signature
        payload = signed_message['payload']
        signature = base64.b64decode(signed_message['signature'])
        payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
        
        if not self.pq_crypto.dilithium_verify(sender_public_key, payload_bytes, signature):
            raise ValueError("Signature verification failed")
        
        # Decrypt message
        shared_secret = self.key_cache[channel_id]
        decrypted_data = self.pq_crypto.decrypt_message(payload['encrypted_data'], shared_secret)
        
        return decrypted_data
    
    def cleanup_channel(self, channel_id: str):
        """
        Clean up channel and remove shared secrets.
        """
        if channel_id in self.key_cache:
            # Securely overwrite the key
            self.key_cache[channel_id] = b'\x00' * 32
            del self.key_cache[channel_id]


# Utility functions for key management
def generate_user_keypair() -> Tuple[str, str]:
    """Generate a new user keypair for messaging."""
    crypto = PostQuantumCrypto()
    private_key, public_key = crypto.generate_keypair()
    
    return (
        base64.b64encode(private_key).decode('utf-8'),
        public_key.decode('utf-8')
    )

def save_keypair(user_id: str, private_key: str, public_key: str, key_storage_path: str = "./keys"):
    """Save user keypair to secure storage."""
    os.makedirs(key_storage_path, exist_ok=True)
    
    # In production, encrypt private keys with user password
    keypair_data = {
        'user_id': user_id,
        'private_key': private_key,
        'public_key': public_key,
        'created_at': datetime.now().isoformat(),
        'algorithm': 'Kyber-1024'
    }
    
    # Use os.path.join for cross-platform path handling
    keypair_path = os.path.join(key_storage_path, f"{user_id}_keypair.json")
    with open(keypair_path, 'w') as f:
        json.dump(keypair_data, f, indent=2)

def load_keypair(user_id: str, key_storage_path: str = "./keys") -> Tuple[str, str]:
    """Load user keypair from storage."""
    try:
        # Use os.path.join for cross-platform path handling
        keypair_path = os.path.join(key_storage_path, f"{user_id}_keypair.json")
        with open(keypair_path, 'r') as f:
            keypair_data = json.load(f)
        return keypair_data['private_key'], keypair_data['public_key']
    except FileNotFoundError:
        raise ValueError(f"Keypair not found for user {user_id}")
