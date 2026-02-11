import sys
from src.database.connection import get_connection
from src.database.mongo_client import mongodb
from config.database import DatabaseConfig
import redis
import psycopg2
import json
from pprint import pprint

def verify_postgres():
    print("\n" + "="*50)
    print("1. POSTGRESQL (Relational Data)")
    print("="*50)
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        tables = ['customers', 'products', 'orders', 'order_items']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"Table '{table}': {count} rows")
            
            # Show top 2 rows as sample
            cursor.execute(f"SELECT * FROM {table} LIMIT 2")
            print(f"  Sample data: {cursor.fetchall()}")
            
        conn.close()
        print("[SUCCESS] Postgres verified")
    except Exception as e:
        print(f"[ERROR] Postgres connection failed: {e}")

def verify_redis():
    print("\n" + "="*50)
    print("2. REDIS (Cache Data)")
    print("="*50)
    try:
        config = DatabaseConfig.get_redis_config()
        r = redis.Redis(**config)
        
        try:
            r.ping()
            print("Connected to Redis")
        except redis.ConnectionError:
            print("[ERROR] Redis is not running")
            return

        keys = r.keys('*')
        print(f"Total keys found: {len(keys)}")
        
        for key in keys:
            val = r.get(key)
            try:
                # Try to pretty print JSON if possible
                decoded_val = val.decode('utf-8')
                parsed = json.loads(decoded_val)
                print(f"  Key: {key.decode('utf-8')} -> Value (JSON): \n{json.dumps(parsed, indent=2)}")
            except:
                print(f"  Key: {key} -> Value: {val}")
            
        print("[SUCCESS] Redis verified")
    except Exception as e:
        print(f"[ERROR] Redis check failed: {e}")

def verify_mongo():
    print("\n" + "="*50)
    print("3. MONGODB (Document Data)")
    print("="*50)
    try:
        if mongodb.test_connection():
            db = mongodb.client[mongodb.config['database']]
            collections = db.list_collection_names()
            print(f"Collections found: {collections}")
            
            for col_name in collections:
                count = db[col_name].count_documents({})
                print(f"Collection '{col_name}': {count} documents")
                
                # Sample
                docs = list(db[col_name].find().limit(2))
                print(f"  Sample: {docs}")
                
            print("[SUCCESS] MongoDB verified")
        else:
            print("[ERROR] MongoDB connection test returned False")
    except Exception as e:
        print(f"[ERROR] MongoDB check failed: {e}")

def main():
    print("VERIFYING DOCKER SERVICES Data...")
    print("Ensure 'docker-compose up' is running first!")
    
    verify_postgres()
    verify_redis()
    verify_mongo()
    
    print("\nDone.")

if __name__ == "__main__":
    main()
