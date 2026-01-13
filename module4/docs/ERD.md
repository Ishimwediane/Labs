# E-Commerce Database - Entity Relationship Diagram

## Database Schema Overview

This document describes the database schema for the E-Commerce Analytics Data Pipeline.

## Entities and Relationships

```
┌─────────────────┐
│   CUSTOMERS     │
├─────────────────┤
│ id (PK)         │
│ name            │
│ email (UNIQUE)  │
│ address         │
│ created_at      │
└────────┬────────┘
         │
         │ 1:N
         │
         ▼
┌─────────────────┐
│     ORDERS      │
├─────────────────┤
│ id (PK)         │
│ customer_id (FK)│
│ total_amount    │
│ status          │
│ created_at      │
└────────┬────────┘
         │
         │ 1:N
         │
         ▼
┌─────────────────┐       ┌─────────────────┐
│  ORDER_ITEMS    │  N:1  │    PRODUCTS     │
├─────────────────┤◄──────┤─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ order_id (FK)   │       │ name            │
│ product_id (FK) │       │ category_id (FK)│
│ quantity        │       │ price           │
│ unit_price      │       │ stock_quantity  │
│ subtotal        │       │ metadata (JSONB)│
└─────────────────┘       │ created_at      │
                          └────────┬────────┘
                                   │
                                   │ N:1
                                   │
                                   ▼
                          ┌─────────────────┐
                          │   CATEGORIES    │
                          ├─────────────────┤
                          │ id (PK)         │
                          │ name (UNIQUE)   │
                          │ description     │
                          │ created_at      │
                          └─────────────────┘
```

## Relationships

### 1. Customers → Orders (1:N)
- One customer can have multiple orders
- Each order belongs to one customer
- Foreign Key: `orders.customer_id` → `customers.id`

### 2. Orders → Order Items (1:N)
- One order can have multiple order items
- Each order item belongs to one order
- Foreign Key: `order_items.order_id` → `orders.id`

### 3. Products → Order Items (1:N)
- One product can appear in multiple order items
- Each order item references one product
- Foreign Key: `order_items.product_id` → `products.id`

### 4. Categories → Products (1:N)
- One category can have multiple products
- Each product belongs to one category
- Foreign Key: `products.category_id` → `categories.id`

## Constraints

### Primary Keys
- All tables have an auto-incrementing `id` as primary key

### Unique Constraints
- `customers.email` - Email must be unique
- `categories.name` - Category name must be unique

### Foreign Key Constraints
- `orders.customer_id` → `customers.id` (ON DELETE RESTRICT, ON UPDATE CASCADE)
- `products.category_id` → `categories.id` (ON DELETE RESTRICT, ON UPDATE CASCADE)
- `order_items.order_id` → `orders.id` (ON DELETE CASCADE, ON UPDATE CASCADE)
- `order_items.product_id` → `products.id` (ON DELETE RESTRICT, ON UPDATE CASCADE)

### Check Constraints
- `customers.email` - Must match email format pattern
- `products.price` - Must be >= 0
- `products.stock_quantity` - Must be >= 0
- `orders.total_amount` - Must be >= 0
- `orders.status` - Must be one of: 'pending', 'processing', 'shipped', 'delivered', 'cancelled'
- `order_items.quantity` - Must be > 0
- `order_items.unit_price` - Must be >= 0
- `order_items.subtotal` - Must equal quantity * unit_price

## Indexes

### Performance Indexes
- `customers.email` - For fast customer lookup
- `products.category_id` - For category filtering
- `orders.customer_id` - For customer order history
- `orders.created_at` - For date-based queries
- `order_items.order_id` - For order details
- `order_items.product_id` - For product sales analytics

## NoSQL Collections (MongoDB)

### user_sessions
```json
{
  "user_id": "string",
  "created_at": "datetime",
  "last_activity": "datetime",
  "data": {
    "ip_address": "string",
    "user_agent": "string",
    "preferences": {
      "theme": "string",
      "language": "string",
      "currency": "string"
    },
    "last_viewed": ["product_ids"]
  }
}
```

### shopping_carts
```json
{
  "user_id": "string",
  "items": [
    {
      "product_id": "integer",
      "name": "string",
      "price": "float",
      "quantity": "integer"
    }
  ],
  "updated_at": "datetime",
  "item_count": "integer",
  "total_items": "integer"
}
```

## Redis Cache Keys

### Cached Data
- `top_products:best_selling` - Top selling products list
- `product:{id}` - Individual product details

### TTL (Time To Live)
- Top products: 10 minutes (600 seconds)
- Product details: 30 minutes (1800 seconds)
