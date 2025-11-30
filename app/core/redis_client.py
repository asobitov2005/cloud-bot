"""Redis client for FSM storage and caching"""
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_redis_client = None

# Try to import Redis, but make it optional
try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    aioredis = None
    REDIS_AVAILABLE = False
    logger.warning("Redis not available - install redis package for Redis features")


def get_redis_url() -> str:
    """Get Redis URL from configuration"""
    if settings.REDIS_URL:
        return settings.REDIS_URL
    
    password = f":{settings.REDIS_PASSWORD}@" if settings.REDIS_PASSWORD else ""
    return f"redis://{password}{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"


async def get_redis_client():
    """Get or create Redis client"""
    global _redis_client
    
    if not REDIS_AVAILABLE:
        raise ImportError("Redis package not installed. Install with: pip install redis aioredis")
    
    if _redis_client is None:
        redis_url = get_redis_url()
        try:
            _redis_client = aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            # Test connection
            await _redis_client.ping()
            logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    return _redis_client


async def close_redis():
    """Close Redis connection"""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")

