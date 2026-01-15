"""
Setup script - Load schema and sample data
Run this BEFORE main.py
"""

import psycopg2
from config.database import DatabaseConfig


def setup_database():
    """Setup database with schema and sample data"""
    config = DatabaseConfig.get_postgres_config()
    conn = psycopg2.connect(**config)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("="*80)
    print("DATABASE SETUP")
    print("="*80 + "\n")
    
    try:
        # Load schema
        print("1. Loading schema...")
        with open('sql/schema.sql', 'r', encoding='utf-8') as f:
            cursor.execute(f.read())
        print("   [SUCCESS] Schema loaded\n")
        
        # Load sample data
        print("2. Loading sample data...")
        with open('sql/sample_data.sql', 'r', encoding='utf-8') as f:
            cursor.execute(f.read())
        print("   [SUCCESS] Sample data loaded\n")
        
        # Create indexes
        print("3. Creating indexes...")
        with open('sql/indexes.sql', 'r', encoding='utf-8') as f:
            cursor.execute(f.read())
        print("   [SUCCESS] Indexes created\n")
        
        # Verify
        print("4. Verifying data...")
        cursor.execute("SELECT COUNT(*) FROM categories")
        print(f"   - Categories: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM customers")
        print(f"   - Customers: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM products")
        print(f"   - Products: {cursor.fetchone()[0]}")
        
        print("\n" + "="*80)
        print("SETUP COMPLETE! You can now run: python main.py")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    setup_database()
