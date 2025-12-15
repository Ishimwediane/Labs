# Testing Strategy

## Test Coverage Goals

| Module        | Coverage Target | Priority |
|---------------|----------------|----------|
| models.py     | 100%           | High     |
| exceptions.py | 100%           | High     |
| validator.py  | 100%           | High     |
| parser.py     | 95%            | High     |
| storage.py    | 95%            | High     |
| main.py       | 90%            | Medium   |

## Test Types

### Unit Tests
Test individual functions/methods in isolation.

### Integration Tests
Test multiple components working together.

### End-to-End Tests
Test entire workflow from CLI to database.

## Test Cases

### CSVParser Tests

#### test_parse_valid_csv
**Description**: Parse valid CSV successfully
**Input**: CSV with 3 valid users
**Expected**: List of 3 User objects
**Type**: Unit test

#### test_parse_missing_file
**Description**: Handle missing file gracefully
**Input**: Non-existent file path
**Expected**: FileNotFoundError raised
**Type**: Unit test

#### test_parse_empty_file
**Description**: Handle empty CSV
**Input**: Empty CSV file
**Expected**: Empty list returned
**Type**: Unit test

#### test_parse_malformed_csv
**Description**: Handle malformed CSV
**Input**: CSV with missing columns
**Expected**: FileFormatError raised
**Type**: Unit test

### UserValidator Tests

#### test_validate_valid_email
**Description**: Accept valid email
**Input**: "user@example.com"
**Expected**: True
**Type**: Unit test

#### test_validate_invalid_email
**Description**: Reject invalid email
**Input**: "notanemail"
**Expected**: False
**Type**: Unit test

#### test_validate_empty_name
**Description**: Reject empty name
**Input**: User with name=""
**Expected**: ValidationError raised
**Type**: Unit test

### UserRepository Tests

#### test_add_user_success
**Description**: Add new user successfully
**Input**: Valid User object
**Expected**: User saved to database
**Type**: Unit test (mocked)

#### test_add_duplicate_user
**Description**: Reject duplicate user_id
**Input**: User with existing ID
**Expected**: DuplicateUserError raised
**Type**: Unit test (mocked)

### Integration Tests

#### test_end_to_end_import
**Description**: Complete import process
**Input**: CSV file with mixed valid/invalid data
**Expected**: Valid users imported, invalid skipped
**Type**: Integration test

## Mocking Strategy

### What to Mock
- File system operations (open, read, write)
- JSON database operations
- Logging outputs

### What NOT to Mock
- Data validation logic
- User model creation
- Exception handling

## Test Fixtures

### valid_csv
```python
@pytest.fixture
def valid_csv(tmp_path):
    """Create temporary valid CSV file."""
    csv_file = tmp_path / "users.csv"
    csv_file.write_text(
        "user_id,name,email\n"
        "1,John Doe,john@example.com\n"
        "2,Jane Smith,jane@example.com\n"
    )
    return csv_file
```

### empty_database
```python
@pytest.fixture
def empty_database(tmp_path):
    """Create empty JSON database."""
    db_file = tmp_path / "database.json"
    db_file.write_text("{}")
    return db_file
```

## Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_parser.py

# Run with verbose output
pytest -v

# Run and stop at first failure
pytest -x
```

## Success Criteria
- [ ] All tests pass
- [ ] Coverage >90%
- [ ] No warnings
- [ ] Fast execution (<10 seconds)