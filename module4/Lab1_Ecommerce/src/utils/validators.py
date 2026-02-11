import re
from decimal import Decimal
from typing import Tuple


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email format.

    """
    if not email:
        return False, "Email cannot be empty"
    
    # email pattern
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    
    if re.match(pattern, email):
        return True, ""
    else:
        return False, "Invalid email format"


def validate_price(price: float) -> Tuple[bool, str]:
    """
    Validate product price.

    """
    if price < 0:
        return False, "Price cannot be negative"
    
    if price > 1000000:
        return False, "Price is too high"
    
    return True, ""


def validate_stock(quantity: int) -> Tuple[bool, str]:
    """
    Validate stock quantity.

    """
    if quantity < 0:
        return False, "Stock quantity cannot be negative"
    
    if quantity > 100000:
        return False, "Stock quantity is too high"
    
    return True, ""


def validate_name(name: str, min_length: int = 2, max_length: int = 255) -> Tuple[bool, str]:
    """
    Validate name field.

    """
    if not name or not name.strip():
        return False, "Name cannot be empty"
    
    if len(name) < min_length:
        return False, f"Name must be at least {min_length} characters"
    
    if len(name) > max_length:
        return False, f"Name cannot exceed {max_length} characters"
    
    return True, ""
