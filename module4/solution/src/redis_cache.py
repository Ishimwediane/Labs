import os
import json
from typing import List, Dict, Optional
import redis
from dotenv import load_dotenv

load_dotenv()


class RedisCache:
    """Redis cache manager for e-commerce analytics."""
    
    def __init__(self):
        """Initialize Redis connection."""
        self.client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
            decode_responses=True
        )
        try:
            self.client.ping()
            print("Redis connection established")
        except redis.ConnectionError as e:
            print(f"Redis connection failed: {e}")
            raise
    
    def cache_top_products(self, products: List[Dict], ttl: int = 300):
        """
        Cache top products list with TTL (Time To Live).
        
        Args:
            products: List of product dictionaries
            ttl: Cache expiration time in seconds (default 5 minutes)
        """
        try:
            key = "top_products:best_selling"
            value = json.dumps(products)
            self.client.setex(key, ttl, value)
            print(f"Cached {len(products)} top products (TTL: {ttl}s)")
        except Exception as e:
            print(f"Error caching products: {e}")
    
    def get_top_products(self) -> Optional[List[Dict]]:
        """
        Retrieve cached top products.
        
        Returns:
            List of products if cached, None if cache miss
        """
        try:
            key = "top_products:best_selling"
            cached = self.client.get(key)
            if cached:
                print("Cache HIT: Retrieved top products from Redis")
                return json.loads(cached)
            else:
                print("Cache MISS: Top products not in cache")
                return None
        except Exception as e:
            print(f"Error retrieving from cache: {e}")
            return None
    
    def invalidate_top_products(self):
        """Invalidate (delete) top products cache."""
        try:
            key = "top_products:best_selling"
            self.client.delete(key)
            print("Top products cache invalidated")
        except Exception as e:
            print(f"Error invalidating cache: {e}")
    
    def cache_product_details(self, product_id: int, product_data: Dict, ttl: int = 600):
        """
        Cache individual product details.
        
        Args:
            product_id: Product ID
            product_data: Product dictionary
            ttl: Cache expiration time in seconds (default 10 minutes)
        """
        try:
            key = f"product:{product_id}"
            value = json.dumps(product_data)
            self.client.setex(key, ttl, value)
            print(f"Cached product {product_id}")
        except Exception as e:
            print(f"Error caching product: {e}")
    
    def get_product_details(self, product_id: int) -> Optional[Dict]:
        """
        Retrieve cached product details.
        
        Args:
            product_id: Product ID
        
        Returns:
            Product dictionary if cached, None otherwise
        """
        try:
            key = f"product:{product_id}"
            cached = self.client.get(key)
            if cached:
                print(f"Cache HIT: Product {product_id}")
                return json.loads(cached)
            else:
                print(f"Cache MISS: Product {product_id}")
                return None
        except Exception as e:
            print(f"Error retrieving product from cache: {e}")
            return None
    
    def get_cache_stats(self) -> Dict:
        """
        Get Redis cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            info = self.client.info('stats')
            return {
                'total_connections': info.get('total_connections_received', 0),
                'total_commands': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {}
    
    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage."""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
