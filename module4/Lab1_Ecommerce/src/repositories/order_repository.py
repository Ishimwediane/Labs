from src.database.connection import get_connection


def create_order(customer_id, total_amount, status='pending'):
    """Create a new order"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO orders (customer_id, total_amount, status)
        VALUES (%s, %s, %s) RETURNING id
    """, (customer_id, total_amount, status))
    
    order_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return order_id


def create_order_item(order_id, product_id, quantity, unit_price, subtotal):
    """Create order item"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
        VALUES (%s, %s, %s, %s, %s)
    """, (order_id, product_id, quantity, unit_price, subtotal))
    
    conn.commit()
    conn.close()


def update_product_stock(product_id, quantity):
    """Update product stock"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE products SET stock_quantity = stock_quantity - %s
        WHERE id = %s
    """, (quantity, product_id))
    
    conn.commit()
    conn.close()
