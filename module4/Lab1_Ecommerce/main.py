from lab_demos import show_connectivity, show_crud, show_transactions
from nosql_demos import show_redis_cache, show_mongodb_sessions
from advanced_sql_demos import show_window_functions, show_cte, show_jsonb
from performance_demos import show_explain_analyze


def main():
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

        print("Summary:")
        print(" Database connectivity with psycopg2")
        print(" CRUD operations with parameterized queries")
        print(" ACID transactions")
        print(" Redis caching")
        print(" MongoDB sessions")
        print(" Window functions (RANK)")
        print(" Common Table Expressions (CTEs)")
        print(" JSONB queries")
        print(" Query optimization (EXPLAIN ANALYZE)")
        
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
