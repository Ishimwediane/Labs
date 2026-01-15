from src.database.connection import get_connection
from psycopg2.extras import RealDictCursor


def create_product(name, category_id, price, stock_quantity, metadata):
    """Create a new product"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        INSERT INTO products (name, category_id, price, stock_quantity, metadata)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, name, price
    """, (name, category_id, price, stock_quantity, metadata))
    
    product = cursor.fetchone()
    conn.commit()
    conn.close()
    return product


def get_product_by_id(product_id):
    """Get product by ID"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    
    conn.close()
    return product


def update_product_price(product_id, new_price):
    """Update product price"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        UPDATE products SET price = %s WHERE id = %s
        RETURNING id, name, price
    """, (new_price, product_id))
    
    product = cursor.fetchone()
    conn.commit()
    conn.close()
    return product


def delete_product(product_id):
    """Delete product by ID"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("DELETE FROM products WHERE id = %s RETURNING name", (product_id,))
    product = cursor.fetchone()
    
    conn.commit()
    conn.close()
    return product


def get_top_products(limit=5):
    """Get top products by price"""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT id, name, price FROM products 
        ORDER BY price DESC LIMIT %s
    """, (limit,))
    
    products = cursor.fetchall()
    conn.close()
    return products
