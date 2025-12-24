# Clean Code Labs - Submission Repository

This repository contains my solutions for the Clean Code, Testing & Git labs.

## 📚 Labs Overview

| Lab | Project | Description | Status |
|-----|---------|-------------|--------|
| Lab 1 | [resilient-data-importer](./resilient-data-importer) | Resilient Data Importer CLI with CSV parsing, validation, and JSON storage | ✅ Complete |
| Lab 2 | [weather-api-stub](./weather-api-stub) | TDD-based Weather API Service Stub with mock provider | ✅ Complete |
| Lab 3 | [secure-service-module](./secure-service-module) | Secure Service Module with TDD and authentication | ✅ Complete |
| Lab 4 | [data_processing_pipeline](./data_processing_pipeline) | Multi-Stage Data Processing Pipeline | ✅ Complete |

---

## 🎯 Learning Objectives

These labs demonstrate proficiency in:

- **Clean Code Principles**: SOLID, DRY, separation of concerns
- **Exception Handling**: Custom exceptions, graceful error handling
- **Testing**: Unit tests, integration tests, TDD workflow
- **Python Best Practices**: Type hints, docstrings, PEP 8
- **Git Workflow**: Feature branches, conventional commits, pull requests
- **Code Quality**: Black, mypy, ruff, pre-commit hooks

---

## 🏗️ Repository Structure

```
module2/
├── resilient-data-importer/     # Lab 1: Data import CLI
│   ├── src/
│   ├── tests/
│   ├── docs/
│   └── README.md
├── weather-api-stub/            # Lab 2: API service stub
│   ├── src/
│   ├── tests/
│   └── README.md
├── secure-service-module/       # Lab 3: Authentication module
│   ├── src/auth/
│   ├── tests/
│   └── README.md
├── data_processing_pipeline/    # Lab 4: Data pipeline
│   ├── src/
│   ├── tests/
│   └── README.md
└── README.md                    # This file
```

---

## 🚀 Quick Start

Each lab is self-contained with its own dependencies and documentation.

### General Setup

1. **Navigate to a lab directory**
   ```bash
   cd resilient-data-importer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\\Scripts\\activate  # Windows
   source .venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run tests**
   ```bash
   pytest -v
   ```

5. **See lab-specific README for usage instructions**

---

## 🧪 Testing

All labs include comprehensive test suites:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test end-to-end workflows
- **Test Coverage**: >80% coverage across all labs

### Run All Tests

```bash
# From repository root
pytest resilient-data-importer/tests/ -v
pytest weather-api-stub/tests/ -v
pytest secure-service-module/tests/ -v
pytest data_processing_pipeline/tests/ -v
```

---

## 📋 Code Quality

All projects follow strict code quality standards:

- ✅ **Type Hints**: Full type annotations
- ✅ **Docstrings**: Comprehensive documentation
- ✅ **PEP 8**: Style guide compliance
- ✅ **Linting**: Ruff for code quality
- ✅ **Formatting**: Black for consistent style
- ✅ **Type Checking**: Mypy for type safety

---

## 🌿 Git Workflow

This repository follows a structured branching strategy:

```
main (production-ready code)
  └── developer (main development branch)
       ├── feature/lab1-data-importer
       ├── feature/lab2-api-stub
       ├── feature/lab3-secure-service
       └── feature/lab4-pipeline
```

### Branch Naming Convention

- `feature/lab{N}-{description}` - Lab implementations
- `fix/lab{N}-{description}` - Bug fixes
- `docs/lab{N}-{description}` - Documentation updates

### Commit Message Format

Following [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New features
- `fix:` - Bug fixes
- `test:` - Test additions/modifications
- `docs:` - Documentation updates
- `refactor:` - Code refactoring
- `style:` - Code style changes

---

## 📊 Lab Highlights

### Lab 1: Resilient Data Importer
- CSV parsing with error handling
- Email validation
- Duplicate detection
- JSON storage with atomic writes
- Comprehensive logging

### Lab 2: Weather API Stub
- TDD workflow demonstration
- Mock provider pattern
- Dependency injection
- Custom exceptions
- SOLID principles

### Lab 3: Secure Service Module
- User authentication
- Password hashing with bcrypt
- Interface-based design
- Dependency inversion
- 100% test coverage

### Lab 4: Data Processing Pipeline
- Multi-stage pipeline architecture
- Text cleaning and sentiment analysis
- Database integration (PostgreSQL/SQLite)
- Custom exceptions per stage
- Integration testing with testcontainers

---

## 🛠️ Technologies Used

- **Python 3.11+**
- **pytest** - Testing framework
- **black** - Code formatter
- **mypy** - Static type checker
- **ruff** - Fast Python linter
- **bcrypt** - Password hashing (Lab 3)
- **psycopg2** - PostgreSQL adapter (Lab 4)
- **testcontainers** - Integration testing (Lab 4)

---

## 📖 Documentation

Each lab includes detailed documentation:

- **README.md**: Project overview, installation, usage
- **docs/**: Architecture diagrams, API design, testing strategy
- **Code comments**: Inline documentation for complex logic
- **Docstrings**: Function and class documentation

---

## ✅ Completion Checklist

- [x] All 4 labs implemented
- [x] Comprehensive test suites
- [x] Documentation complete
- [x] Code quality checks passing
- [x] Git repository initialized
- [x] README files for all labs
- [x] .gitignore files configured

---

## 👤 Author

**Your Name**
- Email: your.email@example.com
- GitHub: [@Ishimwediane](https://github.com/Ishimwediane)

---

## 📅 Submission Date

December 2025

---

## 🙏 Acknowledgments

- Course instructors for comprehensive lab requirements
- Python community for excellent testing tools
- Clean Code principles by Robert C. Martin

---

**Thank you for reviewing my work!** 🚀
