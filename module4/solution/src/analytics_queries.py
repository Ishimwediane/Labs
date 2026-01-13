from typing import List, Dict
from db_connection import db
from redis_cache import cache


# PRODUCT QUERIES

def list_products() -> List[Dict]:
    """
    Get all products with their category names.
    Uses  INNER JOIN.
    
    Returns:
        List of all products with category information
    """
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT 
                    p.id,
                    p.name,
                    c.name as category,
                    p.price,
                    p.stock_quantity
                FROM products p
                INNER JOIN categories c ON p.category_id = c.id
                ORDER BY p.name;
            """)
            
            results = []
            for row in cur.fetchall():
                results.append({
                    'product_id': row[0],
                    'product_name': row[1],
                    'category': row[2],
                    'price': float(row[3]),
                    'stock': row[4]
                })
            
            print(f"[SUCCESS] Retrieved {len(results)} products")
            return results
    except Exception as e:
        print(f"[ERROR] Error listing products: {e}")
        return []


def top_products(limit: int = 10) -> List[Dict]:
    """
    Get best-selling products using aggregation.
    Uses  JOIN, GROUP BY, and ORDER BY.
    
    Args:
        limit: Number of top products to return
    
    Returns:
        List of top-selling products
    """
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT 
                    p.id,
                    p.name,
                    p.price,
                    SUM(oi.quantity) as total_sold,
                    SUM(oi.subtotal) as revenue
                FROM products p
                INNER JOIN order_items oi ON p.id = oi.product_id
                GROUP BY p.id, p.name, p.price
                ORDER BY total_sold DESC
                LIMIT %s;
            """, (limit,))
            
            results = []
            for row in cur.fetchall():
                results.append({
                    'product_id': row[0],
                    'name': row[1],
                    'price': float(row[2]),
                    'total_sold': row[3],
                    'revenue': float(row[4])
                })
            
            print(f"[SUCCESS] Retrieved top {len(results)} products")
            return results
    except Exception as e:
        print(f"[ERROR] Error getting top products: {e}")
        return []


def products_by_category(category_name: str) -> List[Dict]:
    """
    Get all products in a specific category.
       
    Args:
        category_name: Name of the category
    
    Returns:
        List of products in the category
    """
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT 
                    p.id,
                    p.name,
                    p.price,
                    p.stock_quantity
                FROM products p
                INNER JOIN categories c ON p.category_id = c.id
                WHERE c.name = %s
                ORDER BY p.name;
            """, (category_name,))
            
            results = []
            for row in cur.fetchall():
                results.append({
                    'product_id': row[0],
                    'name': row[1],
                    'price': float(row[2]),
                    'stock': row[3]
                })
            
            print(f"[SUCCESS] Found {len(results)} products in {category_name}")
            return results
    except Exception as e:
        print(f"[ERROR] Error getting products by category: {e}")
        return []

# BASIC CUSTOMER QUERIES

def customer_spending() -> List[Dict]:
    """
    Calculate total spending per customer.
       
    Returns:
        List of customers with their total spending
    """
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT 
                    c.id,
                    c.name,
                    c.email,
                    COUNT(o.id) as order_count,
                    SUM(o.total_amount) as total_spent
                FROM customers c
                INNER JOIN orders o ON c.id = o.customer_id
                GROUP BY c.id, c.name, c.email
                ORDER BY total_spent DESC;
            """)
            
            results = []
            for row in cur.fetchall():
                results.append({
                    'customer_id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'order_count': row[3],
                    'total_spent': float(row[4])
                })
            
            print(f"[SUCCESS] Calculated spending for {len(results)} customers")
            return results
    except Exception as e:
        print(f"[ERROR] Error calculating customer spending: {e}")
        return []


