from .settings import settings

class DatabaseConfig:
    """Database configuration and connection parameters."""
    
    POSTGRES_MIN_CONNECTIONS = 1
    POSTGRES_MAX_CONNECTIONS = 10
    
    MONGODB_SERVER_SELECTION_TIMEOUT = 5000  
    
    REDIS_SOCKET_TIMEOUT = 5  
    REDIS_DECODE_RESPONSES = True
    
    CACHE_TTL_SHORT = 300      
    CACHE_TTL_MEDIUM = 600     
    CACHE_TTL_LONG = 1800      
    
    @staticmethod
    def get_postgres_config() -> dict:
        """
        Get PostgreSQL connection configuration.
        
        Returns:
            Dictionary with PostgreSQL connection parameters
        """
        return {
            'host': settings.POSTGRES_HOST,
            'port': settings.POSTGRES_PORT,
            'database': settings.POSTGRES_DB,
            'user': settings.POSTGRES_USER,
            'password': settings.POSTGRES_PASSWORD
        }
    
    @staticmethod
    def get_mongodb_config() -> dict:
        """
        Get MongoDB connection configuration.

        """
        return {
            'uri': settings.MONGODB_URI,
            'database': settings.MONGODB_DB,
            'serverSelectionTimeoutMS': DatabaseConfig.MONGODB_SERVER_SELECTION_TIMEOUT
        }
    
    @staticmethod
    def get_redis_config() -> dict:
        """
        Get Redis connection configuration.

        """
        return {
            'host': settings.REDIS_HOST,
            'port': settings.REDIS_PORT,
            'db': settings.REDIS_DB,
            'socket_timeout': DatabaseConfig.REDIS_SOCKET_TIMEOUT,
            'decode_responses': DatabaseConfig.REDIS_DECODE_RESPONSES
        }


db_config = DatabaseConfig()
