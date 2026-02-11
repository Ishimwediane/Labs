from src.database.connection import get_connection
from psycopg2.extras import RealDictCursor
from src.utils.validators import validate_email, validate_name
from typing import Optional, Dict, Any

def create_customer(name: str, email: str, address: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new customer with validation.

    """
    # Validate inputs
    is_valid_name, message_name = validate_name(name)
    if not is_valid_name:
        raise ValueError(message_name)
        
    is_valid_email, message_email = validate_email(email)
    if not is_valid_email:
        raise ValueError(message_email)
    
    conn = get_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            INSERT INTO customers (name, email, address)
            VALUES (%s, %s, %s)
            RETURNING id, name, email, address
        """, (name, email, address))
        
        customer = cursor.fetchone()
        conn.commit()
        return customer
        
    finally:
        conn.close()

def get_customer_by_id(customer_id: int) -> Optional[Dict[str, Any]]:
    """Get customer by ID"""
    conn = get_connection()
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        return cursor.fetchone()
    finally:
        conn.close()
