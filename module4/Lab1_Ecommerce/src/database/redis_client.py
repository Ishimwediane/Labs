import redis
from typing import Optional

from config.database import db_config
from src.utils.logger import log_info, log_error, log_success


class RedisClient:
    def __init__(self):
        """Initialize Redis client."""
        self.config = db_config.get_redis_config()
        self.client = None
        self._connect()
    
    def _connect(self):
        """connecting to Redis."""
        try:
            log_info("Connecting to Redis...")
            self.client = redis.Redis(**self.config)
            self.client.ping()
            log_success("Connected to Redis")
            
        except redis.ConnectionError as e:
            log_error(f"Redis connection failed: {e}")
            raise
    
    def get(self, key: str) -> Optional[str]:
        try:
            return self.client.get(key)
        except Exception as e:
            log_error(f"Redis GET error: {e}")
            return None
    
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        try:
            if ttl:
                self.client.setex(key, ttl, value)
            else:
                self.client.set(key, value)
            return True
        except Exception as e:
            log_error(f"Redis SET error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            log_error(f"Redis DELETE error: {e}")
            return False
    
    def test_connection(self) -> bool:
        try:
            self.client.ping()
            log_success("Redis connection test passed")
            return True
        except Exception as e:
            log_error(f"Redis connection test failed: {e}")
            return False
    
    def get_stats(self) -> dict:
        try:
            info = self.client.info('stats')
            return {
                'total_connections': info.get('total_connections_received', 0),
                'total_commands': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0)
            }
        except Exception as e:
            log_error(f"Error getting Redis stats: {e}")
            return {}

cache = RedisClient()
