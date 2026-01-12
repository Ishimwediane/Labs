import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """
    Create and return a new PostgreSQL database connection.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '5432'),
            database=os.getenv('POSTGRES_DB', 'ecommerce'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'postgres123')
        )
        print("Connected to the database")
        return conn
    except Exception as e:
        print(f"Connection error: {e}")
        return None


def execute_query(query, commit=False):
    """
    Execute a SQL query with optional commit.
    """
    conn = get_connection()
    if not conn:
        return

    try:
        cur = conn.cursor()
        cur.execute(query)
        
        if commit:
            conn.commit()
    
        try:
            results = cur.fetchall()
            return results
        except psycopg2.ProgrammingError:
            return None

    except Exception as e:
        print(f"Query error: {e}")
    finally:
        cur.close()
        conn.close()
        print("Connection closed")


if __name__ == "__main__":
    version = execute_query("SELECT version();")
    if version:
        print(f"PostgreSQL version: {version[0][0]}")

    tables = execute_query("""
        SELECT table_name
        FROM schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    if tables:
        print(f"Available tables: {[t[0] for t in tables]}")
