from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from typing import Optional

from config.database import db_config
from src.utils.logger import log_info, log_error, log_success


class MongoDBClient:
    def __init__(self):
        """Initialize MongoDB """
        self.config = db_config.get_mongodb_config()
        self.client = None
        self.db = None
        self._connect()
    
    def _connect(self):
        """connecting to MongoDB."""
        try:
            uri = self.config['uri']
            if not uri:
                raise ValueError(
                    "MONGODB_URI not found. Please set it in your .env file."
                )            
            log_info("Connecting to MongoDB Atlas...")            
            self.client = MongoClient(
                uri,
                serverSelectionTimeoutMS=self.config['serverSelectionTimeoutMS']
            )
            self.client.admin.command('ping')
            db_name = self.config['database']
            self.db = self.client[db_name]            
            log_success(f"Connected to MongoDB Atlas (database: {db_name})")
            
        except ConnectionFailure as e:
            log_error(f"MongoDB connection failed: {e}")
            raise
        except ValueError as e:
            log_error(str(e))
            raise
    
    def get_collection(self, collection_name: str):
        if not self.db:
            raise RuntimeError("MongoDB not connected")
        
        return self.db[collection_name]
    
    def test_connection(self) -> bool:
        try:
            self.client.admin.command('ping')
            log_success("MongoDB connection test passed")
            return True
        except Exception as e:
            log_error(f"MongoDB connection test failed: {e}")
            return False
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            log_info("MongoDB connection closed")
mongodb = MongoDBClient()
