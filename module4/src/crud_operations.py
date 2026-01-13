from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from db_connection import db


# CUSTOMER OPERATIONS


def create_customer(name: str, email: str, address: str) -> Optional[int]:
    """
    Create a new customer with parameterized query.
    
    Args:
        name: Customer full name
        email: Unique email address
        address: Shipping address
    
    Returns:
        Customer ID if successful, None otherwise
    """
    try:
        with db.get_cursor(commit=True) as cur:
            cur.execute(
                """
                INSERT INTO customers (name, email, address)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (name, email, address)
            )
            customer_id = cur.fetchone()[0]
            print(f"Customer created: ID={customer_id}, Email={email}")
            return customer_id
    except Exception as e:
        print(f"Error creating customer: {e}")
        return None


def get_customer_by_id(customer_id: int) -> Optional[Dict]:
    """
    Retrieve customer by ID.
    
    Args:
        customer_id: Customer ID
    
    Returns:
        Dictionary with customer data or None
    """
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT id, name, email, address, created_at
                FROM customers
                WHERE id = %s;
                """,
                (customer_id,)
            )
            row = cur.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'address': row[3],
                    'created_at': row[4]
                }
            return None
    except Exception as e:
        print(f"Error fetching customer: {e}")
        return None


def get_customer_orders(customer_id: int) -> List[Dict]:
    """
    Get all orders for a specific customer with JOIN.
    
    Args:
        customer_id: Customer ID
    
    Returns:
        List of order dictionaries
    """
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT 
                    o.id,
                    o.total_amount,
                    o.status,
                    o.created_at,
                    COUNT(oi.id) as item_count
                FROM orders o
                LEFT JOIN order_items oi ON o.id = oi.order_id
                WHERE o.customer_id = %s
                GROUP BY o.id, o.total_amount, o.status, o.created_at
                ORDER BY o.created_at DESC;
                """,
                (customer_id,)
            )
            orders = []
            for row in cur.fetchall():
                orders.append({
                    'order_id': row[0],
                    'total_amount': float(row[1]),
                    'status': row[2],
                    'created_at': row[3],
                    'item_count': row[4]
                })
            return orders
    except Exception as e:
        print(f"Error fetching customer orders: {e}")
        return []

# PRODUCT OPERATIONS

def add_product(name: str, category_id: int, price: Decimal, 
                stock_quantity: int, metadata: Dict = None) -> Optional[int]:
    """
    Add a new product with JSONB metadata.
    
    Args:
        name: Product name
        category_id: Category ID (foreign key)
        price: Product price
        stock_quantity: Available stock
        metadata: JSONB metadata (color, size, brand, etc.)
    
    Returns:
        Product ID if successful, None otherwise
    """
    import json
    
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
            print(f"Product created: ID={product_id}, Name={name}")
            return product_id
    except Exception as e:
        print(f"Error creating product: {e}")
        return None


def get_product_by_id(product_id: int) -> Optional[Dict]:
    """
    Retrieve product by ID including JSONB metadata.
    
    Args:
        product_id: Product ID
    
    Returns:
        Dictionary with product data or None
    """
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT p.id, p.name, p.price, p.stock_quantity, p.metadata, c.name as category
                FROM products p
                JOIN categories c ON p.category_id = c.id
                WHERE p.id = %s;
                """,
                (product_id,)
            )
            row = cur.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'price': float(row[2]),
                    'stock_quantity': row[3],
                    'metadata': row[4],
                    'category': row[5]
                }
            return None
    except Exception as e:
        print(f"Error fetching product: {e}")
        return None


def update_product_stock(product_id: int, quantity_change: int) -> bool:
    """
    Update product stock quantity.
    
    Args:
        product_id: Product ID
        quantity_change: Amount to add/subtract from stock
    
    Returns:
        True if successful, False otherwise
    """
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
                print(f"Stock updated: Product {product_id}, New stock: {result[0]}")
                return True
            else:
                print(f"Insufficient stock for product {product_id}")
                return False
    except Exception as e:
        print(f"Error updating stock: {e}")
        return False

# ORDER OPERATIONS (ACID TRANSACTIONS)

def create_order(customer_id: int, items: List[Tuple[int, int]]) -> Optional[int]:
    """
    Create an order with ACID transaction.
    Atomically: check stock, update stock, create order, create order items.
    
    Args:
        customer_id: Customer ID
        items: List of (product_id, quantity) tuples
    
    Returns:
        Order ID if successful, None otherwise
    """
    try:
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                total_amount = Decimal('0.00')
                order_details = []
                
                for product_id, quantity in items:
                    cur.execute(
                        """
                        SELECT price, stock_quantity, name
                        FROM products
                        WHERE id = %s
                        FOR UPDATE;  -- Lock row for update
                        """,
                        (product_id,)
                    )
                    result = cur.fetchone()
                    
                    if not result:
                        raise ValueError(f"Product {product_id} not found")
                    
                    price, stock, name = result
                    
                    if stock < quantity:
                        raise ValueError(f"Insufficient stock for {name}: {stock} available, {quantity} requested")
                    
                    subtotal = price * quantity
                    total_amount += subtotal
                    order_details.append((product_id, quantity, price, subtotal, name))

                cur.execute(
                    """
                    INSERT INTO orders (customer_id, total_amount, status)
                    VALUES (%s, %s, 'pending')
                    RETURNING id;
                    """,
                    (customer_id, total_amount)
                )
                order_id = cur.fetchone()[0]

                for product_id, quantity, price, subtotal, name in order_details:
                    cur.execute(
                        """
                        INSERT INTO order_items (order_id, product_id, quantity, unit_price, subtotal)
                        VALUES (%s, %s, %s, %s, %s);
                        """,
                        (order_id, product_id, quantity, price, subtotal)
                    )
        
                    cur.execute(
                        """
                        UPDATE products
                        SET stock_quantity = stock_quantity - %s
                        WHERE id = %s;
                        """,
                        (quantity, product_id)
                    )

                conn.commit()
                print(f"Order created: ID={order_id}, Total=${total_amount}, Items={len(items)}")
                return order_id
                
    except Exception as e:
        print(f"Error creating order: {e}")
        return None


def get_order_details(order_id: int) -> Optional[Dict]:
    """
    Get complete order details with items.
    
    Args:
        order_id: Order ID
    
    Returns:
        Dictionary with order and items data
    """
    try:
        with db.get_cursor() as cur:
            cur.execute(
                """
                SELECT o.id, o.customer_id, c.name, c.email, 
                       o.total_amount, o.status, o.created_at
                FROM orders o
                JOIN customers c ON o.customer_id = c.id
                WHERE o.id = %s;
                """,
                (order_id,)
            )
            order_row = cur.fetchone()
            
            if not order_row:
                return None
            cur.execute(
                """
                SELECT oi.product_id, p.name, oi.quantity, oi.unit_price, oi.subtotal
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = %s;
                """,
                (order_id,)
            )
            items = []
            for item_row in cur.fetchall():
                items.append({
                    'product_id': item_row[0],
                    'product_name': item_row[1],
                    'quantity': item_row[2],
                    'unit_price': float(item_row[3]),
                    'subtotal': float(item_row[4])
                })
            
            return {
                'order_id': order_row[0],
                'customer_id': order_row[1],
                'customer_name': order_row[2],
                'customer_email': order_row[3],
                'total_amount': float(order_row[4]),
                'status': order_row[5],
                'created_at': order_row[6],
                'items': items
            }
    except Exception as e:
        print(f"Error fetching order details: {e}")
        return None


