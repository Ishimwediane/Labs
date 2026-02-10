"""
Validation Utilities Module
Reusable validation functions for common data types.
"""

import re
from decimal import Decimal
from typing import Tuple


def validate_email(email: str) -> Tuple[bool, str]:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return False, "Email cannot be empty"
    
    # Simple email pattern
    pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
    
    if re.match(pattern, email):
        return True, ""
    else:
        return False, "Invalid email format"


def validate_price(price: float) -> Tuple[bool, str]:
    """
    Validate product price.
    
    Args:
        price: Price to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if price < 0:
        return False, "Price cannot be negative"
    
    if price > 1000000:
        return False, "Price is too high"
    
    return True, ""


def validate_stock(quantity: int) -> Tuple[bool, str]:
    """
    Validate stock quantity.
    
    Args:
        quantity: Stock quantity to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if quantity < 0:
        return False, "Stock quantity cannot be negative"
    
    if quantity > 100000:
        return False, "Stock quantity is too high"
    
    return True, ""


def validate_name(name: str, min_length: int = 2, max_length: int = 255) -> Tuple[bool, str]:
    """
    Validate name field.
    
    Args:
        name: Name to validate
        min_length: Minimum length allowed
        max_length: Maximum length allowed
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name or not name.strip():
        return False, "Name cannot be empty"
    
    if len(name) < min_length:
        return False, f"Name must be at least {min_length} characters"
    
    if len(name) > max_length:
        return False, f"Name cannot exceed {max_length} characters"
    
    return True, ""
