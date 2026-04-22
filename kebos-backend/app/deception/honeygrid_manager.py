from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging
import asyncpg

logger = logging.getLogger(__name__)


class HoneytokenType(Enum):
    """3 honeytoken types as per context requirements"""
    AWS_ACCESS_KEY = "aws_access_key"
    DATABASE_CREDENTIAL = "database_credential"
    API_TOKEN = "api_token"


@dataclass
class Honeytoken:
    """Honeytoken definition"""
    id: str
    token_type: HoneytokenType
    value: str
    description: str
    deployed_at: Optional[str] = None
    last_triggered: Optional[str] = None
    trigger_count: int = 0
    is_active: bool = True


class HoneyGridManager:
    """
    HoneyGrid Manager for managing honeytokens.
    
    Uses Tecnativa docker-proxy instead of Docker socket (Bug #9).
    """
    
    def __init__(self, db_pool: asyncpg.Pool = None):
        self.db_pool = db_pool
        # TODO: Configure Tecnativa docker-proxy endpoint
        # Bug #9: Docker socket replaced by Tecnativa proxy
        self.docker_proxy_url = "http://docker-proxy:2375"
    
    async def create_honeytoken(
        self,
        token_type: HoneytokenType,
        description: str,
        custom_value: Optional[str] = None
    ) -> Honeytoken:
        """
        Create a new honeytoken.
        
        For scaffold, generates deterministic fake values.
        In production, would use secure random generation.
        """
        import uuid
        import secrets
        
        # Generate honeytoken value
        if custom_value:
            value = custom_value
        elif token_type == HoneytokenType.AWS_ACCESS_KEY:
            # AWS access key format: AKIAIOSFODNN7EXAMPLE
            value = f"AKIA{secrets.token_urlsafe(16).upper()}"
        elif token_type == HoneytokenType.DATABASE_CREDENTIAL:
            # Database credential
            value = f"honey_{secrets.token_urlsafe(16)}"
        elif token_type == HoneytokenType.API_TOKEN:
            # API token
            value = secrets.token_urlsafe(32)
        else:
            value = secrets.token_urlsafe(32)
        
        honeytoken_id = str(uuid.uuid4())
        
        # Store in database
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO honeytokens (id, token_type, value, description, is_active)
                        VALUES ($1, $2, $3, $4, true)
                    """, honeytoken_id, token_type.value, value, description)
                    logger.info(f"Created honeytoken: {honeytoken_id} ({token_type.value})")
            except Exception as e:
                logger.error(f"Error storing honeytoken in database: {e}")
        
        return Honeytoken(
            id=honeytoken_id,
            token_type=token_type,
            value=value,
            description=description
        )
    
    async def deploy_honeytoken(
        self,
        honeytoken_id: str,
        deployment_target: str
    ) -> bool:
        """
        Deploy honeytoken to target via Tecnativa docker-proxy.
        
        Bug #9: Uses docker-proxy instead of Docker socket.
        """
        # TODO: Implement deployment via Tecnativa docker-proxy
        # For scaffold, just mark as deployed in database
        
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE honeytokens
                        SET deployed_at = NOW(), deployment_target = $1
                        WHERE id = $2
                    """, deployment_target, honeytoken_id)
                    logger.info(f"Deployed honeytoken {honeytoken_id} to {deployment_target}")
                    return True
            except Exception as e:
                logger.error(f"Error deploying honeytoken: {e}")
        
        return False
    
    async def trigger_honeytoken(
        self,
        honeytoken_value: str,
        trigger_source: str,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        """
        Handle honeytoken trigger.
        Returns threat_id if trigger was valid.
        """
        import uuid
        
        # Find honeytoken by value
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    row = await conn.fetchrow("""
                        SELECT id, token_type, trigger_count
                        FROM honeytokens
                        WHERE value = $1 AND is_active = true
                    """, honeytoken_value)
                    
                    if row:
                        honeytoken_id = row["id"]
                        token_type = row["token_type"]
                        
                        # Update trigger count and last triggered
                        await conn.execute("""
                            UPDATE honeytokens
                            SET trigger_count = trigger_count + 1,
                                last_triggered = NOW()
                            WHERE id = $1
                        """, honeytoken_id)
                        
                        logger.warning(
                            f"HONEYTOKEN TRIGGERED: {honeytoken_id} ({token_type}) "
                            f"from {trigger_source}"
                        )
                        
                        # Create threat record for honeytoken interaction
                        threat_id = str(uuid.uuid4())
                        await conn.execute("""
                            INSERT INTO threats (id, ioc_value, ioc_type, category, confidence, source_type, is_proactive)
                            VALUES ($1, $2, 'honeytoken', 'C2_Infrastructure', 1.0, 'honeypot', false)
                        """, threat_id, honeytoken_value)
                        
                        # Send to Kafka for QMind processing
                        # TODO: Implement Kafka producer
                        # For scaffold, just log
                        logger.info(f"Would send honeytoken trigger to Kafka: {threat_id}")
                        
                        # Send to SIEM
                        siem_client = get_siem_client()
                        siem_client.send_honeytoken_trigger(
                            honeytoken_id=honeytoken_id,
                            token_type=token_type,
                            trigger_source=trigger_source,
                            threat_id=threat_id
                        )
                        
                        return threat_id
                    else:
                        logger.debug(f"Honeytoken not found: {honeytoken_value}")
                        return None
                        
            except Exception as e:
                logger.error(f"Error handling honeytoken trigger: {e}")
        
        return None
    
    async def list_honeytokens(self, active_only: bool = True) -> List[Honeytoken]:
        """List all honeytokens"""
        honeytokens = []
        
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    if active_only:
                        rows = await conn.fetch("""
                            SELECT id, token_type, value, description, deployed_at, last_triggered, trigger_count, is_active
                            FROM honeytokens
                            WHERE is_active = true
                        """)
                    else:
                        rows = await conn.fetch("""
                            SELECT id, token_type, value, description, deployed_at, last_triggered, trigger_count, is_active
                            FROM honeytokens
                        """)
                    
                    for row in rows:
                        honeytokens.append(Honeytoken(
                            id=row["id"],
                            token_type=HoneytokenType(row["token_type"]),
                            value=row["value"],
                            description=row["description"],
                            deployed_at=row["deployed_at"].isoformat() if row["deployed_at"] else None,
                            last_triggered=row["last_triggered"].isoformat() if row["last_triggered"] else None,
                            trigger_count=row["trigger_count"],
                            is_active=row["is_active"]
                        ))
                        
            except Exception as e:
                logger.error(f"Error listing honeytokens: {e}")
        
        return honeytokens
    
    async def revoke_honeytoken(self, honeytoken_id: str) -> bool:
        """Revoke a honeytoken (mark as inactive)"""
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    await conn.execute("""
                        UPDATE honeytokens
                        SET is_active = false
                        WHERE id = $1
                    """, honeytoken_id)
                    logger.info(f"Revoked honeytoken: {honeytoken_id}")
                    return True
            except Exception as e:
                logger.error(f"Error revoking honeytoken: {e}")
        
        return False


# Singleton instance
_honeygrid_manager: Optional[HoneyGridManager] = None


def get_honeygrid_manager(db_pool: asyncpg.Pool = None) -> HoneyGridManager:
    """Get or create the singleton HoneyGridManager instance"""
    global _honeygrid_manager
    if _honeygrid_manager is None:
        _honeygrid_manager = HoneyGridManager(db_pool)
    return _honeygrid_manager
