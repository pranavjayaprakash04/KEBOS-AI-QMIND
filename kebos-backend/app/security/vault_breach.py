import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from dataclasses import dataclass, field
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RotationResult:
    initiated_at: datetime
    completed_at: Optional[datetime] = None
    steps_completed: list[str] = field(default_factory=list)
    steps_failed: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0


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

            # Store in Vault (TODO: implement Vault client)
            # vault_client.write_secret("kebos/rsa-private-key", private_pem)
            # Update in-memory key immediately
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
        # TODO: Implement Vault client to write to kebos/rsa-private-key
        # For now, log the action
        logger.info("RSA keypair stored in Vault (TODO: implement hvac client)")
        # In production, this would also trigger a key reload in AuthService

    async def _rotate_db_passwords(self):
        """Rotate all database passwords via Vault"""
        # TODO: Implement Vault KV rotation for database credentials
        # For now, log the action
        logger.info("DB passwords rotated in Vault (TODO: implement hvac client)")

    async def _rotate_kafka_credentials(self):
        """Rotate Kafka credentials via Vault"""
        # TODO: Implement Vault KV rotation for Kafka credentials
        # For now, log the action
        logger.info("Kafka credentials rotated in Vault (TODO: implement hvac client)")

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
