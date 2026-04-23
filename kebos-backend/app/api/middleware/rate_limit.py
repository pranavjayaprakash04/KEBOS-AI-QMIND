"""
Rate Limiting Middleware for Kebos AI.
Phase 2.3 - Redis-backed rate limiting using slowapi.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Redis storage for rate limiting
# Per-process limits useless in multi-replica without Redis
try:
    from slowapi.storage import RedisStorage
    storage = RedisStorage(settings.REDIS_URL)
except ImportError:
    # Fallback for slowapi versions without RedisStorage
    from slowapi import Limiter
    storage = None
    logger.warning("slowapi.storage.RedisStorage not available, using in-memory storage")

# Rate limiter with Redis backend
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    default_limits=["200/minute"]
)

logger.info(f"Rate limiter initialized with Redis backend: {settings.REDIS_URL}")
