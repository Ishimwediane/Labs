from src.database.connection import get_connection
from psycopg2.extras import RealDictCursor


def show_window_functions():
    print("\n" + "="*80)
    print("WINDOW FUNCTION - Product Rankings")
    print("="*80 + "\n")
    
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT 
            p.name AS product_name,
            c.name AS category_name,
            p.price,
            RANK() OVER (PARTITION BY c.name ORDER BY p.price DESC) AS price_rank
        FROM products p
        JOIN categories c ON p.category_id = c.id
        ORDER BY c.name, price_rank
        LIMIT 10
    """)
    
    results = cursor.fetchall()
    for row in results:
        print(f"  {row['category_name']}: {row['product_name']} (${row['price']}) - Rank {row['price_rank']}")
    
    conn.close()
    print("\n[SUCCESS] Window function executed!")


def show_cte():
    print("\n" + "="*80)
    print("Customer Revenue Analysis")
    print("="*80 + "\n")
    
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        WITH customer_stats AS (
            SELECT 
                c.id,
                c.name,
                COUNT(o.id) AS total_orders,
                COALESCE(SUM(o.total_amount), 0) AS total_revenue
            FROM customers c
            LEFT JOIN orders o ON c.id = o.customer_id
            GROUP BY c.id, c.name
        )
        SELECT 
            name,
            total_orders,
            ROUND(total_revenue::numeric, 2) AS revenue,
            CASE 
                WHEN total_revenue > 1000 THEN 'VIP'
                WHEN total_revenue > 500 THEN 'Gold'
                ELSE 'Bronze'
            END AS tier
        FROM customer_stats
        ORDER BY total_revenue DESC
        LIMIT 5
    """)
    
    results = cursor.fetchall()
    for row in results:
        print(f"  {row['name']}: {row['total_orders']} orders, ${row['revenue']} ({row['tier']})")
    
    conn.close()
    print("\n[SUCCESS] CTE query executed!")


def show_jsonb():
    print("\n" + "="*80)
    print("JSONB - Flexible Product Metadata")
    print("="*80 + "\n")
    
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT name, price, metadata->>'brand' AS brand, metadata->>'color' AS color
        FROM products
        WHERE metadata ? 'brand'
        LIMIT 5
    """)
    
    results = cursor.fetchall()
    for row in results:
        print(f"  {row['name']}: {row['brand']} ({row['color']}) - ${row['price']}")
    
    conn.close()
    print("\n[SUCCESS] JSONB query executed!")


if __name__ == "__main__":
    try:
        show_window_functions()
        show_cte()
        show_jsonb()
    except Exception as e:
        print(f"Error running demos: {e}")
