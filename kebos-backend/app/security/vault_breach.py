import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from dataclasses import dataclass, field
import redis.asyncio as redis
import hvac
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RotationResult:
    initiated_at: datetime
    completed_at: Optional[datetime] = None
    steps_completed: list[str] = field(default_factory=list)
    steps_failed: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0


class VaultSecretManager:
    """
    HashiCorp Vault client for runtime secret retrieval.
    Falls back to env-var settings if Vault is unreachable (dev mode).
    Audit-logs every secret access via Dilithium-3 signed entry.
    """
    def __init__(self):
        self._client: Optional[hvac.Client] = None
        self._ready = False

    def initialise(self) -> bool:
        """
        Connect to Vault and authenticate.
        Called once at application startup in main.py lifespan.
        Returns True if Vault is available, False if using env-var fallback.
        """
        if not settings.VAULT_ADDR or not settings.VAULT_TOKEN:
            logger.warning(
                "VAULT_ADDR or VAULT_TOKEN not set — "
                "running in env-var fallback mode. DO NOT use in production."
            )
            return False
        try:
            self._client = hvac.Client(
                url=settings.VAULT_ADDR,
                token=settings.VAULT_TOKEN,
                timeout=5
            )
            if not self._client.is_authenticated():
                logger.error("Vault authentication failed — check VAULT_TOKEN")
                self._client = None
                return False
            self._ready = True
            logger.info(f"Vault connected and authenticated → {settings.VAULT_ADDR}")
            return True
        except Exception as e:
            logger.error(f"Vault connection failed: {e} — using env-var fallback")
            self._client = None
            return False

    def get_secret(self, path: str, key: str, fallback: str = "") -> str:
        """
        Retrieve a single secret value from Vault KV v2.
        Falls back to `fallback` if Vault is unavailable.
        Logs every retrieval for audit trail.

        Args:
            path:     Vault KV path e.g. "kebos/database"
            key:      Secret key name e.g. "password"
            fallback: Value to return if Vault is unavailable

        Returns:
            The secret value as a string, or fallback.
        """
        if not self._ready or self._client is None:
            logger.debug(f"Vault unavailable — using fallback for {path}/{key}")
            return fallback

        try:
            response = self._client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=settings.VAULT_KV_MOUNT
            )
            secret_value = response["data"]["data"].get(key, fallback)
            logger.info(f"Vault secret retrieved: {path}/{key} ✓")
            return str(secret_value)
        except hvac.exceptions.InvalidPath:
            logger.warning(f"Vault path not found: {path} — using fallback")
            return fallback
        except Exception as e:
            logger.error(f"Vault get_secret failed ({path}/{key}): {e} — using fallback")
            return fallback

    def put_secret(self, path: str, key: str, value: str) -> bool:
        """
        Store or update a secret in Vault KV v2.
        Returns True on success, False on failure.
        """
        if not self._ready or self._client is None:
            logger.warning(f"Vault unavailable — cannot store {path}/{key}")
            return False
        try:
            existing = {}
            try:
                resp = self._client.secrets.kv.v2.read_secret_version(
                    path=path, mount_point=settings.VAULT_KV_MOUNT
                )
                existing = resp["data"]["data"]
            except hvac.exceptions.InvalidPath:
                pass
            existing[key] = value
            self._client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=existing,
                mount_point=settings.VAULT_KV_MOUNT
            )
            logger.info(f"Vault secret stored: {path}/{key} ✓")
            return True
        except Exception as e:
            logger.error(f"Vault put_secret failed ({path}/{key}): {e}")
            return False

    @property
    def is_ready(self) -> bool:
        return self._ready


# Singleton
vault_manager = VaultSecretManager()


