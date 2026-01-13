from typing import Optional, List, Tuple
from decimal import Decimal
from src.database.connection import db
from src.models.schemas import Order, OrderItem
from src.utils.logger import log_success, log_error


class OrderRepository:
    """Repository for order """
    
    def create(self, customer_id: int, items: List[Tuple[int, int]]) -> Optional[int]:
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
                            FOR UPDATE;
                            """,
                            (product_id,)
                        )
                        result = cur.fetchone()
                        
                        if not result:
                            raise ValueError(f"Product {product_id} not found")
                        
                        price, stock, name = result
                        
                        if stock < quantity:
                            raise ValueError(
                                f"Insufficient stock for {name}: "
                                f"{stock} available, {quantity} requested"
                            )
                        
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
                    log_success(
                        f"Order created: ID={order_id}, Total=${total_amount}, Items={len(items)}"
                    )
                    return order_id
                    
        except Exception as e:
            log_error(f"Error creating order: {e}")
            return None
    
    def get_by_id(self, order_id: int) -> Optional[Order]:
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
                    SELECT oi.id, oi.product_id, p.name, oi.quantity,
                           oi.unit_price, oi.subtotal
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    WHERE oi.order_id = %s;
                    """,
                    (order_id,)
                )
                
                items = []
                for item_row in cur.fetchall():
                    items.append(OrderItem(
                        id=item_row[0],
                        order_id=order_id,
                        product_id=item_row[1],
                        product_name=item_row[2],
                        quantity=item_row[3],
                        unit_price=item_row[4],
                        subtotal=item_row[5]
                    ))
                
                return Order(
                    id=order_row[0],
                    customer_id=order_row[1],
                    customer_name=order_row[2],
                    customer_email=order_row[3],
                    total_amount=order_row[4],
                    status=order_row[5],
                    items=items,
                    created_at=order_row[6]
                )
        except Exception as e:
            log_error(f"Error fetching order: {e}")
            return None
    
    def update_status(self, order_id: int, new_status: str) -> bool:
        valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            log_error(f"Invalid status: {new_status}")
            return False
        
        try:
            with db.get_cursor(commit=True) as cur:
                cur.execute(
                    """
                    UPDATE orders
                    SET status = %s
                    WHERE id = %s
                    RETURNING id;
                    """,
                    (new_status, order_id)
                )
                result = cur.fetchone()
                
                if result:
                    log_success(f"Order {order_id} status updated to {new_status}")
                    return True
                else:
                    log_error(f"Order {order_id} not found")
                    return False
        except Exception as e:
            log_error(f"Error updating order status: {e}")
            return False

order_repo = OrderRepository()
