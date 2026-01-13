from typing import Optional, List, Dict
from src.database.connection import db
from src.models.schemas import Customer
from src.utils.logger import log_success, log_error
from src.utils.validators import validate_email, validate_name


class CustomerRepository:
    """Repository for customer """
    
    def create(self, name: str, email: str, address: str) -> Optional[int]:
        is_valid, error = validate_name(name)
        if not is_valid:
            log_error(f"Invalid name: {error}")
            return None
        
        is_valid, error = validate_email(email)
        if not is_valid:
            log_error(f"Invalid email: {error}")
            return None
        
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
                log_success(f"Customer created: ID={customer_id}, Email={email}")
                return customer_id
        except Exception as e:
            log_error(f"Error creating customer: {e}")
            return None
    
    def get_by_id(self, customer_id: int) -> Optional[Customer]:
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
                    return Customer(
                        id=row[0],
                        name=row[1],
                        email=row[2],
                        address=row[3],
                        created_at=row[4]
                    )
                return None
        except Exception as e:
            log_error(f"Error fetching customer: {e}")
            return None
    
    def get_all(self) -> List[Customer]:
        try:
            with db.get_cursor() as cur:
                cur.execute(
                    """
                    SELECT id, name, email, address, created_at
                    FROM customers
                    ORDER BY name;
                    """
                )
                
                customers = []
                for row in cur.fetchall():
                    customers.append(Customer(
                        id=row[0],
                        name=row[1],
                        email=row[2],
                        address=row[3],
                        created_at=row[4]
                    ))
                
                log_success(f"Retrieved {len(customers)} customers")
                return customers
        except Exception as e:
            log_error(f"Error fetching customers: {e}")
            return []
    
    def update(self, customer_id: int, name: str = None, 
               email: str = None, address: str = None) -> bool:
        updates = []
        params = []
        
        if name:
            is_valid, error = validate_name(name)
            if not is_valid:
                log_error(f"Invalid name: {error}")
                return False
            updates.append("name = %s")
            params.append(name)
        
        if email:
            is_valid, error = validate_email(email)
            if not is_valid:
                log_error(f"Invalid email: {error}")
                return False
            updates.append("email = %s")
            params.append(email)
        
        if address:
            updates.append("address = %s")
            params.append(address)
        
        if not updates:
            log_error("No fields to update")
            return False
        
        params.append(customer_id)
        
        try:
            with db.get_cursor(commit=True) as cur:
                query = f"""
                    UPDATE customers
                    SET {', '.join(updates)}
                    WHERE id = %s
                    RETURNING id;
                """
                cur.execute(query, tuple(params))
                result = cur.fetchone()
                
                if result:
                    log_success(f"Customer {customer_id} updated")
                    return True
                else:
                    log_error(f"Customer {customer_id} not found")
                    return False
        except Exception as e:
            log_error(f"Error updating customer: {e}")
            return False

customer_repo = CustomerRepository()
