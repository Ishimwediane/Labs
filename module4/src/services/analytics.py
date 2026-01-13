from typing import List, Dict
from src.database.connection import db
from src.utils.logger import log_success, log_error


class AnalyticsService:
    """Service for analytics and reporting """
    
    # PRODUCT ANALYTICS
    
    def get_top_products(self, limit: int = 10) -> List[Dict]:
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    """
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
                    """,
                    (limit,)
                )
                
                results = []
                for row in cur.fetchall():
                    results.append({
                        'product_id': row[0],
                        'name': row[1],
                        'price': float(row[2]),
                        'total_sold': row[3],
                        'revenue': float(row[4])
                    })
                
                log_success(f"Retrieved top {len(results)} products")
                return results
        except Exception as e:
            log_error(f"Error getting top products: {e}")
            return []
    
    def get_products_by_category(self, category_name: str) -> List[Dict]:
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    """
                    SELECT 
                        p.id,
                        p.name,
                        p.price,
                        p.stock_quantity
                    FROM products p
                    INNER JOIN categories c ON p.category_id = c.id
                    WHERE c.name = %s
                    ORDER BY p.name;
                    """,
                    (category_name,)
                )
                
                results = []
                for row in cur.fetchall():
                    results.append({
                        'product_id': row[0],
                        'name': row[1],
                        'price': float(row[2]),
                        'stock': row[3]
                    })
                
                log_success(f"Found {len(results)} products in {category_name}")
                return results
        except Exception as e:
            log_error(f"Error getting products by category: {e}")
            return []
    
    # CUSTOMER ANALYTICS
    
    def get_customer_spending(self) -> List[Dict]:
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    """
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
                    """
                )
                
                results = []
                for row in cur.fetchall():
                    results.append({
                        'customer_id': row[0],
                        'name': row[1],
                        'email': row[2],
                        'order_count': row[3],
                        'total_spent': float(row[4])
                    })
                
                log_success(f"Calculated spending for {len(results)} customers")
                return results
        except Exception as e:
            log_error(f"Error calculating customer spending: {e}")
            return []
    
    def get_best_customers(self, limit: int = 10) -> List[Dict]:
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    """
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
                    """,
                    (limit,)
                )
                
                results = []
                for row in cur.fetchall():
                    results.append({
                        'customer_id': row[0],
                        'name': row[1],
                        'email': row[2],
                        'orders': row[3],
                        'total_spent': float(row[4])
                    })
                
                log_success(f"Retrieved top {len(results)} customers")
                return results
        except Exception as e:
            log_error(f"Error getting best customers: {e}")
            return []
    
    # ORDER ANALYTICS
    
    def get_recent_orders(self, days: int = 30) -> List[Dict]:
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    """
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
                    """,
                    (days,)
                )
                
                results = []
                for row in cur.fetchall():
                    results.append({
                        'order_id': row[0],
                        'customer': row[1],
                        'total': float(row[2]),
                        'status': row[3],
                        'date': row[4]
                    })
                
                log_success(f"Found {len(results)} orders in last {days} days")
                return results
        except Exception as e:
            log_error(f"Error getting recent orders: {e}")
            return []
    
    def get_order_summary(self, days: int = 30) -> Dict:
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    """
                    SELECT 
                        COUNT(*) as total_orders,
                        SUM(total_amount) as total_revenue,
                        AVG(total_amount) as avg_order_value,
                        MIN(total_amount) as min_order,
                        MAX(total_amount) as max_order
                    FROM orders
                    WHERE created_at >= CURRENT_DATE - INTERVAL '%s days';
                    """,
                    (days,)
                )
                
                row = cur.fetchone()
                
                summary = {
                    'period_days': days,
                    'total_orders': row[0] or 0,
                    'total_revenue': float(row[1] or 0),
                    'avg_order_value': float(row[2] or 0),
                    'min_order': float(row[3] or 0),
                    'max_order': float(row[4] or 0)
                }
                
                log_success(f"Generated summary for last {days} days")
                return summary
        except Exception as e:
            log_error(f"Error generating order summary: {e}")
            return {}
    
    # CATEGORY ANALYTICS
    
    def get_category_sales(self) -> List[Dict]:
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    """
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
                    """
                )
                
                results = []
                for row in cur.fetchall():
                    results.append({
                        'category_id': row[0],
                        'category': row[1],
                        'products': row[2],
                        'units_sold': row[3],
                        'revenue': float(row[4])
                    })
                
                log_success(f"Analyzed {len(results)} categories")
                return results
        except Exception as e:
            log_error(f"Error analyzing category sales: {e}")
            return []

analytics = AnalyticsService()
