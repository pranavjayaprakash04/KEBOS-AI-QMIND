from app.config import settings
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)


def validate_environment() -> list[str]:
    """Validate environment configuration - returns list of errors"""
    errors = []
    if settings.JWT_ALGORITHM != "RS256":
        errors.append("CRITICAL: JWT_ALGORITHM must be RS256, got: " + settings.JWT_ALGORITHM)
    if settings.ACCESS_TOKEN_EXPIRE_MINUTES > 15:
        errors.append(f"CRITICAL: ACCESS_TOKEN_EXPIRE_MINUTES={settings.ACCESS_TOKEN_EXPIRE_MINUTES}, must be <= 15")
    if not settings.USE_REAL_PQC:
        errors.append("CRITICAL: USE_REAL_PQC=false — post-quantum cryptography disabled. Set USE_REAL_PQC=true.")
    if settings.SYSLOG_HOST and not settings.SYSLOG_CA_CERT:
        errors.append("CRITICAL: SYSLOG_CA_CERT required when SYSLOG_HOST is set (TCP+TLS required)")
    # Startup assertions — any CRITICAL error is fatal
    critical = [e for e in errors if e.startswith("CRITICAL")]
    if critical:
        for msg in errors:
            logger.error(msg)
        raise SystemExit(f"Environment validation failed with {len(critical)} critical errors. See logs.")
    for msg in errors:
        logger.warning(msg)
    return errors


async def check_redis_connectivity() -> bool:
    """Check if Redis is accessible"""
    try:
        client = redis.from_url(settings.REDIS_URL)
        await client.ping()
        await client.close()
        return True
    except Exception as e:
        logger.warning(f"Redis connectivity check failed: {e}")
        return False


async def check_vault_connectivity() -> bool:
    """Check if Vault is accessible"""
    # TODO: Implement Vault connectivity check
    return True


async def check_postgres_connectivity() -> bool:
    """Check if PostgreSQL is accessible"""
    # TODO: Implement PostgreSQL connectivity check
    return True
