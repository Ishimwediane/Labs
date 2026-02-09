# Python Labs - Complete Submission Repository

This repository contains my comprehensive solutions for Python programming labs across multiple modules, covering OOP fundamentals, clean code practices, advanced Python concepts, and database integration.

##  Repository Overview

This repository is organized into **5 modules**, each containing multiple labs that progressively build Python development skills:

| Module | Focus Area | Labs | Status |
|--------|-----------|------|--------|
| **Module 1** | OOP Fundamentals | 4 Labs | ✅ Complete |
| **Module 2** | Clean Code & Testing | 4 Labs | ✅ Complete |
| **Module 3** | Advanced Python | 2 Labs | ✅ Complete |
| **Module 4** | Database Integration | 1 Lab | ✅ Complete |
| **Module 5** | Django Microservices | 1 Lab | ✅ Complete |

---

##  Module 1: Object-Oriented Programming Fundamentals

**Focus**: Core OOP principles, inheritance, polymorphism, encapsulation, and abstraction.

### Labs

| Lab | Project | Description | Key Concepts |
|-----|---------|-------------|--------------|
| 1 | [Employee Payroll Tracker](./module1/Employee-Payroll-Tracker) | Console-based payroll management system | Classes, Inheritance, Polymorphism, Abstract Base Classes |
| 2 | [Library Management System](./module1/library-management) | Library book and member management | Encapsulation, Class Design, Data Structures |
| 3 | [Student Management System](./module1/student-management-system) | Student records and grade tracking | OOP Design Patterns, File I/O |
| 4 | [Vehicle Rental System](./module1/vehicle-rental) | Vehicle rental and booking management | Inheritance Hierarchies, Business Logic |

### Key Features
- **Employee Payroll Tracker**: Supports Full-Time, Contract, and Intern employees with automatic tax calculation and payslip generation
- **Library Management**: Book cataloging, member management, borrowing/returning workflows
- **Student Management**: Grade tracking, GPA calculation, student records management
- **Vehicle Rental**: Multi-vehicle type support, rental calculations, booking system

---

##  Module 2: Clean Code, Testing & Git

**Focus**: Clean code principles, TDD, testing strategies, and professional Git workflows.

### Labs

| Lab | Project | Description | Key Concepts |
|-----|---------|-------------|--------------|
| 1 | [Resilient Data Importer](./module2/resilient-data-importer) | CSV data import with validation and error handling | Exception Handling, File I/O, Data Validation |
| 2 | [Weather API Stub](./module2/weather-api-stub) | TDD-based weather service with mock provider | TDD, Mocking, Dependency Injection |
| 3 | [Secure Service Module](./module2/secure-service-module) | Authentication module with password hashing | Security, bcrypt, Interface Design |
| 4 | [Data Processing Pipeline](./module2/data_processing_pipeline) | Multi-stage data pipeline with sentiment analysis | Pipeline Architecture, Database Integration |

### Key Features
- **Resilient Data Importer**: Email validation, duplicate detection, JSON storage with atomic writes
- **Weather API Stub**: Mock provider pattern, SOLID principles, comprehensive test coverage
- **Secure Service Module**: User authentication, password hashing with bcrypt, 100% test coverage
- **Data Processing Pipeline**: Text cleaning, sentiment analysis, PostgreSQL/SQLite integration

---

##  Module 3: Advanced Python Concepts

**Focus**: Advanced data structures, collections, async programming, and performance optimization.

### Labs

| Lab | Project | Description | Key Concepts |
|-----|---------|-------------|--------------|
| 1 | [Student Grade Analytics Tool](./module3/lab1-Student-Grade-Analytics-Tool) | CSV-based grade analytics with advanced collections | `dataclasses`, `Counter`, `defaultdict`, `deque`, Type Hints |
| 5 | [Async Web Scraper](./module3/lab5-Async-Web-Scraper) | Multi-approach web scraper with benchmarking | `asyncio`, `aiohttp`, Threading, Performance Comparison |

### Key Features
- **Grade Analytics Tool**: 
  - Advanced collections (`Counter`, `defaultdict`, `OrderedDict`, `deque`)
  - Comprehensive type hinting with `TypedDict`
  - Grade distribution analysis and rolling averages
  
- **Async Web Scraper**:
  - Three implementations: Sequential, Threaded, Async
  - Performance benchmarking and comparison
  - Utility decorators (`@retry`, `@log_execution`)
  - Async generators for data processing

---

##  Module 4: Database Integration & Analytics

**Focus**: Database design, SQL optimization, NoSQL integration, and data pipeline architecture.

### Labs

| Lab | Project | Description | Key Concepts |
|-----|---------|-------------|--------------|
| 1 | [E-Commerce Analytics Pipeline](./module4/Lab1_Ecommerce) | Full-stack data pipeline with PostgreSQL, MongoDB, Redis | Database Design, CRUD, Transactions, Caching, Advanced SQL |

