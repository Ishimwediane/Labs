from src.database.connection import get_connection


def show_explain_analyze():
    print("\n" + "="*80)
    print("PERFORMANCE OPTIMIZATION - EXPLAIN ANALYZE")
    print("="*80 + "\n")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    print("Query: Find all orders for customer_id = 1")
    cursor.execute("""
        EXPLAIN ANALYZE
        SELECT * FROM orders WHERE customer_id = 1
    """)
    
    print("\nExecution Plan:")
    for row in cursor.fetchall():
        print(f"  {row[0]}")
    
    conn.close()
    print("\n[SUCCESS] Query analysis completed!")
