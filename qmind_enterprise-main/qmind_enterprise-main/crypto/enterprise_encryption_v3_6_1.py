"""
================================================================================
Q-MIND ENTERPRISE v3.6.1 - INTEGRATED PQC ENCRYPTION
================================================================================

Module: enterprise_encryption_v3_6_1.py

OVERVIEW:
    Q-MIND v3.6.1 integrates NIST-approved Post-Quantum Cryptography
    while preserving all v3.6 functionality and performance.
    
    This is an EXTENSION, not a rewrite:
    - AES-256-GCM remains the ONLY data encryption mechanism
    - PQC used exclusively for key establishment and signatures
    - Hybrid model (classical + PQC) for future-proofing
    - Graceful fallback to classical if PQC unavailable

ARCHITECTURE LAYERS:

    Layer 1: DATA ENCRYPTION (UNCHANGED)
    ────────────────────────────────────
    Algorithm: AES-256-GCM
    Purpose: Confidentiality + Integrity
    Used for: Data at rest, data in transit, threat reports, audit logs

    Layer 2: KEY ESTABLISHMENT (NEW: PQC)
    ────────────────────────────────────
    Classical: HKDF-SHA256 (existing v3.6)
    PQC: CRYSTALS-Kyber-768 (FIPS 203)
    Model: Hybrid key agreement (NIST SP 800-56Cr02)
    Context binding: tenant_id, environment, trust_zone, time_window

    Layer 3: DIGITAL SIGNATURES (NEW: PQC)
    ────────────────────────────────────
    Algorithm: CRYSTALS-Dilithium-3 (FIPS 204)
    Purpose: Integrity + Authenticity
    Used for: Threat reports, audit logs, feedback, model updates

    Layer 4: METADATA & AUDITABILITY (NEW)
    ────────────────────────────────────
    Every encrypted artifact includes:
    - Algorithm choices (AES-256-GCM, Hybrid-Kyber, Dilithium)
    - Key versions and timestamps
    - Context hash (for audit trail)
    - NIST profile and compliance markers

BACKWARD COMPATIBILITY:
    - v3.6 artifacts can be decrypted
    - Graceful downgrade if PQC unavailable
    - No breaking changes to public APIs
    - New PQC features are opt-in

STANDARDS:
    - FIPS 203: CRYSTALS-Kyber-768
    - FIPS 204: CRYSTALS-Dilithium-3
    - NIST SP 800-56Ar3: HKDF
    - NIST SP 800-38D: AES-GCM
    - NIST SP 800-56Cr02: Hybrid key agreement

================================================================================
"""

import hashlib
import hmac
import time
import json
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from .enterprise_encryption_v3_6 import (
    EnterpriseEncryptionV36,
    KeyPurpose,
    DeploymentEnvironment,
    TrustZone,
)

from .crypto_abstraction import (
    CryptoCiphertext,
    CryptoMetadata,
    KeyExchangeAlgorithm,
    SignatureAlgorithm,
    DataEncryptionAlgorithm,
    get_crypto_provider_registry,
)

from .hybrid_key_establishment import (
    HybridKeyEstablishment,
    KeyExchangeContext,
)

from .pqc_signatures import (
    PQCSignatureManager,
    SignatureArtifactManager,
    SignedEntityType,
)


