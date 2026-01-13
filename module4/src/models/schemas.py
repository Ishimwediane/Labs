from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, List


@dataclass
class Customer:
    """Customer data model."""
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    address: str = ""
    created_at: Optional[datetime] = None


@dataclass
class Product:
    """Product data model."""
    id: Optional[int] = None
    name: str = ""
    category_id: int = 0
    category_name: Optional[str] = None
    price: Decimal = Decimal('0.00')
    stock_quantity: int = 0
    metadata: Optional[Dict] = None
    created_at: Optional[datetime] = None


@dataclass
class OrderItem:
    """Order item data model."""
    id: Optional[int] = None
    order_id: int = 0
    product_id: int = 0
    product_name: Optional[str] = None
    quantity: int = 0
    unit_price: Decimal = Decimal('0.00')
    subtotal: Decimal = Decimal('0.00')


@dataclass
class Order:
    """Order data model."""
    id: Optional[int] = None
    customer_id: int = 0
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    total_amount: Decimal = Decimal('0.00')
    status: str = "pending"
    items: Optional[List[OrderItem]] = None
    created_at: Optional[datetime] = None
