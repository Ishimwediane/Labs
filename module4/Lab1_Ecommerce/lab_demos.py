from src.database.connection import get_connection
from src.repositories.product_repository import (
    create_product, get_product_by_id, update_product_price, delete_product
)
from src.services.order_service import process_order


def show_connectivity():
    print("\n" + "="*80)
    print("DATABASE CONNECTIVITY (psycopg2)")
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
    print("\n" + "="*80)
    print("CRUD OPERATIONS (Create, Read, Update, Delete)")
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
    print("\n" + "="*80)
    print("TRANSACTIONS (ACID Properties)")
    print("="*80 + "\n")
    
    try:
        print("Creating order with transaction...")
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


if __name__ == "__main__":
    try:
        show_connectivity()
        show_crud()
        show_transactions()
    except Exception as e:
        print(f"Error running demos: {e}")
