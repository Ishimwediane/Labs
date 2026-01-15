"""
Database connection helper
"""

import psycopg2
from config.database import DatabaseConfig


def get_connection():
    """Get PostgreSQL database connection"""
    config = DatabaseConfig.get_postgres_config()
    return psycopg2.connect(**config)
