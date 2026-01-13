import json
from typing import List, Dict, Optional
from src.database.redis_client import cache
from config.database import db_config
from src.utils.logger import log_success, log_error, log_info


class CacheService:
    def cache_top_products(self, products: List[Dict], ttl: int = None) -> bool:
        if ttl is None:
            ttl = db_config.CACHE_TTL_MEDIUM
        
        try:
            key = "top_products:best_selling"
            value = json.dumps(products)
            cache.set(key, value, ttl)
            log_success(f"Cached {len(products)} top products (TTL: {ttl}s)")
            return True
        except Exception as e:
            log_error(f"Error caching products: {e}")
            return False
    
    def get_top_products(self) -> Optional[List[Dict]]:
        try:
            key = "top_products:best_selling"
            cached = cache.get(key)
            
            if cached:
                log_info("Cache HIT: Retrieved top products from Redis")
                return json.loads(cached)
            else:
                log_info("Cache MISS: Top products not in cache")
                return None
        except Exception as e:
            log_error(f"Error retrieving from cache: {e}")
            return None
    
    def cache_product_details(self, product_id: int, product_data: Dict, 
                             ttl: int = None) -> bool:
        if ttl is None:
            ttl = db_config.CACHE_TTL_LONG
        
        try:
            key = f"product:{product_id}"
            value = json.dumps(product_data)
            cache.set(key, value, ttl)
            log_success(f"Cached product {product_id}")
            return True
        except Exception as e:
            log_error(f"Error caching product: {e}")
            return False
    
    def get_product_details(self, product_id: int) -> Optional[Dict]:
        try:
            key = f"product:{product_id}"
            cached = cache.get(key)
            
            if cached:
                log_info(f"Cache HIT: Product {product_id}")
                return json.loads(cached)
            else:
                log_info(f"Cache MISS: Product {product_id}")
                return None
        except Exception as e:
            log_error(f"Error retrieving product from cache: {e}")
            return None
    
    def invalidate_top_products(self) -> bool:
        try:
            key = "top_products:best_selling"
            cache.delete(key)
            log_success("Top products cache invalidated")
            return True
        except Exception as e:
            log_error(f"Error invalidating cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict:
        try:
            stats = cache.get_stats()
            
            # Calculate hit rate
            hits = stats.get('keyspace_hits', 0)
            misses = stats.get('keyspace_misses', 0)
            total = hits + misses
            
            if total > 0:
                hit_rate = round((hits / total) * 100, 2)
            else:
                hit_rate = 0.0
            
            return {
                'total_connections': stats.get('total_connections', 0),
                'total_commands': stats.get('total_commands', 0),
                'keyspace_hits': hits,
                'keyspace_misses': misses,
                'hit_rate': hit_rate
            }
        except Exception as e:
            log_error(f"Error getting cache stats: {e}")
            return {}

cache_service = CacheService()
