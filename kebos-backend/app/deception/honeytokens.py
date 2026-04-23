"""
Honeytoken Manager for Kebos AI Deception Grid.
Phase 4.1 - Manages honeytoken creation, deployment, and triggering.
Honeytoken trigger = confirmed breach, confidence=1.0 (bypasses ALL thresholds).
"""
import logging
import secrets
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncpg
from app.config import settings
from app.integrations.egress_client import get_egress_client

logger = logging.getLogger(__name__)


class HoneytokenType(Enum):
    """Supported honeytoken types"""
    AWS_KEY = "aws_key"
    DB_PASSWORD = "db_password"
    API_KEY = "api_key"
    UPI_CRED = "upi_cred"
    SWIFT_TOKEN = "swift_token"


@dataclass
class Honeytoken:
    """Honeytoken record"""
    id: int
    tenant_id: int
    token_type: str
    value: str
    description: str
    deployed_at: datetime
    triggered_at: Optional[datetime] = None
    is_active: bool = True


class HoneytokenManager:
    """
    Manages honeytoken lifecycle.
    Honeytoken trigger = confirmed breach, injects at confidence=1.0.
    """
    
    TOKEN_TYPES = {
        HoneytokenType.AWS_KEY: ("AKIA" + secrets.token_urlsafe(12).upper()[:16], "CloudTrail access attempt"),
        HoneytokenType.DB_PASSWORD: (f"honey_{secrets.token_hex(8)}_db", "Database authentication attempt"),
        HoneytokenType.API_KEY: (f"sk-honey-{secrets.token_hex(16)}", "API authentication attempt"),
        HoneytokenType.UPI_CRED: (f"upi_honey_{secrets.token_hex(8)}@kebos", "UPI validation attempt"),
        HoneytokenType.SWIFT_TOKEN: (f"swift_honey_{secrets.token_hex(8)}", "SWIFT API call attempt"),
    }
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.egress_client = get_egress_client()
        self._honeytoken_cache = {}  # In-memory cache: {token_value: Honeytoken}
        self._cache_loaded = False
    
    async def _load_cache(self):
        """Load active honeytokens into memory cache"""
        if self._cache_loaded:
            return
        
        async with self.db_pool.acquire() as conn:
            active_tokens = await conn.fetch("""
                SELECT id, tenant_id, token_type, value, description, deployed_at
                FROM honeytokens
                WHERE is_active = true
            """)
        
        for token_row in active_tokens:
            honeytoken = Honeytoken(
                id=token_row["id"],
                tenant_id=token_row["tenant_id"],
                token_type=token_row["token_type"],
                value=token_row["value"],
                description=token_row["description"],
                deployed_at=token_row["deployed_at"],
                is_active=True
            )
            self._honeytoken_cache[honeytoken.value] = honeytoken
        
        self._cache_loaded = True
        logger.info(f"Loaded {len(self._honeytoken_cache)} honeytokens into cache")
    
    async def create_honeytoken(
        self,
        tenant_id: int,
        token_type: HoneytokenType,
        description: Optional[str] = None
    ) -> Honeytoken:
        """
        Create a new honeytoken.
        
        Args:
            tenant_id: Tenant ID
            token_type: Type of honeytoken
            description: Optional description
        
        Returns:
            Honeytoken record
        """
        token_value, default_desc = self.TOKEN_TYPES.get(token_type, ("unknown", "Unknown"))
        desc = description or default_desc
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO honeytokens (tenant_id, token_type, value, description, deployed_at, is_active)
                VALUES ($1, $2, $3, $4, NOW(), true)
                RETURNING id, tenant_id, token_type, value, description, deployed_at, is_active
            """, tenant_id, token_type.value, token_value, desc)
            
            honeytoken = Honeytoken(
                id=row["id"],
                tenant_id=row["tenant_id"],
                token_type=row["token_type"],
                value=row["value"],
                description=row["description"],
                deployed_at=row["deployed_at"],
                is_active=row["is_active"]
            )
            
            # Add to cache
            self._honeytoken_cache[honeytoken.value] = honeytoken
            
            logger.info(f"Created honeytoken {honeytoken.id} ({token_type.value}) for tenant {tenant_id}")
            return honeytoken
    
    async def check_request_for_honeytokens(
        self,
        request_body: bytes,
        request_headers: Dict[str, str],
        client_ip: str
    ) -> Optional[Honeytoken]:
        """
        Check if request contains any honeytokens.
        Called in main.py middleware - checks every request.
        Uses in-memory cache to avoid DB query on every request.
        
        Args:
            request_body: Request body bytes
            request_headers: Request headers dict
            client_ip: Client IP address
        
        Returns:
            Triggered honeytoken if found, None otherwise
        """
        # Load cache on first call
        await self._load_cache()
        
        # Combine body and headers for full content check
        body_str = request_body.decode('utf-8', errors='ignore')
        full_content = json.dumps({
            "body": body_str,
            "headers": request_headers
        })
        
        # Check against cached honeytokens
        for token_value, honeytoken in self._honeytoken_cache.items():
            if token_value in full_content:
                # Honeytoken triggered!
                await self._trigger_honeytoken_alert(honeytoken, client_ip, request_body, request_headers)
                return honeytoken
        
        return None
    
    async def _trigger_honeytoken_alert(
        self,
        token: Honeytoken,
        client_ip: str,
        request_body: bytes,
        request_headers: Dict[str, str]
    ):
        """
        Honeytoken = confirmed breach. confidence=1.0 — bypasses ALL thresholds.
        Injects to QMind at maximum confidence.
        """
        logger.critical(
            f"HONEYTOKEN TRIGGERED: {token.token_type} (ID: {token.id}) "
            f"from IP {client_ip} - CONFIRMED BREACH"
        )
        
        # Update honeytoken status
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE honeytokens
                SET triggered_at = NOW(), is_active = false
                WHERE id = $1
            """, token.id)
        
        # Inject to QMind at confidence=1.0 (ONLY signal in system at 1.0)
        try:
            await self.egress_client.post(
                "http://qmind:8001/signals/inject",
                json={
                    "indicator_value": client_ip,
                    "indicator_type": "ip",
                    "source": "honeytoken",
                    "confidence": 1.0,  # MAXIMUM - bypasses ALL thresholds
                    "tenant_id": str(token.tenant_id),
                    "metadata": {
                        "honeytoken_id": str(token.id),
                        "honeytoken_type": token.token_type,
                        "trigger": "honeytoken_used",
                        "request_headers": request_headers,
                        "request_body_preview": request_body[:500].decode('utf-8', errors='ignore') if request_body else "",
                    }
                }
            )
            logger.info(f"Injected honeytoken trigger to QMind at confidence=1.0")
        except Exception as e:
            logger.error(f"Failed to inject honeytoken trigger to QMind: {e}")
    
    async def list_honeytokens(self, tenant_id: Optional[int] = None) -> List[Honeytoken]:
        """List honeytokens, optionally filtered by tenant"""
        async with self.db_pool.acquire() as conn:
            if tenant_id:
                rows = await conn.fetch("""
                    SELECT id, tenant_id, token_type, value, description, deployed_at, triggered_at, is_active
                    FROM honeytokens
                    WHERE tenant_id = $1
                    ORDER BY deployed_at DESC
                """, tenant_id)
            else:
                rows = await conn.fetch("""
                    SELECT id, tenant_id, token_type, value, description, deployed_at, triggered_at, is_active
                    FROM honeytokens
                    ORDER BY deployed_at DESC
                """)
            
            return [
                Honeytoken(
                    id=row["id"],
                    tenant_id=row["tenant_id"],
                    token_type=row["token_type"],
                    value=row["value"],
                    description=row["description"],
                    deployed_at=row["deployed_at"],
                    triggered_at=row["triggered_at"],
                    is_active=row["is_active"]
                )
                for row in rows
            ]
    
    async def revoke_honeytoken(self, token_id: int) -> bool:
        """Revoke (deactivate) a honeytoken"""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute("""
                UPDATE honeytokens
                SET is_active = false
                WHERE id = $1
            """, token_id)
            
            # Remove from cache
            to_remove = [value for value, token in self._honeytoken_cache.items() if token.id == token_id]
            for value in to_remove:
                del self._honeytoken_cache[value]
            
            logger.info(f"Revoked honeytoken {token_id}")
            return result == "UPDATE 1"


# Singleton instance
_honeytoken_instance: Optional[HoneytokenManager] = None


def get_honeytoken_manager(db_pool: asyncpg.Pool) -> HoneytokenManager:
    """Get or create the singleton HoneytokenManager instance"""
    global _honeytoken_instance
    if _honeytoken_instance is None:
        _honeytoken_instance = HoneytokenManager(db_pool)
    return _honeytoken_instance
