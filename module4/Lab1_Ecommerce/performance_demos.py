from src.database.connection import get_connection


def show_explain_analyze():
    print("\n" + "="*80)
    print("PERFORMANCE OPTIMIZATION - EXPLAIN ANALYZE")
    print("="*80 + "\n")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Force Index Scans for all queries in this demo
    print("SET enable_seqscan = off;")
    cursor.execute("SET enable_seqscan = off;")
    
    # 1. Customer Index Demo
    print("\n--- 1. Customer ID Query (Using Index) ---")
    print("Query: SELECT * FROM orders WHERE customer_id = 1")
    cursor.execute("""
        EXPLAIN ANALYZE
        SELECT * FROM orders WHERE customer_id = 1
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}")
        
    # 2. Price Index Demo (New)
    print("\n--- 2. Price Query (Using New Index) ---")
    print("Query: SELECT * FROM products WHERE price > 100")
    cursor.execute("""
        EXPLAIN ANALYZE
        SELECT * FROM products WHERE price > 100
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}")
        
    # Reset configuration
    cursor.execute("SET enable_seqscan = on;")
    
    conn.close()
    print("\n[SUCCESS] Query analysis completed!")


if __name__ == "__main__":
    try:
        show_explain_analyze()
    except Exception as e:
        print(f"Error running demos: {e}")
