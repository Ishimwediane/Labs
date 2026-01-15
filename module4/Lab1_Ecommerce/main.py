"""
Lab 1: E-Commerce Analytics Data Pipeline
Main entry point - Executes all lab requirements

Run: python main.py
"""

from src.lab.lab_demos import show_connectivity, show_crud, show_transactions
from src.lab.nosql_demos import show_redis_cache, show_mongodb_sessions
from src.lab.advanced_sql_demos import show_window_functions, show_cte, show_jsonb
from src.lab.performance_demos import show_explain_analyze


def main():
    """Execute all lab requirements"""
    print("\n" + "="*80)
    print("LAB 1: E-COMMERCE ANALYTICS DATA PIPELINE")
    print("="*80)
    
    try:
        # 1. Database Connectivity
        show_connectivity()
        
        # 2. CRUD Operations
        show_crud()
        
        # 3. Transactions
        show_transactions()
        
        # 4. NoSQL Integration
        show_redis_cache()
        show_mongodb_sessions()
        
        # 5. Advanced SQL
        show_window_functions()
        show_cte()
        show_jsonb()
        
        # 6. Performance
        show_explain_analyze()
        
        # Summary
        print("\n" + "="*80)
        print("ALL LAB REQUIREMENTS COMPLETED")
        print("="*80 + "\n")
        print("Summary:")
        print("[OK] Database connectivity with psycopg2")
        print("[OK] CRUD operations with parameterized queries")
        print("[OK] ACID transactions")
        print("[OK] Redis caching")
        print("[OK] MongoDB sessions")
        print("[OK] Window functions (RANK)")
        print("[OK] Common Table Expressions (CTEs)")
        print("[OK] JSONB queries")
        print("[OK] Query optimization (EXPLAIN ANALYZE)")
        print("\n[SUCCESS] All lab requirements completed!\n")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
