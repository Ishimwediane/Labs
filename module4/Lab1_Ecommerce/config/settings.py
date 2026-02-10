import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application configuration settings."""
    
    def __init__(self):
        """Initialize settings from environment variables."""
        # PostgreSQL settings
        self.POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
        self.POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
        self.POSTGRES_DB = os.getenv('POSTGRES_DB', 'ecommerce')
        self.POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
        self.POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
        
        # MongoDB settings
        self.MONGODB_URI = os.getenv('MONGODB_URI', '')
        self.MONGODB_DB = os.getenv('DB_NAME', 'store')
        
        # Redis settings
        self.REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
        self.REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
        self.REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    def validate(self):
        """
        Validate required settings are present.

        """
        if not self.MONGODB_URI:
            raise ValueError(
                "MONGODB_URI is required. Please set it in your .env file."
            )
        
        if not self.POSTGRES_PASSWORD:
            raise ValueError(
                "POSTGRES_PASSWORD is required. Please set it in your .env file."
            )

settings = Settings()
