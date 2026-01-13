# Project Architecture

## System Architecture Overview

The E-Commerce Analytics Data Pipeline follows a layered architecture pattern with clear separation of concerns.

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                            │
│              (Scripts, Tests, External Apps)                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    SERVICES LAYER                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Analytics   │  │    Cache     │  │     Cart     │      │
│  │   Service    │  │   Service    │  │   Service    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐                                           │
│  │   Session    │         Business Logic Layer              │
│  │   Service    │                                           │
│  └──────────────┘                                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                 REPOSITORIES LAYER                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Customer    │  │   Product    │  │    Order     │      │
│  │ Repository   │  │ Repository   │  │ Repository   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                   Data Access Layer                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   MODELS LAYER                               │
│  ┌──────────────────────────────────────────────────┐       │
│  │  Customer, Product, Order, OrderItem Schemas     │       │
│  └──────────────────────────────────────────────────┘       │
│                   Data Models                                │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                  DATABASE LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  PostgreSQL  │  │   MongoDB    │  │    Redis     │      │
│  │  Connection  │  │    Client    │  │    Client    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                Connection Managers                           │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                 CONFIGURATION LAYER                          │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │   Settings   │  │   Database   │                         │
│  │              │  │    Config    │                         │
│  └──────────────┘  └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    UTILITIES LAYER                           │
│  (Logger, Validators, Formatters, Query Builders)           │
│                  Cross-cutting Concerns                      │
└─────────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### 1. Configuration Layer (`config/`)
**Purpose**: Centralized configuration management

**Components**:
- `settings.py` - Environment variables, connection strings
- `database.py` - Database-specific configuration, TTL settings

**Responsibilities**:
- Load environment variables
- Validate configuration
- Provide configuration to other layers

### 2. Database Layer (`src/database/`)
**Purpose**: Database connection management

**Components**:
- `connection.py` - PostgreSQL connection manager
- `mongo_client.py` - MongoDB client
- `redis_client.py` - Redis client

**Responsibilities**:
- Establish database connections
- Provide context managers for safe operations
- Handle connection pooling
- Test connections

### 3. Models Layer (`src/models/`)
**Purpose**: Data structure definitions

**Components**:
- `schemas.py` - Customer, Product, Order, OrderItem models

**Responsibilities**:
- Define data structures
- Provide type safety
- Document data fields

### 4. Repository Layer (`src/repositories/`)
**Purpose**: Data access and CRUD operations

**Components**:
- `customer_repo.py` - Customer CRUD
- `product_repo.py` - Product CRUD
- `order_repo.py` - Order CRUD (with ACID transactions)

**Responsibilities**:
- Create, Read, Update, Delete operations
- Input validation
- Database queries
- Transaction management

### 5. Services Layer (`src/services/`)
**Purpose**: Business logic and complex operations

**Components**:
- `analytics.py` - Analytics queries and reporting
- `cache_service.py` - Caching operations
- `cart_service.py` - Shopping cart management
- `session_service.py` - User session management

**Responsibilities**:
- Complex business logic
- Multi-repository operations
- Analytics and reporting
- Caching strategies

### 6. Utilities Layer (`src/utils/`)
**Purpose**: Reusable helper functions

**Components**:
- `logger.py` - Logging utilities
- `validators.py` - Input validation
- `formatters.py` - Data formatting
- `query_builder.py` - SQL query helpers

**Responsibilities**:
- Cross-cutting concerns
- Reusable utilities
- Code deduplication

## Data Flow

### Example: Creating an Order

```
1. Client/Script
   ↓
2. order_repo.create(customer_id, items)
   ↓
3. Database Layer (PostgreSQL connection)
   ↓
4. ACID Transaction:
   - Check stock (FOR UPDATE lock)
   - Create order record
   - Create order_items records
   - Update product stock
   - Commit transaction
   ↓
5. Return order_id to client
```

### Example: Analytics with Caching

```
1. Client requests top products
   ↓
2. analytics.get_top_products()
   ↓
3. Check cache_service.get_top_products()
   ↓
4. If cache miss:
   - Query PostgreSQL (JOIN products + order_items)
   - cache_service.cache_top_products()
   ↓
5. Return results to client
```

## Design Patterns

### 1. Repository Pattern
- Abstracts data access logic
- Each entity has its own repository
- Provides clean API for CRUD operations

### 2. Service Layer Pattern
- Encapsulates business logic
- Coordinates between multiple repositories
- Handles complex operations

### 3. Dependency Injection
- Layers depend on abstractions
- Easy to test and mock
- Loose coupling

### 4. Context Manager Pattern
- Safe resource management
- Automatic cleanup
- Transaction handling

## Technology Stack

### Databases
- **PostgreSQL**: Relational data (customers, products, orders)
- **MongoDB**: Unstructured data (sessions, carts)
- **Redis**: Caching layer

### Python Libraries
- `psycopg2-binary`: PostgreSQL adapter
- `pymongo`: MongoDB driver
- `redis`: Redis client
- `python-dotenv`: Environment management
- `pytest`: Testing framework

## Scalability Considerations

### Horizontal Scaling
- Stateless services layer
- Connection pooling for databases
- Redis for distributed caching

### Performance Optimization
- Indexes on frequently queried columns
- Redis caching for expensive queries
- ACID transactions for data consistency
- Query optimization with query builders

### Maintainability
- Clear separation of concerns
- Small, focused modules (< 150 lines)
- Comprehensive documentation
- Extensive test coverage
