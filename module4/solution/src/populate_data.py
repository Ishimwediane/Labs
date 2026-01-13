"""
Data Population Module - Beginner Level
Simple, straightforward data generation for testing.
Uses clear, predictable patterns instead of complex random logic.
"""

import random
from datetime import datetime, timedelta
from decimal import Decimal
from crud_operations import create_order, get_product_by_id
from mongodb_session import mongodb
from redis_cache import cache
from analytics_queries import top_products
from db_connection import db


def create_sample_orders(num_orders: int = 20):
    """
    Generate sample orders with simple, predictable patterns.
    
    Args:
        num_orders: Number of orders to create
    """
    print(f"\n[INFO] Creating {num_orders} sample orders...\n")
    
    # Simple customer IDs (assuming 8 customers exist)
    customer_ids = [1, 2, 3, 4, 5, 6, 7, 8]
    
    # Simple product IDs (assuming 18 products exist)
    product_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
    
    success_count = 0
    fail_count = 0
    
    for i in range(num_orders):
        # Pick a customer (cycle through all customers)
        customer_id = customer_ids[i % len(customer_ids)]
        
        # Create order with 1-3 items
        num_items = (i % 3) + 1  # Alternates between 1, 2, 3 items
        
        # Pick products
        items = []
        for j in range(num_items):
            # Pick different products for each order
            product_id = product_ids[(i + j) % len(product_ids)]
            quantity = (j % 2) + 1  # Alternates between 1 and 2
            items.append((product_id, quantity))
        
        # Create the order
        order_id = create_order(customer_id, items)
        
        if order_id:
            success_count += 1
            print(f"  Order {i+1}/{num_orders}: [SUCCESS] ID={order_id}, Customer={customer_id}, Items={num_items}")
        else:
            fail_count += 1
            print(f"  Order {i+1}/{num_orders}: [FAILED] Customer={customer_id} (stock issue)")
    
    print(f"\n[SUCCESS] Created {success_count} orders")
    if fail_count > 0:
        print(f"[WARNING] Failed to create {fail_count} orders (insufficient stock)")


def add_sample_sessions():
    """
    Add sample user sessions to MongoDB.
    Uses simple, clear session data.
    """
    print("\n[INFO] Adding sample sessions to MongoDB...\n")
    
    # Simple user list
    users = [
        'alice', 'bob', 'charlie', 'diana',
        'eve', 'frank', 'grace', 'henry'
    ]
    
    themes = ['light', 'dark']
    languages = ['en', 'es', 'fr']
    
    for i, user_id in enumerate(users):
        # Create simple session data
        session_data = {
            'ip_address': f'192.168.1.{i + 100}',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'preferences': {
                'theme': themes[i % 2],  # Alternate between light and dark
                'language': languages[i % 3],  # Cycle through languages
                'currency': 'USD'
            },
            'last_viewed': [1, 2, 3]  # Simple product IDs
        }
        
        mongodb.create_session(user_id, session_data)
        print(f"  [SUCCESS] Session created for user: {user_id}")
    
    print(f"\n[SUCCESS] Created sessions for {len(users)} users")


def add_sample_carts():
    """
    Add sample shopping carts to MongoDB.
    Uses simple cart data.
    """
    print("\n[INFO] Adding sample shopping carts to MongoDB...\n")
    
    # Users who will have carts (half of all users)
    users_with_carts = ['alice', 'charlie', 'eve', 'grace']
    
    for i, user_id in enumerate(users_with_carts):
        # Add 1-2 items to cart
        num_items = (i % 2) + 1
        
        for j in range(num_items):
            product_id = (i * 2 + j + 1)  # Simple product selection
            product = get_product_by_id(product_id)
            
            if product:
                mongodb.add_to_cart(
                    user_id,
                    product_id,
                    quantity=1,
                    name=product['name'],
                    price=product['price']
                )
        
        print(f"  [SUCCESS] Cart created for user: {user_id} ({num_items} items)")
    
    print(f"\n[SUCCESS] Created carts for {len(users_with_carts)} users")


def cache_top_products():
    """
    Cache top-selling products in Redis.
    Simple caching demonstration.
    """
    print("\n[INFO] Caching top products in Redis...\n")
    
    # Get top 10 products
    products = top_products(10)
    
    if products:
        # Cache them with 10-minute expiration
        cache.cache_top_products(products, ttl=600)
        print(f"[SUCCESS] Cached {len(products)} top products (TTL: 10 minutes)")
        
        # Show what was cached
        for i, p in enumerate(products[:5], 1):
            print(f"  {i}. {p['name']}: {p['total_sold']} sold")
    else:
        print("[WARNING] No products to cache (no sales data yet)")


def show_stats():
    """
    Display simple database statistics.
    Uses basic COUNT queries.
    """
    print("\n[INFO] Database Statistics\n")
    print("=" * 60)
    
    try:
        with db.get_cursor() as cur:
            # Count customers
            cur.execute("SELECT COUNT(*) FROM customers;")
            print(f"Customers:    {cur.fetchone()[0]}")
            
            # Count products
            cur.execute("SELECT COUNT(*) FROM products;")
            print(f"Products:     {cur.fetchone()[0]}")
            
            # Count categories
            cur.execute("SELECT COUNT(*) FROM categories;")
            print(f"Categories:   {cur.fetchone()[0]}")
            
            # Count orders
            cur.execute("SELECT COUNT(*) FROM orders;")
            order_count = cur.fetchone()[0]
            print(f"Orders:       {order_count}")
            
            # Count order items
            cur.execute("SELECT COUNT(*) FROM order_items;")
            print(f"Order Items:  {cur.fetchone()[0]}")
            
            # Total revenue
            cur.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders;")
            total_revenue = cur.fetchone()[0]
            print(f"Total Revenue: ${float(total_revenue):,.2f}")
            
            # Average order value
            if order_count > 0:
                avg_order = float(total_revenue) / order_count
                print(f"Avg Order:    ${avg_order:,.2f}")
    
    except Exception as e:
        print(f"[ERROR] Error getting stats: {e}")
    
    print("=" * 60)


if __name__ == "__main__":
    """Main execution - populate database with sample data."""
    
    print("\n" + "=" * 60)
    print("E-COMMERCE DATA POPULATION - BEGINNER LEVEL")
    print("=" * 60)
    
    # Step 1: Create sample orders
    print("\n[STEP 1] Creating Sample Orders")
    create_sample_orders(20)
    
    # Step 2: Add MongoDB sessions
    print("\n[STEP 2] Adding User Sessions")
    add_sample_sessions()
    
    # Step 3: Add MongoDB shopping carts
    print("\n[STEP 3] Adding Shopping Carts")
    add_sample_carts()
    
    # Step 4: Cache top products in Redis
    print("\n[STEP 4] Caching Top Products")
    cache_top_products()
    
    # Step 5: Show statistics
    print("\n[STEP 5] Database Statistics")
    show_stats()
    
    print("\n[SUCCESS] Data population complete!\n")
