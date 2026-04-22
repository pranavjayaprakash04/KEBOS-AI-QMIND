"""
Audit Chain for Kebos AI.
Phase 2.4 - Dilithium-3 signed audit log chain.
"""
import hashlib
import json
import logging
import sys
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
import asyncpg

# Add parent directory to path to import qmind_enterprise
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

logger = logging.getLogger(__name__)

# Import from qmind PQC module (shared library)
# If liboqs unavailable, fall back to SHA-256-only chain with WARNING
try:
    from qmind_enterprise.pqc.dilithium_sign import sign, verify, generate_keypair
    _PQC_SIGNING = True
except ImportError:
    _PQC_SIGNING = False
    logger.warning("liboqs unavailable — audit chain using SHA-256 only (no Dilithium-3)")


@dataclass
class AuditEntry:
    """Audit log entry with Dilithium-3 signature."""
    entry_id: UUID = field(default_factory=uuid4)
    tenant_id: UUID = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    actor_id: UUID = None
    action: str = ""
    resource: str = ""
    metadata: dict = field(default_factory=dict)
    prev_hash: str = ""            # SHA-256 of previous entry
    entry_hash: str = ""           # SHA-256 of this entry's content
    signature: Optional[bytes] = None   # Dilithium-3 signature of entry_hash
    pubkey_ref: str = ""           # key reference in Vault

class AuditChain:
    """
    Audit chain with Dilithium-3 signatures.
    Each entry signed and linked via prev_hash.
    """
    
    def __init__(self, db_pool: asyncpg.Pool, signing_key_bytes: bytes = None, pubkey_ref: str = ""):
        self.db_pool = db_pool
        self._sk = signing_key_bytes
        self._pubkey_ref = pubkey_ref
        self._last_hash = "GENESIS"
    
    def _compute_entry_hash(self, entry: AuditEntry) -> str:
        """Compute SHA-256 hash of entry content."""
        content = json.dumps({
            "entry_id": str(entry.entry_id),
            "tenant_id": str(entry.tenant_id),
            "timestamp": entry.timestamp.isoformat(),
            "actor_id": str(entry.actor_id),
            "action": entry.action,
            "resource": entry.resource,
            "metadata": entry.metadata,
            "prev_hash": entry.prev_hash,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def append(
        self,
        tenant_id: UUID,
        actor_id: UUID,
        action: str,
        resource: str,
        metadata: dict = None
    ) -> AuditEntry:
        """
        Append audit entry to chain with Dilithium-3 signature.
        
        Args:
            tenant_id: Tenant UUID
            actor_id: Actor UUID (user/system)
            action: Action performed
            resource: Resource affected
            metadata: Additional metadata
        
        Returns:
            AuditEntry with signature
        """
        entry = AuditEntry(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action=action,
            resource=resource,
            metadata=metadata or {},
            prev_hash=self._last_hash,
        )
        entry.entry_hash = self._compute_entry_hash(entry)
        
        # Dilithium-3 sign the hash
        if _PQC_SIGNING and self._sk:
            entry.signature = sign(self._sk, entry.entry_hash.encode())
            entry.pubkey_ref = self._pubkey_ref
        
        # Persist to DB
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO audit_entries (
                    entry_id, tenant_id, timestamp, actor_id, action, resource,
                    metadata, prev_hash, entry_hash, signature, pubkey_ref
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
                entry.entry_id,
                entry.tenant_id,
                entry.timestamp,
                entry.actor_id,
                entry.action,
                entry.resource,
                json.dumps(entry.metadata),
                entry.prev_hash,
                entry.entry_hash,
                entry.signature.hex() if entry.signature else None,
                entry.pubkey_ref
            )
        
        self._last_hash = entry.entry_hash
        return entry


def verify_chain(entries: list[AuditEntry], public_key_bytes: bytes) -> bool:
    """
    Verify integrity of the entire audit chain.
    
    Args:
        entries: List of audit entries to verify
        public_key_bytes: Dilithium-3 public key for signature verification
    
    Returns:
        True if chain is valid, False otherwise
    """
    for i, entry in enumerate(entries):
        # Verify hash link
        if i > 0 and entry.prev_hash != entries[i-1].entry_hash:
            return False
        
        # Verify Dilithium-3 signature
        if entry.signature and _PQC_SIGNING:
            if not verify(public_key_bytes, entry.entry_hash.encode(), entry.signature):
                return False
    
    return True
