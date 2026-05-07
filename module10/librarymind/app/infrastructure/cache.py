import json
import hashlib
import logging
from typing import Any, Optional

import redis
from app.config import get_settings

logger = logging.getLogger(__name__)

class CacheService:
    """
    A service for caching AI responses using Redis.
    Provides deterministic key generation and graceful degradation.
    """

    def __init__(self):
        self.settings = get_settings()
        self.redis_client: Optional[redis.Redis] = None
        self.enabled = self.settings.CACHE_ENABLED
        self.default_ttl = self.settings.CACHE_DEFAULT_TTL
        
        if self.enabled:
            self._connect()
        else:
            logger.info("Cache is explicitly disabled in settings.")

    def _connect(self) -> None:
        """Initialize connection to Redis."""
        try:
            self.redis_client = redis.from_url(
                self.settings.REDIS_URL, 
                decode_responses=True,
                socket_connect_timeout=2
            )
            # Test connection
            self.redis_client.ping()
            logger.info(f"Connected to Redis at {self.settings.REDIS_URL}")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"Redis unavailable: {e}. Caching disabled for this session.")
            self.enabled = False
            self.redis_client = None

    def make_key(self, namespace: str, payload: dict) -> str:
        """
        Generate a deterministic cache key based on a namespace and a payload.
        The payload is sorted to ensure the same input always produces the same key.
        """
        serialized_payload = json.dumps(payload, sort_keys=True)
        payload_hash = hashlib.sha256(serialized_payload.encode()).hexdigest()
        return f"{namespace}:{payload_hash}"

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache. 
        Returns None on cache miss or if cache is disabled.
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            value = self.redis_client.get(key)
            if value:
                logger.info(f"Cache HIT for key: {key}")
                return json.loads(value)
            
            logger.info(f"Cache MISS for key: {key}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store a value in the cache with an optional TTL.
        Returns True on success, False if cache is disabled or error occurs.
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            serialized_value = json.dumps(value)
            expiry = ttl if ttl is not None else self.default_ttl
            
            self.redis_client.set(key, serialized_value, ex=expiry)
            logger.info(f"Cache SET for key: {key} (TTL: {expiry}s)")
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False