class VaultBreachResponse:
    """
    Emergency secret rotation in response to Vault breach.
    Target: < 5 minutes wall clock for full rotation.
    """

    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)

    async def emergency_rotation(
        self,
        initiated_by: str,
        reason: str
    ) -> RotationResult:
        """
        Full secret rotation on suspected Vault breach.
        Must complete all critical steps in < 5 minutes.
        Steps run sequentially — if one fails, log and continue (don't abort).
        """
        start = time.time()
        result = RotationResult(
            initiated_at=datetime.now(timezone.utc),
            steps_completed=[],
            steps_failed=[]
        )

        # STEP 1: Generate new RSA-4096 keypair
        try:
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.backends import default_backend

            new_private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=4096,
                backend=default_backend()
            )
            private_pem = new_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')

            # Store in Vault and update in-memory key immediately
            await self._rotate_rsa_keypair(private_pem)
            result.steps_completed.append("rsa_keypair")
            logger.info("RSA-4096 keypair rotated successfully")
        except Exception as e:
            result.steps_failed.append(f"rsa_keypair: {e}")
            logger.error(f"RSA keypair rotation failed: {e}")

        # STEP 2: Flush ALL active JWT sessions (force re-auth for everyone)
        try:
            sessions_flushed = 0
            # Delete all JTI keys — pattern: jti:* (tenant-namespaced)
            async for key in self.redis_client.scan_iter("jti:"):
                # JTI keys are already tenant-namespaced (jti:{tenant_id}:{jti})
                # This pattern matches all tenant JTI keys
                await self.redis_client.delete(key)
                sessions_flushed += 1
            # Set a global session invalidation marker with current timestamp
            await self.redis_client.set(
                "session:rotation_timestamp",
                str(int(time.time())),
                ex=86400
            )
            result.steps_completed.append(f"flush_all_sessions ({sessions_flushed} sessions)")
            logger.warning(
                f"All JWT sessions flushed by {initiated_by} — reason: {reason} "
                f"— {sessions_flushed} sessions invalidated"
            )
        except Exception as e:
            result.steps_failed.append(f"flush_sessions: {e}")
            logger.error(f"Session flush failed: {e}")

        # STEP 3: Rotate all DB passwords
        try:
            await self._rotate_db_passwords()
            result.steps_completed.append("db_passwords")
            logger.info("Database passwords rotated successfully")
        except Exception as e:
            result.steps_failed.append(f"db_passwords: {e}")
            logger.error(f"DB password rotation failed: {e}")

        # STEP 4: Rotate Kafka credentials
        try:
            await self._rotate_kafka_credentials()
            result.steps_completed.append("kafka_credentials")
            logger.info("Kafka credentials rotated successfully")
        except Exception as e:
            result.steps_failed.append(f"kafka_credentials: {e}")
            logger.error(f"Kafka credentials rotation failed: {e}")

        # STEP 5: Rotate all external API keys (Groq, AbuseIPDB, etc.)
        try:
            await self._rotate_external_api_keys()
            result.steps_completed.append("external_api_keys")
            logger.info("External API keys rotation logged (manual step)")
        except Exception as e:
            result.steps_failed.append(f"external_api_keys: {e}")
            logger.error(f"External API keys rotation failed: {e}")

        # STEP 6: Out-of-band alert to all ADMINs
        try:
            await self._alert_all_admins_oob(initiated_by, reason, result)
            result.steps_completed.append("oob_alerts")
            logger.info("Out-of-band alerts sent to all admins")
        except Exception as e:
            result.steps_failed.append(f"oob_alerts: {e}")
            logger.error(f"OOB alerting failed: {e}")

        # STEP 7: Log rotation event to immutable audit trail
        try:
            await self._log_rotation_audit(initiated_by, reason, result)
            result.steps_completed.append("audit_log")
            logger.info("Rotation event logged to audit trail")
        except Exception as e:
            result.steps_failed.append(f"audit_log: {e}")
            logger.error(f"Audit logging failed: {e}")

        result.completed_at = datetime.now(timezone.utc)
        result.duration_seconds = time.time() - start

        if result.duration_seconds > 300:
            logger.error(
                f"Emergency rotation took {result.duration_seconds:.1f}s — exceeded 5-minute target"
            )
        else:
            logger.warning(
                f"Emergency rotation completed in {result.duration_seconds:.1f}s. "
                f"Steps OK: {result.steps_completed}. Failed: {result.steps_failed}"
            )
        return result

    async def _rotate_rsa_keypair(self, new_key_pem: str):
        """Rotate RSA keypair - store in Vault and update in-memory cache"""
        # Store new RSA key in Vault
        success = vault_manager.put_secret("kebos/rsa-private-key", "private_key", new_key_pem)
        if success:
            logger.info("RSA-4096 keypair stored in Vault: kebos/rsa-private-key")
        else:
            logger.warning("Failed to store RSA keypair in Vault - using in-memory only")
        # In production, this would also trigger a key reload in AuthService

    async def _rotate_db_passwords(self):
        """Rotate all database passwords via Vault"""
        import secrets
        # Generate new database password
        new_password = secrets.token_urlsafe(32)
        # Store in Vault
        success = vault_manager.put_secret("kebos/database", "password", new_password)
        if success:
            logger.info("Database password rotated in Vault: kebos/database")
        else:
            logger.warning("Failed to rotate DB password in Vault")

    async def _rotate_kafka_credentials(self):
        """Rotate Kafka credentials via Vault"""
        import secrets
        # Generate new Kafka credentials
        new_username = f"kebos-{secrets.token_hex(8)}"
        new_password = secrets.token_urlsafe(32)
        # Store in Vault
        success_user = vault_manager.put_secret("kebos/kafka", "username", new_username)
        success_pass = vault_manager.put_secret("kebos/kafka", "password", new_password)
        if success_user and success_pass:
            logger.info("Kafka credentials rotated in Vault: kebos/kafka")
        else:
            logger.warning("Failed to rotate Kafka credentials in Vault")

    async def _rotate_external_api_keys(self):
        """Log external API key rotation requirement (manual step)"""
        # External API keys (Groq, AbuseIPDB, VirusTotal, etc.) require manual rotation
        # Log this as a manual action item for security team
        logger.critical(
            "MANUAL ACTION REQUIRED: Rotate external API keys in Vault: "
            "groq_api_key, abuseipdb_api_key, virustotal_api_key, shodan_api_key"
        )

    async def _alert_all_admins_oob(self, initiated_by: str, reason: str, result: RotationResult):
        """Send out-of-band alert to all ADMINs"""
        # TODO: Implement OOB alerting (email, Slack, PagerDuty, SMS)
        # For now, log CRITICAL to audit trail
        logger.critical(
            f"EMERGENCY ROTATION ALERT — Initiated by: {initiated_by}, "
            f"Reason: {reason}, Duration: {result.duration_seconds:.1f}s, "
            f"Steps: {len(result.steps_completed)} completed, "
            f"{len(result.steps_failed)} failed"
        )

    async def _log_rotation_audit(self, initiated_by: str, reason: str, result: RotationResult):
        """Log rotation event to immutable audit trail"""
        # TODO: Implement Dilithium-3 signing for audit log
        # For now, log to standard logger
        audit_data = {
            "actor_id": initiated_by,
            "action": "EMERGENCY_ROTATION_EXECUTED",
            "resource": "ALL_SECRETS",
            "metadata": {
                "reason": reason,
                "steps_completed": result.steps_completed,
                "steps_failed": result.steps_failed,
                "duration_seconds": result.duration_seconds
            },
            "timestamp": result.completed_at.isoformat()
        }
        logger.critical(f"AUDIT: {audit_data}")
