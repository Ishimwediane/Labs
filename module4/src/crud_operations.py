from db_connection import execute_query

# CUSTOMER OPERATIONS

def create_customer(name, email, address):
    """Add new customer"""
    try:
        result = execute_query(
            "INSERT INTO customers(name,email,address) VALUES(%s,%s,%s) RETURNING id;",
            (name, email, address),
            commit=True
        )
        customer_id = result[0][0]
        print(f"✅ Customer created: ID={customer_id}")
        return customer_id
    except Exception as e:
        print(f"❌ Error creating customer: {e}")


def get_customer(customer_id):
    """Get customer by id"""
    try:
        result = execute_query(
            "SELECT id,name,email,address FROM customers WHERE id=%s;",
            (customer_id,)
        )
        if result:
            row = result[0]
            return {
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "address": row[3]
            }
        return None
    except Exception as e:
        print(f"❌ Error getting customer: {e}")


# PRODUCT OPERATIONS

def add_product(name, price, stock):
    """Add new product"""
    try:
        result = execute_query(
            "INSERT INTO products(name,price,stock_quantity) VALUES(%s,%s,%s) RETURNING id;",
            (name, price, stock),
            commit=True
        )
        product_id = result[0][0]
        print(f"✅ Product created: ID={product_id}")
        return product_id
    except Exception as e:
        print(f"❌ Error creating product: {e}")


def get_product(product_id):
    """Get product by id"""
    try:
        result = execute_query(
            "SELECT id,name,price,stock_quantity FROM products WHERE id=%s;",
            (product_id,)
        )
        if result:
            row = result[0]
            return {
                "id": row[0],
                "name": row[1],
                "price": float(row[2]),
                "stock_quantity": row[3]
            }
        return None
    except Exception as e:
        print(f"❌ Error getting product: {e}")


# ORDER OPERATIONS

def create_order(customer_id, items):
    """
    Create an order.
    items = [(product_id, quantity), ...]
    """
    try:
      
        total = 0
        for product_id, quantity in items:
            result = execute_query(
                "SELECT price, stock_quantity FROM products WHERE id=%s;",
                (product_id,)
            )
            if not result:
                raise ValueError(f"Product with ID {product_id} not found")
            price, stock = result[0]
            if stock < quantity:
                raise ValueError(f"Insufficient stock for product ID {product_id}")
            total += price * quantity

       
        result = execute_query(
            "INSERT INTO orders(customer_id,total_amount,status) VALUES(%s,%s,'pending') RETURNING id;",
            (customer_id, total),
            commit=True
        )
        order_id = result[0][0]

     
        for product_id, quantity in items:
            execute_query(
                "UPDATE products SET stock_quantity=stock_quantity-%s WHERE id=%s;",
                (quantity, product_id),
                commit=True
            )

        print(f"✅ Order created: ID={order_id}")
        return order_id

    except Exception as e:
        print(f"❌ Error creating order: {e}")