### Key Features
- **Database Schema**: 3NF normalized design with ER diagram
- **PostgreSQL Integration**: 
  - Connection pooling with psycopg2
  - CRUD operations with parameterized queries
  - ACID transactions
  - Window functions (RANK)
  - Common Table Expressions (CTEs)
  - JSONB for flexible metadata
  - Performance optimization with EXPLAIN ANALYZE
  
- **NoSQL Integration**:
  - MongoDB Atlas for session storage
  - Redis caching layer
  
- **Architecture**:
  - Repository pattern for data access
  - Service layer for business logic
  - Clean separation of concerns

---

##  Module 5: Django Microservices

**Focus**: RESTful API development, microservices architecture, Docker containerization, and API documentation.

### Labs

| Lab | Project | Description | Key Concepts |
|-----|---------|-------------|--------------|
| 1 | [URL Shortener Microservice](./module5) | Django REST API for URL shortening with Redis caching | Django REST Framework, Redis, Docker, OpenAPI/Swagger, Microservices |

### Key Features
- **Django REST Framework**: 
  - RESTful API design with proper HTTP methods
  - Serializers for data validation
  - ViewSets and API views
  - Interactive Swagger UI documentation
  
- **Caching Layer**:
  - Redis integration for fast URL lookups
  - Cache-aside pattern implementation
  
- **Containerization**:
  - Docker multi-stage builds
  - Docker Compose orchestration
  - Production-ready configuration
  
- **Architecture**:
  - Service layer pattern
  - Clean separation of concerns
  - RESTful resource design

---

##  Complete Repository Structure

```
Labs/
├── README.md                           # This file
│
├── module1/                            # OOP Fundamentals
│   ├── Employee-Payroll-Tracker/
│   ├── library-management/
│   ├── student-management-system/
│   └── vehicle-rental/
│
├── module2/                            # Clean Code & Testing
│   ├── resilient-data-importer/
│   ├── weather-api-stub/
│   ├── secure-service-module/
│   └── data_processing_pipeline/
│
├── module3/                            # Advanced Python
│   ├── lab1-Student-Grade-Analytics-Tool/
│   ├── lab5-Async-Web-Scraper/
│   └── .pre-commit-config.yaml
│
├── module4/                            # Database Integration
│   └── Lab1_Ecommerce/
│
└── module5/                            # Django Microservices
    └── url/                            # URL Shortener Microservice
```

---

##  Quick Start Guide

### Prerequisites
- **Python 3.11+** (required for all modules)
- **PostgreSQL** (Module 4)
- **MongoDB** (Module 4 - Atlas or local)
- **Redis** (Module 4 & 5)
- **Docker & Docker Compose** (Module 5 - recommended)

### General Setup for Any Lab

1. **Navigate to the specific lab directory**
   ```bash
   cd module2/resilient-data-importer
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   
   # macOS/Linux
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the lab** (see individual lab README for specific instructions)
   ```bash
   python main.py
   ```

5. **Run tests** (where applicable)
   ```bash
   pytest -v
   ```

---

##  Learning Objectives Demonstrated

### Core Python Skills
- ✅ **OOP Principles**: Classes, inheritance, polymorphism, encapsulation, abstraction
- ✅ **Clean Code**: SOLID principles, DRY, separation of concerns
- ✅ **Type Safety**: Comprehensive type hints, static type checking with mypy
- ✅ **Error Handling**: Custom exceptions, graceful error recovery
- ✅ **File I/O**: CSV parsing, JSON serialization, context managers, `pathlib`

### Advanced Concepts
- ✅ **Data Structures**: `Counter`, `defaultdict`, `OrderedDict`, `deque`, `dataclasses`
- ✅ **Async Programming**: `asyncio`, `aiohttp`, concurrent execution
- ✅ **Performance**: Benchmarking, optimization, threading vs async comparison
- ✅ **Decorators**: Custom decorators for retry logic and logging

### Testing & Quality
- ✅ **Testing**: Unit tests, integration tests, TDD workflow, >80% coverage
- ✅ **Mocking**: Mock objects, dependency injection, test isolation
- ✅ **Code Quality**: Black formatting, ruff linting, mypy type checking
- ✅ **Pre-commit Hooks**: Automated quality checks

### Database & Integration
- ✅ **SQL**: Database design (3NF), CRUD operations, transactions, indexes
- ✅ **Advanced SQL**: Window functions, CTEs, JSONB queries, query optimization
- ✅ **NoSQL**: MongoDB document storage, Redis caching
- ✅ **Architecture**: Repository pattern, service layer, connection pooling

### Professional Practices
- ✅ **Git Workflow**: Feature branches, conventional commits, pull requests
- ✅ **Documentation**: Comprehensive README files, docstrings, code comments
- ✅ **Project Structure**: Modular design, clear separation of concerns
- ✅ **Environment Management**: Virtual environments, dependency management

---

##  Testing Strategy

### Module 2 & 4: Comprehensive Test Suites

```bash
# Run all Module 2 tests
cd module2
pytest resilient-data-importer/tests/ -v
pytest weather-api-stub/tests/ -v
pytest secure-service-module/tests/ -v
pytest data_processing_pipeline/tests/ -v

