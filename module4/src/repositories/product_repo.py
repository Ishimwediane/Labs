import json
from typing import Optional, List
from decimal import Decimal
from src.database.connection import db
from src.models.schemas import Product
from src.utils.logger import log_success, log_error
from src.utils.validators import validate_price, validate_stock, validate_name


class ProductRepository:
    """Repository for product """
    
    def create(self, name: str, category_id: int, price: Decimal,
               stock_quantity: int, metadata: dict = None) -> Optional[int]:
        is_valid, error = validate_name(name)
        if not is_valid:
            log_error(f"Invalid name: {error}")
            return None
        
        is_valid, error = validate_price(float(price))
        if not is_valid:
            log_error(f"Invalid price: {error}")
            return None
        
        is_valid, error = validate_stock(stock_quantity)
        if not is_valid:
            log_error(f"Invalid stock: {error}")
            return None
        
        try:
            with db.get_cursor(commit=True) as cur:
                cur.execute(
                    """
                    INSERT INTO products (name, category_id, price, stock_quantity, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (name, category_id, price, stock_quantity, json.dumps(metadata or {}))
                )
                product_id = cur.fetchone()[0]
                log_success(f"Product created: ID={product_id}, Name={name}")
                return product_id
        except Exception as e:
            log_error(f"Error creating product: {e}")
            return None
    
    def get_by_id(self, product_id: int) -> Optional[Product]:
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    """
                    SELECT p.id, p.name, p.category_id, c.name as category,
                           p.price, p.stock_quantity, p.metadata, p.created_at
                    FROM products p
                    JOIN categories c ON p.category_id = c.id
                    WHERE p.id = %s;
                    """,
                    (product_id,)
                )
                row = cur.fetchone()
                
                if row:
                    return Product(
                        id=row[0],
                        name=row[1],
                        category_id=row[2],
                        category_name=row[3],
                        price=row[4],
                        stock_quantity=row[5],
                        metadata=row[6],
                        created_at=row[7]
                    )
                return None
        except Exception as e:
            log_error(f"Error fetching product: {e}")
            return None
    
    def get_by_category(self, category_id: int) -> List[Product]:
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    """
                    SELECT p.id, p.name, p.category_id, c.name as category,
                           p.price, p.stock_quantity, p.metadata, p.created_at
                    FROM products p
                    JOIN categories c ON p.category_id = c.id
                    WHERE p.category_id = %s
                    ORDER BY p.name;
                    """,
                    (category_id,)
                )
                
                products = []
                for row in cur.fetchall():
                    products.append(Product(
                        id=row[0],
                        name=row[1],
                        category_id=row[2],
                        category_name=row[3],
                        price=row[4],
                        stock_quantity=row[5],
                        metadata=row[6],
                        created_at=row[7]
                    ))
                
                log_success(f"Retrieved {len(products)} products")
                return products
        except Exception as e:
            log_error(f"Error fetching products: {e}")
            return []
    
    def update_stock(self, product_id: int, quantity_change: int) -> bool:
        try:
            with db.get_cursor(commit=True) as cur:
                cur.execute(
                    """
                    UPDATE products
                    SET stock_quantity = stock_quantity + %s
                    WHERE id = %s AND (stock_quantity + %s) >= 0
                    RETURNING stock_quantity;
                    """,
                    (quantity_change, product_id, quantity_change)
                )
                result = cur.fetchone()
                
                if result:
                    log_success(f"Stock updated: Product {product_id}, New stock: {result[0]}")
                    return True
                else:
                    log_error(f"Insufficient stock for product {product_id}")
                    return False
        except Exception as e:
            log_error(f"Error updating stock: {e}")
            return False

product_repo = ProductRepository()
