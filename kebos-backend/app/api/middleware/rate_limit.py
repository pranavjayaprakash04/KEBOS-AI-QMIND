"""
Rate Limiting Middleware for Kebos AI.
Phase 2.3 - Redis-backed rate limiting using slowapi.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.storage import RedisStorage
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Redis storage for rate limiting
# Per-process limits useless in multi-replica without Redis
storage = RedisStorage(settings.REDIS_URL)

# Rate limiter with Redis backend
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.REDIS_URL,
    default_limits=["200/minute"]
)

logger.info(f"Rate limiter initialized with Redis backend: {settings.REDIS_URL}")
