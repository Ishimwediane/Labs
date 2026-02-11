from src.database.connection import get_connection
from config.database import DatabaseConfig
from psycopg2.extras import RealDictCursor
import redis
import json
from decimal import Decimal
from pymongo import MongoClient
from datetime import datetime


def show_redis_cache():
    print("\n" + "="*80)
    print("REDIS CACHE - Top Products")
    print("="*80 + "\n")
    
    try:
        redis_config = DatabaseConfig.get_redis_config()
        r = redis.Redis(**redis_config)
        
        # Check cache
        cached = r.get('top_products')
        if cached:
            print(f"[CACHE HIT] Found cached data")
            products = json.loads(cached)
            for p in products:
                print(f"  - {p['name']}: ${p['price']}")
        else:
            print("[CACHE MISS] Fetching from database...")
            
            # Use repository to get products
            from src.repositories.product_repository import get_top_products
            products = get_top_products(limit=5)
            
            # Helper to Convert Decimals to float for JSON
            class DecimalEncoder(json.JSONEncoder):
                def default(self, o):
                    if isinstance(o, Decimal):
                        return float(o)
                    return super(DecimalEncoder, self).default(o)
            
            # Cache results as JSON
            r.setex('top_products', 300, json.dumps(products, cls=DecimalEncoder))
            print(f"[CACHED] Stored top 5 products")
            
            for p in products:
                print(f"  - {p['name']}: ${p['price']}")
        
        print("\n[SUCCESS] Redis cache working!")
        
    except Exception as e:
        print(f"[WARNING] Redis not available: {e}")


def show_mongodb_sessions():
    print("\n" + "="*80)
    print("MONGODB - User Sessions")
    print("="*80 + "\n")
    
    try:
        mongo_config = DatabaseConfig.get_mongodb_config()
        client = MongoClient(mongo_config['uri'], 
                           serverSelectionTimeoutMS=mongo_config['serverSelectionTimeoutMS'])
        db = client[mongo_config['database']]
        session_data = {
            'user_id': 1,
            'cart': [
                {'product_id': 1, 'quantity': 2},
                {'product_id': 3, 'quantity': 1}
            ],
            'timestamp': datetime.now()
        }
        
        result = db.sessions.insert_one(session_data)
        print(f"Session stored: {result.inserted_id}")
        session = db.sessions.find_one({'user_id': 1})
        print(f"Cart items: {len(session['cart'])}")
        
        print("\n[SUCCESS] MongoDB sessions working!")
        
    except Exception as e:
        print(f"[WARNING] MongoDB not available: {e}")


if __name__ == "__main__":
    try:
        show_redis_cache()
        show_mongodb_sessions()
    except Exception as e:
        print(f"Error running demos: {e}")
