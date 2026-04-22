"""
================================================================================
Q-MIND ENTERPRISE v3.6.2 - SIGNATURE BUNDLE CANONICAL CONTRACT
================================================================================

Module: signature_bundle.py

PURPOSE:
    Defines the canonical container for all digital signatures in Q-MIND.
    
    This ensures:
    1. Consistent signature representation across all modules
    2. Explicit type enforcement (prevents bytes vs object confusion)
    3. Full auditability and metadata tracking
    4. Deterministic serialization for reproducibility
    5. Clear API contracts for integration

DESIGN PRINCIPLES:
    • Immutable (frozen dataclass)
    • Self-documenting (explicit fields)
    • Type-safe (no raw bytes passed around)
    • Auditable (timestamp + version tracking)
    • Serializable (JSON-compatible)

VERSIONING:
    Introduced in: v3.6.2
    Reason: Integration API stabilization
    Backward Compatibility: Optional (v3.6.1 methods still accept bytes)

================================================================================
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json
from enum import Enum


class SignatureAlgorithmType(Enum):
    """Supported signature algorithms."""
    
    PQC_DILITHIUM_3 = "dilithium_3"      # FIPS 204
    CLASSICAL_HMAC_SHA256 = "hmac_sha256"
    CLASSICAL_ECDSA = "ecdsa_p256"
    LEGACY_V36 = "legacy_v3.6"  # For backward compatibility


@dataclass(frozen=True)
class SignatureBundle:
    """
    Canonical container for all digital signatures in Q-MIND.
    
    Attributes:
        signature_bytes: The actual signature (variable length based on algorithm)
        algorithm: Which algorithm produced this signature
        key_version: Version of the signing key (for rotation tracking)
        timestamp: When signature was created (UTC)
        entity_type: What was signed (threat_report, audit_log, etc.)
        signer_id: Optional identifier of signer (tenant, user, system)
        metadata: Additional metadata (optional)
    
    Notes:
        • Immutable to prevent accidental modification
        • All fields are required or have sensible defaults
        • Serializable to JSON for audit trails
        • Type-safe: can never be confused with raw bytes
    """
    
    # Core signature data
    signature_bytes: bytes
    algorithm: SignatureAlgorithmType
    key_version: int = 1
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Context information
    entity_type: Optional[str] = None  # e.g., "threat_report", "audit_log"
    signer_id: Optional[str] = None    # e.g., tenant_id, user_id
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "signature_bytes_hex": self.signature_bytes.hex(),
            "algorithm": self.algorithm.value,
            "key_version": self.key_version,
            "timestamp": self.timestamp.isoformat(),
            "entity_type": self.entity_type,
            "signer_id": self.signer_id,
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: dict) -> "SignatureBundle":
        """Reconstruct from dictionary."""
        return cls(
            signature_bytes=bytes.fromhex(data["signature_bytes_hex"]),
            algorithm=SignatureAlgorithmType(data["algorithm"]),
            key_version=data.get("key_version", 1),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
            entity_type=data.get("entity_type"),
            signer_id=data.get("signer_id"),
            metadata=data.get("metadata", {}),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "SignatureBundle":
        """Reconstruct from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @property
    def signature_length(self) -> int:
        """Length of signature in bytes."""
        return len(self.signature_bytes)
    
    def __repr__(self) -> str:
        """Human-readable representation."""
        sig_preview = self.signature_bytes[:8].hex() + "..." if len(self.signature_bytes) > 8 else self.signature_bytes.hex()
        return (
            f"SignatureBundle("
            f"algo={self.algorithm.value}, "
            f"len={self.signature_length}, "
            f"sig={sig_preview}, "
            f"v{self.key_version}, "
            f"@{self.timestamp.isoformat()}"
            f")"
        )


# ================================================================================
# SIGNATURE CREATION HELPERS
# ================================================================================

def create_signature_bundle(
    signature_bytes: bytes,
    algorithm: SignatureAlgorithmType = SignatureAlgorithmType.PQC_DILITHIUM_3,
    key_version: int = 1,
    entity_type: Optional[str] = None,
    signer_id: Optional[str] = None,
) -> SignatureBundle:
    """
    Create a signature bundle with standard fields.
    
    Args:
        signature_bytes: The actual signature
        algorithm: Which algorithm (defaults to Dilithium)
        key_version: Key version (for tracking rotation)
        entity_type: What was signed (optional)
        signer_id: Who signed (optional)
    
    Returns:
        SignatureBundle ready to use
    """
    return SignatureBundle(
        signature_bytes=signature_bytes,
        algorithm=algorithm,
        key_version=key_version,
        timestamp=datetime.utcnow(),
        entity_type=entity_type,
        signer_id=signer_id,
    )


# ================================================================================
# BACKWARD COMPATIBILITY
# ================================================================================

def bytes_to_signature_bundle(
    signature_bytes: bytes,
    algorithm: SignatureAlgorithmType = SignatureAlgorithmType.LEGACY_V36,
    key_version: int = 1,
) -> SignatureBundle:
    """
    Convert legacy raw bytes signature to SignatureBundle.
    
    Used for backward compatibility when v3.6.1 methods return raw bytes.
    
    Args:
        signature_bytes: Legacy signature as raw bytes
        algorithm: Algorithm that produced it (defaults to LEGACY_V36)
        key_version: Key version (default 1)
    
    Returns:
        SignatureBundle wrapping the bytes
    """
    return SignatureBundle(
        signature_bytes=signature_bytes,
        algorithm=algorithm,
        key_version=key_version,
        timestamp=datetime.utcnow(),
    )


def signature_bundle_to_bytes(bundle: SignatureBundle) -> bytes:
    """
    Extract raw bytes from SignatureBundle (for backward compatibility).
    
    Args:
        bundle: The signature bundle
    
    Returns:
        Raw signature bytes
    
    Note: This loses all metadata. Use only for compatibility with old APIs.
    """
    return bundle.signature_bytes
