# Lab 1: E-Commerce Analytics Data Pipeline

## Quick Start

```bash
# 1. Setup database (run once)
python setup.py

# 2. Run lab
python main.py
```

## What This Lab Demonstrates

✓ Database connectivity with psycopg2  
✓ CRUD operations (Create, Read, Update, Delete)  
✓ ACID transactions  
✓ Redis caching (optional)  
✓ MongoDB sessions  
✓ Window functions (RANK)  
✓ Common Table Expressions (CTEs)  
✓ JSONB queries  
✓ Performance optimization (EXPLAIN ANALYZE)  

## Project Structure

```
module4/
├── main.py                    # Main entry point
├── setup.py                   # Database setup
├── requirements.txt           # Dependencies
├── docker-compose.yml         # Docker setup
│
├── config/                    # Configuration
│   ├── database.py
│   └── settings.py
│
├── sql/                       # SQL files
│   ├── schema.sql            # Database schema
│   ├── sample_data.sql       # Sample data
│   ├── indexes.sql           # Performance indexes
│   └── advanced_queries.sql  # Advanced SQL queries
│
└── src/                       # Source code
    ├── database/
    │   └── connection.py     # Database connection helper
    ├── repositories/          # Data access layer
    │   ├── product_repository.py  # Product CRUD operations
    │   └── order_repository.py    # Order operations
    ├── services/              # Business logic layer
    │   └── order_service.py       # Order processing with transactions
    └── lab/                   # Lab requirement implementations
        ├── lab_demos.py          # Uses repositories & services
        ├── nosql_demos.py        # NoSQL requirements
        ├── advanced_sql_demos.py # Advanced SQL requirements
        └── performance_demos.py  # Performance requirements
```

## Requirements

- Python 3.11+
- PostgreSQL
- MongoDB Atlas (or local MongoDB)
- Redis (optional)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `.env`:
```
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ecommerce
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

MONGODB_URI=your_mongodb_atlas_uri
MONGODB_DB=ecommerce

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

3. Run setup:
```bash
python setup.py
```

4. Run lab:
```bash
python main.py
```

## Lab Requirements Checklist

- [x] Database schema design (3NF)
- [x] Python DB-API with psycopg2
- [x] Connection pooling
- [x] CRUD operations with parameterized queries
- [x] ACID transactions
- [x] Redis caching
- [x] MongoDB session storage
- [x] JSONB for flexible metadata
- [x] Window functions (RANK)
- [x] Common Table Expressions (CTEs)
- [x] EXPLAIN ANALYZE for performance
- [x] B-tree and GIN indexes

## Author

Amalitech Student - Module 4 Lab 1
