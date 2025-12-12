# API Design Documentation

## Module: models.py

### Class: User
```python
@dataclass
class User:
    """Represents a user in the system."""
    user_id: int
    name: str
    email: str
```

**Methods**:
- `to_dict() -> dict` - Convert to dictionary
- `from_dict(data: dict) -> User` - Create from dictionary

---

## Module: parser.py

### Class: CSVParser
```python
class CSVParser:
    """Parses CSV files containing user data."""
```

**Constructor**:
```python
def __init__(self, file_path: str) -> None:
    """
    Args:
        file_path: Path to CSV file to parse
    """
```

**Methods**:

#### parse()
```python
def parse(self) -> List[User]:
    """Parse CSV and return list of users.
    
    Returns:
        List of User objects
        
    Raises:
        FileNotFoundError: File doesn't exist
        FileFormatError: Invalid CSV format
    """
```

---

## Module: validator.py

### Class: UserValidator
```python
class UserValidator:
    """Validates user data."""
```

**Methods**:

#### validate()
```python
def validate(self, user: User) -> bool:
    """Validate all user fields.
    
    Args:
        user: User object to validate
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
```

#### validate_email()
```python
def validate_email(self, email: str) -> bool:
    """Check if email format is valid.
    
    Args:
        email: Email string to validate
        
    Returns:
        True if valid format
    """
```

---

## Module: storage.py

### Class: UserRepository
```python
class UserRepository:
    """Manages user storage in JSON database."""
```

**Constructor**:
```python
def __init__(self, db_path: str = "data/database.json") -> None:
    """
    Args:
        db_path: Path to JSON database file
    """
```

**Methods**:

#### add_user()
```python
def add_user(self, user: User) -> None:
    """Add user to database.
    
    Args:
        user: User to add
        
    Raises:
        DuplicateUserError: User ID already exists
        DatabaseError: Cannot write to database
    """
```

#### user_exists()
```python
def user_exists(self, user_id: int) -> bool:
    """Check if user ID exists.
    
    Args:
        user_id: ID to check
        
    Returns:
        True if exists
    """
```

---

## Module: exceptions.py

### Exception Hierarchy
```python
class ImporterError(Exception):
    """Base exception for all importer errors."""

class FileFormatError(ImporterError):
    """Raised when CSV format is invalid."""

class ValidationError(ImporterError):
    """Raised when data validation fails."""

class DuplicateUserError(ImporterError):
    """Raised when duplicate user_id found."""

class DatabaseError(ImporterError):
    """Raised when database operations fail."""
```

---

## Module: main.py

### Function: import_users()
```python
def import_users(csv_path: str) -> None:
    """Import users from CSV file.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        None (outputs to console and logs)
    """
```

### Function: main()
```python
def main() -> None:
    """CLI entry point."""
```

**Command Line Usage**:
```bash
python main.py --file users.csv
python main.py --help
```