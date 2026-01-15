"""
Lab demonstrations - Using repository and service layers
"""

from src.database.connection import get_connection
from src.repositories.product_repository import (
    create_product, get_product_by_id, update_product_price, delete_product
)
from src.services.order_service import process_order


def show_connectivity():
    """1. DATABASE CONNECTIVITY - Show psycopg2 connection works"""
    print("\n" + "="*80)
    print("1. DATABASE CONNECTIVITY (psycopg2)")
    print("="*80 + "\n")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"Connected to PostgreSQL: {version[:50]}...")
    
    cursor.execute("SELECT COUNT(*) FROM products")
    print(f"Products in database: {cursor.fetchone()[0]}")
    
    conn.close()
    print("[SUCCESS] Database connection working!")


def show_crud():
    """2. CRUD OPERATIONS - Using repository pattern"""
    print("\n" + "="*80)
    print("2. CRUD OPERATIONS (Create, Read, Update, Delete)")
    print("="*80 + "\n")
    
    # CREATE - Using repository
    print("CREATE: Adding new product...")
    new_product = create_product(
        name="Test Laptop",
        category_id=1,
        price=999.99,
        stock_quantity=10,
        metadata='{"brand": "TestBrand", "color": "Black"}'
    )
    print(f"  Created: {new_product}")
    
    # READ - Using repository
    print("\nREAD: Fetching product...")
    product = get_product_by_id(new_product['id'])
    print(f"  Found: {product['name']} - ${product['price']}")
    
    # UPDATE - Using repository
    print("\nUPDATE: Changing price...")
    updated = update_product_price(new_product['id'], 899.99)
    print(f"  Updated: {updated['name']} - ${updated['price']}")
    
    # DELETE - Using repository
    print("\nDELETE: Removing product...")
    deleted = delete_product(new_product['id'])
    print(f"  Deleted: {deleted['name']}")
    
    print("\n[SUCCESS] CRUD operations completed!")


def show_transactions():
    """3. TRANSACTIONS - Using service layer with ACID properties"""
    print("\n" + "="*80)
    print("3. TRANSACTIONS (ACID Properties)")
    print("="*80 + "\n")
    
    try:
        print("Creating order with transaction...")
        
        # Process order using service (handles transaction)
        order_id = process_order(
            customer_id=1,
            product_id=1,
            quantity=2,
            unit_price=149.99
        )
        
        print(f"  Order created: ID {order_id}")
        print(f"  Order item added")
        print(f"  Stock updated")
        print("\n[SUCCESS] Transaction committed successfully!")
        
    except Exception as e:
        print(f"\n[ERROR] Transaction rolled back: {e}")