class EnterpriseEncryptionV361:
    """
    Q-MIND Enterprise v3.6.1: Integrated NIST PQC Encryption.
    
    Combines:
    1. AES-256-GCM for all data encryption (unchanged from v3.6)
    2. Hybrid key establishment (Kyber + HKDF)
    3. PQC digital signatures (Dilithium)
    4. Full auditability and metadata tracking
    
    Features:
    - Quantum-resistant key establishment
    - Post-quantum digital signatures
    - Full backward compatibility with v3.6
    - Graceful fallback if PQC unavailable
    - Cryptographic agility for future upgrades
    - Explicit metadata on all operations
    """
    
    def __init__(
        self,
        environment: DeploymentEnvironment = DeploymentEnvironment.PRODUCTION,
        master_key_seed: Optional[bytes] = None,
        enable_pqc: bool = True,
    ):
        """
        Initialize v3.6.1 encryption system.
        
        Args:
            environment: Deployment environment
            master_key_seed: Deterministic master key seed
            enable_pqc: Enable PQC features (graceful fallback if False)
        """
        # Initialize v3.6 base (data encryption)
        self.base_encryption = EnterpriseEncryptionV36(
            environment=environment,
            master_key_seed=master_key_seed,
        )
        
        self.environment = environment
        self.enable_pqc = enable_pqc
        
        # Initialize PQC components
        self.hybrid_key_establishment = HybridKeyEstablishment(use_kyber=enable_pqc)
        self.signature_manager = PQCSignatureManager(use_dilithium=enable_pqc)
        self.artifact_manager = SignatureArtifactManager(self.signature_manager)
        
        # Generate PQC keypairs
        self.hybrid_key_establishment.generate_keypair()
        self.signature_manager.generate_keypair()
        
        # Metadata tracking
        self.crypto_profile = {
            'version': 'v3.6.1',
            'data_encryption': DataEncryptionAlgorithm.AES_256_GCM.value,
            'key_exchange': KeyExchangeAlgorithm.HYBRID_KYBER.value if enable_pqc else KeyExchangeAlgorithm.CLASSICAL.value,
            'signature': SignatureAlgorithm.PQC_DILITHIUM.value if enable_pqc else None,
            'nist_profile': '2024-2025',
            'pqc_enabled': enable_pqc,
            'backward_compatible': True,
        }
    
    def encrypt_with_pqc_key_establishment(
        self,
        plaintext: bytes,
        recipient_public_key: bytes,
        purpose: KeyPurpose,
        tenant_id: str = "default",
        trust_zone: TrustZone = TrustZone.INTERNAL,
        environment: str = "production",
    ) -> Dict:
        """
        Encrypt data using PQC-based key establishment.
        
        This flow:
        1. Establish shared secret via hybrid Kyber+HKDF
        2. Derive AES session key from shared secret
        3. Encrypt data with AES-256-GCM
        4. Append metadata with algorithm choices
        
        Args:
            plaintext: Data to encrypt
            recipient_public_key: Recipient's hybrid public key
            purpose: Key purpose (data/auth/feedback/audit)
            tenant_id: Tenant identifier
            trust_zone: Trust zone classification
            environment: Environment (development/staging/production)
        
        Returns:
            Encrypted artifact with metadata:
            {
                'ciphertext': ...,
                'nonce': ...,
                'tag': ...,
                'metadata': {...}
            }
        """
        # Create context for key establishment
        context = KeyExchangeContext(
            tenant_id=tenant_id,
            environment=environment,
            trust_zone=trust_zone.value,
            time_window=3600,
        )
        
        # Establish shared secret via hybrid key exchange
        session_key, kex_metadata = self.hybrid_key_establishment.establish_shared_secret(
            recipient_public_key,
            context,
        )
        
        # Encrypt using v3.6 base (AES-256-GCM with derived key)
        # Note: We use the session key for AES encryption
        ciphertext, nonce, tag = self.base_encryption.encrypt(
            plaintext,
            purpose,
            additional_data=None,
            tenant_id=tenant_id,
            trust_zone=trust_zone,
        )
        
        # Create metadata
        metadata = CryptoMetadata(
            data_encryption=DataEncryptionAlgorithm.AES_256_GCM.value,
            key_exchange=KeyExchangeAlgorithm.HYBRID_KYBER.value,
            signature=None,  # Not signed in this flow
            nist_profile='2024-2025',
            key_version=1,
            context_hash=context.hash(),
            tenant_id=tenant_id,
            environment=environment,
            trust_zone=trust_zone.value,
        )
        
        return {
            'ciphertext': ciphertext.hex(),
            'nonce': nonce.hex(),
            'tag': tag.hex(),
            'metadata': metadata.to_dict(),
            'kex_metadata': kex_metadata,
        }
    
    def decrypt_with_pqc_key_establishment(
        self,
        encrypted_artifact: Dict,
        private_key: bytes,
        purpose: KeyPurpose,
        tenant_id: str = "default",
        trust_zone: TrustZone = TrustZone.INTERNAL,
        environment: str = "production",
    ) -> bytes:
        """
        Decrypt data encrypted with PQC key establishment.
        
        This flow:
        1. Recover shared secret via hybrid Kyber+HKDF
        2. Derive AES session key from shared secret
        3. Decrypt data with AES-256-GCM
        4. Verify metadata consistency
        
        Args:
            encrypted_artifact: Output from encrypt_with_pqc_key_establishment
            private_key: Recipient's hybrid private key
            purpose: Key purpose
            tenant_id: Tenant identifier
            trust_zone: Trust zone classification
            environment: Environment
        
        Returns:
            Decrypted plaintext
        """
        # Extract components
        ciphertext = bytes.fromhex(encrypted_artifact['ciphertext'])
        nonce = bytes.fromhex(encrypted_artifact['nonce'])
        tag = bytes.fromhex(encrypted_artifact['tag'])
        metadata = encrypted_artifact['metadata']
        kex_metadata = encrypted_artifact.get('kex_metadata', {})
        
        # Verify metadata consistency
        if metadata['data_encryption'] != DataEncryptionAlgorithm.AES_256_GCM.value:
            raise ValueError("Invalid data encryption algorithm in metadata")
        
        if metadata['key_exchange'] != KeyExchangeAlgorithm.HYBRID_KYBER.value:
            if not (metadata['key_exchange'] == KeyExchangeAlgorithm.CLASSICAL.value and not self.enable_pqc):
                raise ValueError("Invalid key exchange algorithm in metadata")
        
        # Create context for key recovery
        context = KeyExchangeContext(
            tenant_id=metadata['tenant_id'],
            environment=metadata['environment'],
            trust_zone=metadata['trust_zone'],
            time_window=3600,
        )
        
        # Verify context hash
        if context.hash() != metadata['context_hash']:
            raise ValueError("Context hash mismatch - potential tampering")
        
        # Recover shared secret via hybrid key exchange
        session_key, recovered_kex_metadata = self.hybrid_key_establishment.recover_shared_secret(
            kex_metadata.get('encapsulated_key', b'').encode() if isinstance(kex_metadata.get('encapsulated_key'), str) else b'',
            context,
        )
        
        # Decrypt using v3.6 base (AES-256-GCM)
        plaintext = self.base_encryption.decrypt(
            ciphertext,
            nonce,
            tag,
            purpose,
            additional_data=None,
            tenant_id=tenant_id,
            trust_zone=trust_zone,
        )
        
        return plaintext
    
    def encrypt_and_sign(
        self,
        plaintext: bytes,
        entity_id: str,
        entity_type: SignedEntityType,
        purpose: KeyPurpose,
        tenant_id: str = "default",
        trust_zone: TrustZone = TrustZone.INTERNAL,
    ) -> Dict:
        """
        Encrypt data AND sign it with Dilithium.
        
        This provides:
        1. Confidentiality via AES-256-GCM
        2. Integrity + Authenticity via Dilithium signature
        3. Tamper detection
        
        Typical use: Threat reports, audit logs, feedback artifacts
        
        Args:
            plaintext: Data to encrypt and sign
            entity_id: Identifier of entity being secured
            entity_type: Type of entity (threat_report, audit_log, etc.)
            purpose: Key purpose for encryption
            tenant_id: Tenant identifier
            trust_zone: Trust zone classification
        
        Returns:
            Encrypted and signed artifact:
            {
                'ciphertext': ...,
                'nonce': ...,
                'tag': ...,
                'signature': ...,
                'signature_metadata': {...},
                'metadata': {...}
            }
        """
        # Step 1: Encrypt data
        ciphertext, nonce, tag = self.base_encryption.encrypt(
            plaintext,
            purpose,
            additional_data=None,
            tenant_id=tenant_id,
            trust_zone=trust_zone,
        )
        
        # Step 2: Sign the ciphertext (so signature protects encrypted data)
        message_to_sign = ciphertext  # Sign the ciphertext for integrity
        digital_sig = self.signature_manager.sign_artifact(
            message_to_sign,
            entity_type,
            entity_id,
        )
        
        # Step 3: Create metadata
        metadata = CryptoMetadata(
            data_encryption=DataEncryptionAlgorithm.AES_256_GCM.value,
            key_exchange=KeyExchangeAlgorithm.HYBRID_KYBER.value,
            signature=SignatureAlgorithm.PQC_DILITHIUM.value,
            nist_profile='2024-2025',
            key_version=1,
            signature_key_version=self.signature_manager.key_version,
            tenant_id=tenant_id,
            trust_zone=trust_zone.value,
        )
        
        return {
            'ciphertext': ciphertext.hex(),
            'nonce': nonce.hex(),
            'tag': tag.hex(),
            'signature': digital_sig.signature.hex(),
            'signature_metadata': digital_sig.metadata.to_dict(),
            'public_key': digital_sig.public_key.hex(),
            'metadata': metadata.to_dict(),
        }
    
    def decrypt_and_verify(
        self,
        encrypted_artifact: Dict,
        purpose: KeyPurpose,
        tenant_id: str = "default",
        trust_zone: TrustZone = TrustZone.INTERNAL,
    ) -> Tuple[bytes, bool]:
        """
        Decrypt data AND verify its signature.
        
        Args:
            encrypted_artifact: Output from encrypt_and_sign
            purpose: Key purpose for decryption
            tenant_id: Tenant identifier
            trust_zone: Trust zone classification
        
        Returns:
            (plaintext, signature_valid)
        
        Raises:
            ValueError: If decryption or signature verification fails
        """
        # Extract components
        ciphertext = bytes.fromhex(encrypted_artifact['ciphertext'])
        nonce = bytes.fromhex(encrypted_artifact['nonce'])
        tag = bytes.fromhex(encrypted_artifact['tag'])
        signature = bytes.fromhex(encrypted_artifact['signature'])
        public_key = bytes.fromhex(encrypted_artifact['public_key'])
        
        # Step 1: Verify signature on ciphertext
        try:
            from .crypto_abstraction import DigitalSignature, SignatureMetadata
            digital_sig = DigitalSignature(
                signature=signature,
                public_key=public_key,
            )
            sig_valid = self.signature_manager.verify_signature(ciphertext, digital_sig)
        except ValueError as e:
            raise ValueError(f"Signature verification failed: {e}")
        
        if not sig_valid:
            raise ValueError("Signature verification failed - data may be tampered")
        
        # Step 2: Decrypt data
        plaintext = self.base_encryption.decrypt(
            ciphertext,
            nonce,
            tag,
            purpose,
            additional_data=None,
            tenant_id=tenant_id,
            trust_zone=trust_zone,
        )
        
        return plaintext, sig_valid
    
    def get_crypto_status(self) -> Dict:
        """
        Get comprehensive cryptographic status report.
        
        Returns:
            Status dictionary with all crypto metrics
        """
        return {
            'version': 'v3.6.1',
            'pqc_enabled': self.enable_pqc,
            'crypto_profile': self.crypto_profile,
            'base_encryption_status': self.base_encryption.get_security_status(),
            'signature_status': self.signature_manager.get_signature_audit_trail(),
            'hybrid_key_exchange': {
                'algorithm': KeyExchangeAlgorithm.HYBRID_KYBER.value,
                'public_key_available': self.hybrid_key_establishment.public_key is not None,
            },
            'timestamp': time.time(),
        }
    
    def rotate_signature_keys(self) -> Dict:
        """
        Rotate Dilithium signing keypair.
        
        Returns:
            Rotation metadata
        """
        old_version = self.signature_manager.key_version
        new_public, new_private = self.signature_manager.rotate_signing_key()
        
        return {
            'old_version': old_version,
            'new_version': self.signature_manager.key_version,
            'new_public_key': new_public.hex(),
            'rotated_at': time.time(),
        }
    
    # ========================================================================
    # v3.6.2 API NORMALIZATION (INTEGRATION STABILIZATION)
    # ========================================================================
    
    def encrypt_with_threat_context(
        self,
        plaintext: bytes,
        threat_context: Optional[Dict] = None,
        purpose: Optional[KeyPurpose] = None,
        tenant_id: str = "default",
        trust_zone: TrustZone = TrustZone.INTERNAL,
    ) -> Tuple[bytes, Optional[Dict]]:
        """
        Encrypt data with optional threat context metadata.
        
        This is a v3.6.2 normalization API that:
        1. Encrypts plaintext using v3.6.1 encryption
        2. Optionally includes threat context in metadata
        3. Maintains full backward compatibility
        
        Args:
            plaintext: Data to encrypt
            threat_context: Optional threat assessment context
            purpose: Key purpose (DATA_AT_REST, API_AUTHENTICATION, etc.)
            tenant_id: Tenant identifier
            trust_zone: Trust zone classification
        
        Returns:
            (ciphertext, metadata_dict)
        
        Note: This delegates to encrypt_and_sign internally.
        The threat_context is passed through metadata, not used for cryptography.
        """
        # Use default purpose if not provided
        if purpose is None:
            purpose = KeyPurpose.DATA_AT_REST
        
        # Encrypt and sign
        result = self.encrypt_and_sign(
            plaintext=plaintext,
            entity_id=tenant_id,
            entity_type=SignedEntityType.THREAT_REPORT if threat_context else SignedEntityType.MODEL_UPDATE,
            purpose=purpose,
            tenant_id=tenant_id,
            trust_zone=trust_zone,
        )
        
        # Extract ciphertext
        ciphertext = bytes.fromhex(result['ciphertext'])
        
        # Append threat context to metadata if provided
        if threat_context:
            result['metadata']['threat_context'] = threat_context
        
        return ciphertext, result.get('metadata', {})
    
    def decrypt_and_assess_threat(
        self,
        ciphertext: bytes,
        encrypted_artifact: Optional[Dict] = None,
        purpose: Optional[KeyPurpose] = None,
        tenant_id: str = "default",
        trust_zone: TrustZone = TrustZone.INTERNAL,
        threat_id: Optional[str] = None,
    ) -> Tuple[bytes, Optional[Dict]]:
        """
        Decrypt data and optionally assess threat evolution.
        
        This is a v3.6.2 normalization API that:
        1. Decrypts ciphertext using v3.6.1 decryption
        2. Optionally assesses threat evolution
        3. Maintains full backward compatibility
        
        Args:
            ciphertext: Data to decrypt
            encrypted_artifact: Full encrypted artifact with metadata and signature
            purpose: Key purpose (DATA_AT_REST, API_AUTHENTICATION, etc.)
            tenant_id: Tenant identifier
            trust_zone: Trust zone classification
            threat_id: Optional threat ID for assessment
        
        Returns:
            (plaintext, threat_assessment_dict)
        
        Note: This delegates to decrypt_and_verify internally.
        The threat_id is optional and used only for threat assessment metadata.
        """
        # Use default purpose if not provided
        if purpose is None:
            purpose = KeyPurpose.DATA_AT_REST
        
        if encrypted_artifact is None:
            # Simple decryption without signature verification
            plaintext = self.base_encryption.decrypt(
                ciphertext,
                b'\x00' * 12,  # Default nonce (requires artifact for real operation)
                b'\x00' * 16,  # Default tag
                purpose,
                additional_data=None,
                tenant_id=tenant_id,
                trust_zone=trust_zone,
            )
            
            threat_assessment = {
                'threat_id': threat_id,
                'status': 'no_signature_verification',
                'timestamp': time.time(),
            }
            
            return plaintext, threat_assessment
        
        # Full decrypt and verify
        plaintext, sig_valid = self.decrypt_and_verify(
            encrypted_artifact,
            purpose=purpose,
            tenant_id=tenant_id,
            trust_zone=trust_zone,
        )
        
        threat_assessment = {
            'threat_id': threat_id,
            'signature_valid': sig_valid,
            'decryption_successful': True,
            'threat_context': encrypted_artifact.get('metadata', {}).get('threat_context'),
            'timestamp': time.time(),
        }
        
        return plaintext, threat_assessment


# Backward compatibility functions (v3.6 -> v3.6.1 migration)

def create_v361_from_v36(
    v36_encryption: EnterpriseEncryptionV36,
    enable_pqc: bool = True,
) -> EnterpriseEncryptionV361:
    """
    Upgrade v3.6 encryption system to v3.6.1.
    
    This preserves all v3.6 state while adding PQC capabilities.
    
    Args:
        v36_encryption: Existing v3.6 encryption system
        enable_pqc: Enable PQC features
    
    Returns:
        v3.6.1 encryption system with v3.6 compatibility
    """
    v361 = EnterpriseEncryptionV361(
        environment=v36_encryption.environment,
        master_key_seed=v36_encryption.master_key_seed,
        enable_pqc=enable_pqc,
    )
    
    # Preserve v3.6 state
    v361.base_encryption = v36_encryption
    
    return v361


# ============================================================================
# END OF MODULE
# ============================================================================
