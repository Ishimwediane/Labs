import psycopg2
from contextlib import contextmanager
from typing import Optional

from config.database import db_config
from src.utils.logger import log_info, log_error, log_success


class DatabaseManager:
    def __init__(self):
        """Initialize database manager."""
        self.config = db_config.get_postgres_config()
        self._connection = None
    
    def connect(self):
        try:
            conn = psycopg2.connect(**self.config)
            log_success("Connected to PostgreSQL database")
            return conn
        except Exception as e:
            log_error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        conn = self.connect()
        try:
            yield conn
        finally:
            conn.close()
    
    @contextmanager
    def get_cursor(self, commit: bool = False):
        conn = self.connect()
        cur = conn.cursor()
        
        try:
            yield cur
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            log_error(f"Database error: {e}")
            raise
        finally:
            cur.close()
            conn.close()
    
    def execute_query(self, query: str, params: tuple = None, fetch: bool = True):
        with self.get_cursor() as cur:
            cur.execute(query, params)
            if fetch:
                return cur.fetchall()
            return None
    
    def test_connection(self) -> bool:
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    result = cur.fetchone()
                    if result and result[0] == 1:
                        log_success("PostgreSQL connection test passed")
                        return True
            return False
        except Exception as e:
            log_error(f"PostgreSQL connection test failed: {e}")
            return False
db = DatabaseManager()
