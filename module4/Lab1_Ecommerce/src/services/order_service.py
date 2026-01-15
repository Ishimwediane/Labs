"""
Order service - Business logic for order processing
"""

from src.repositories.order_repository import create_order, create_order_item, update_product_stock
from src.database.connection import get_connection


def process_order(customer_id, product_id, quantity, unit_price):
    """
    Process order with transaction (ACID)
    Creates order, adds item, updates stock atomically
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Calculate total
        subtotal = quantity * unit_price
        
        # Create order
        cursor.execute("""
            INSERT INTO orders (customer_id, total_amount, status)
            VALUES (%s, %s, %s) RETURNING id
        """, (customer_id, subtotal, 'pending'))
        order_id = cursor.fetchone()[0]
        
        # Add order item
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
            VALUES (%s, %s, %s, %s, %s)
        """, (order_id, product_id, quantity, unit_price, subtotal))
        
        # Update stock
        cursor.execute("""
            UPDATE products SET stock_quantity = stock_quantity - %s
            WHERE id = %s
        """, (quantity, product_id))
        
        # Commit transaction
        conn.commit()
        return order_id
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