def best_customers(limit: int = 10) -> List[Dict]:
    """
    Get top customers by total spending.
    Args:
        limit: Number of top customers to return
    
    Returns:
        List of top customers
    """
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT 
                    c.id,
                    c.name,
                    c.email,
                    COUNT(o.id) as orders,
                    SUM(o.total_amount) as total_spent
                FROM customers c
                INNER JOIN orders o ON c.id = o.customer_id
                GROUP BY c.id, c.name, c.email
                ORDER BY total_spent DESC
                LIMIT %s;
            """, (limit,))
            
            results = []
            for row in cur.fetchall():
                results.append({
                    'customer_id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'orders': row[3],
                    'total_spent': float(row[4])
                })
            
            print(f"[SUCCESS] Retrieved top {len(results)} customers")
            return results
    except Exception as e:
        print(f"[ERROR] Error getting best customers: {e}")
        return []

# BASIC ORDER QUERIES

def recent_orders(days: int = 30) -> List[Dict]:
    """
    Get recent orders within specified days.
        
    Args:
        days: Number of days to look back
    
    Returns:
        List of recent orders
    """
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT 
                    o.id,
                    c.name as customer_name,
                    o.total_amount,
                    o.status,
                    o.created_at
                FROM orders o
                INNER JOIN customers c ON o.customer_id = c.id
                WHERE o.created_at >= CURRENT_DATE - INTERVAL '%s days'
                ORDER BY o.created_at DESC;
            """, (days,))
            
            results = []
            for row in cur.fetchall():
                results.append({
                    'order_id': row[0],
                    'customer': row[1],
                    'total': float(row[2]),
                    'status': row[3],
                    'date': row[4]
                })
            
            print(f"[SUCCESS] Found {len(results)} orders in last {days} days")
            return results
    except Exception as e:
        print(f"[ERROR] Error getting recent orders: {e}")
        return []


def order_summary(days: int = 30) -> Dict:
    """
    Get summary statistics for orders.
        
    Args:
        days: Number of days to analyze
    
    Returns:
        Dictionary with order statistics
    """
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total_orders,
                    SUM(total_amount) as total_revenue,
                    AVG(total_amount) as avg_order_value,
                    MIN(total_amount) as min_order,
                    MAX(total_amount) as max_order
                FROM orders
                WHERE created_at >= CURRENT_DATE - INTERVAL '%s days';
            """, (days,))
            
            row = cur.fetchone()
            
            summary = {
                'period_days': days,
                'total_orders': row[0] or 0,
                'total_revenue': float(row[1] or 0),
                'avg_order_value': float(row[2] or 0),
                'min_order': float(row[3] or 0),
                'max_order': float(row[4] or 0)
            }
            
            print(f"[SUCCESS] Generated summary for last {days} days")
            return summary
    except Exception as e:
        print(f"[ERROR] Error generating order summary: {e}")
        return {}

# CATEGORY QUERIES

def category_sales() -> List[Dict]:
    """
    Get sales performance by category.
     
    Returns:
        List of categories with sales metrics
    """
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT 
                    c.id,
                    c.name,
                    COUNT(DISTINCT p.id) as product_count,
                    SUM(oi.quantity) as units_sold,
                    SUM(oi.subtotal) as revenue
                FROM categories c
                INNER JOIN products p ON c.id = p.category_id
                INNER JOIN order_items oi ON p.id = oi.product_id
                GROUP BY c.id, c.name
                ORDER BY revenue DESC;
            """)
            
            results = []
            for row in cur.fetchall():
                results.append({
                    'category_id': row[0],
                    'category': row[1],
                    'products': row[2],
                    'units_sold': row[3],
                    'revenue': float(row[4])
                })
            
            print(f"[SUCCESS] Analyzed {len(results)} categories")
            return results
    except Exception as e:
        print(f"[ERROR] Error analyzing category sales: {e}")
        return []


def category_avg_price() -> List[Dict]:
    """
    Get average price per category.
    Uses simple AVG aggregation.
    
    Returns:
        List of categories with average prices
    """
    try:
        with db.get_cursor() as cur:
            cur.execute("""
                SELECT 
                    c.name,
                    COUNT(p.id) as product_count,
                    AVG(p.price) as avg_price,
                    MIN(p.price) as min_price,
                    MAX(p.price) as max_price
                FROM categories c
                INNER JOIN products p ON c.id = p.category_id
                GROUP BY c.name
                ORDER BY avg_price DESC;
            """)
            
            results = []
            for row in cur.fetchall():
                results.append({
                    'category': row[0],
                    'products': row[1],
                    'avg_price': float(row[2]),
                    'min_price': float(row[3]),
                    'max_price': float(row[4])
                })
            
            print(f"[SUCCESS] Calculated prices for {len(results)} categories")
            return results
    except Exception as e:
        print(f"[ERROR] Error calculating category prices: {e}")
        return []