# Run Module 4 tests (if available)
cd module4/Lab1_Ecommerce
pytest tests/ -v
```

### Test Coverage
- **Unit Tests**: Individual component testing in isolation
- **Integration Tests**: End-to-end workflow validation
- **Coverage Target**: >80% across all tested modules

---

##  Code Quality Standards

All projects adhere to professional Python standards:

| Tool | Purpose | Status |
|------|---------|--------|
| **Type Hints** | Full type annotations throughout | ✅ |
| **Docstrings** | Comprehensive function/class documentation | ✅ |
| **PEP 8** | Python style guide compliance | ✅ |
| **Black** | Consistent code formatting | ✅ |
| **Ruff** | Fast Python linting | ✅ |
| **Mypy** | Static type checking | ✅ |
| **Pre-commit** | Automated quality checks (Module 3) | ✅ |

---

##  Git Workflow

### Branching Strategy

```
main (production-ready code)
  └── developer (main development branch)
       ├── feature/module1-*
       ├── feature/module2-*
       ├── feature/module3-*
       └── feature/module4-*
```

### Commit Convention

Following [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New features and lab implementations
- `fix:` - Bug fixes and corrections
- `test:` - Test additions or modifications
- `docs:` - Documentation updates
- `refactor:` - Code refactoring without feature changes
- `style:` - Code style and formatting changes

---

##  Technologies & Libraries

### Core Python
- **Python 3.11+** - Modern Python features
- **dataclasses** - Structured data modeling
- **typing** - Type hints and annotations
- **pathlib** - Modern file path handling
- **collections** - Advanced data structures

### Testing & Quality
- **pytest** - Testing framework
- **black** - Code formatter
- **mypy** - Static type checker
- **ruff** - Fast Python linter
- **pre-commit** - Git hooks for quality checks

### Security & Authentication
- **bcrypt** - Password hashing (Module 2, Lab 3)

### Database & Integration
- **psycopg2** - PostgreSQL adapter (Module 2 & 4)
- **pymongo** - MongoDB driver (Module 4)
- **redis** - Redis client (Module 4 & 5)
- **testcontainers** - Integration testing (Module 2, Lab 4)

### Async & Web
- **asyncio** - Asynchronous programming (Module 3)
- **aiohttp** - Async HTTP client (Module 3)

### Django & REST APIs
- **Django 5.0** - Web framework (Module 5)
- **Django REST Framework** - RESTful API toolkit (Module 5)
- **drf-spectacular** - OpenAPI/Swagger documentation (Module 5)
- **gunicorn** - WSGI HTTP server (Module 5)

---

##  Documentation

Each lab includes comprehensive documentation:

- **README.md**: Project overview, setup instructions, usage examples
- **docs/** (where applicable): Architecture diagrams, design decisions
- **Inline Comments**: Complex logic explanations
- **Docstrings**: Function and class documentation
- **Type Hints**: Self-documenting code through annotations

---

## ✅ Completion Status

### Module 1: OOP Fundamentals
- [x] Employee Payroll Tracker
- [x] Library Management System
- [x] Student Management System
- [x] Vehicle Rental System

### Module 2: Clean Code & Testing
- [x] Resilient Data Importer
- [x] Weather API Stub
- [x] Secure Service Module
- [x] Data Processing Pipeline

### Module 3: Advanced Python
- [x] Student Grade Analytics Tool
- [x] Async Web Scraper

### Module 4: Database Integration
- [x] E-Commerce Analytics Pipeline

### Module 5: Django Microservices
- [x] URL Shortener Microservice

### Overall
- [x] All 12 labs implemented
- [x] Comprehensive documentation
- [x] Code quality standards met
- [x] Git repository properly structured
- [x] Individual README files for each lab

---

##  Author

**Diane Ishimwe**
- Email: ishimwediane400@gmail.com
- GitHub: [@Ishimwediane](https://github.com/Ishimwediane)

---

##  Submission Information

- **Academic Period**: 2025-2026
- **Program**: Python Backend and AI application Track
- **Repository**: Complete lab submissions across 5 modules

---

##  Acknowledgments

- Course instructors for comprehensive lab requirements and guidance
- Python community for excellent libraries and tools
- Clean Code principles by Robert C. Martin
- Real-world project inspirations for practical applications

---

##  Notes

- Each module builds upon previous concepts, creating a progressive learning path
- All labs are self-contained and can be run independently
- Database labs (Module 4) require additional setup (PostgreSQL, MongoDB, Redis)
- Django labs (Module 5) support both Docker and local development
- Async labs (Module 3) demonstrate performance optimization techniques
- Testing labs (Module 2) showcase professional TDD workflows

---

**Thank you for reviewing my comprehensive Python lab work!** 🚀

*This repository demonstrates proficiency in Python fundamentals, OOP, clean code practices, advanced concepts, testing strategies, database integration, and Django microservices development.*
