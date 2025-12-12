# System Architecture

## Overview
The Resilient Data Importer follows a layered architecture with clear separation of concerns.

## Architecture Diagram
See: `diagrams/architecture.png`

## Layers

### 1. CLI Layer
**Responsibility**: User interaction
**Components**: 
- `main.py` - Entry point, argument parsing

### 2. Business Logic Layer
**Responsibility**: Core application logic
**Components**:
- `parser.py` - CSV parsing
- `validator.py` - Data validation
- `storage.py` - Data persistence

### 3. Data Layer
**Responsibility**: Data structures and exceptions
**Components**:
- `models.py` - User dataclass
- `exceptions.py` - Custom exceptions

### 4. Infrastructure Layer
**Responsibility**: External interactions
**Components**:
- File system (CSV, JSON)
- Logging system

## Component Interactions
User Input → CLI → Parser → Validator → Storage → JSON Database
↓         ↓          ↓
Logger ← Logger ← Logger
↓         ↓          ↓
Exceptions → Console
## Design Patterns Used

### Repository Pattern
**Where**: `storage.py`
**Why**: Abstracts data access logic

### Context Manager Pattern
**Where**: `DatabaseContext` in `storage.py`
**Why**: Ensures proper resource cleanup

### Factory Pattern
**Where**: User creation in `parser.py`
**Why**: Centralizes object creation logic

## Data Flow

1. **Input**: User runs CLI command with CSV file
2. **Parse**: CSV parsed into rows
3. **Validate**: Each row validated for correctness
4. **Check**: Duplicate check against database
5. **Store**: Valid, unique users saved to JSON
6. **Output**: Summary displayed to user

## Error Handling Strategy

All errors inherit from `ImporterError` base class.
Errors are caught at the CLI layer and displayed to user.
All errors are logged with appropriate severity.


## Layered diagram
```mermaid
graph TB
    %% Presentation Layer
    subgraph "Presentation Layer"
        CLI[CLI Interface / main.py]
    end

    %% Business Logic Layer
    subgraph "Business Logic Layer"
        Parser[CSVParser / parser.py]
        Validator[UserValidator / validator.py]
    end

    %% Data Access Layer
    subgraph "Data Access Layer"
        Repository[UserRepository / storage.py]
    end

    %% Domain Layer
    subgraph "Domain Layer"
        UserModel[User Model / models.py]
        Exceptions[Exceptions / exceptions.py]
    end

    %% Data Storage
    subgraph "Data Storage"
        JSONDB[(JSON Database)]
    end

    %% Cross-Cutting
    Logger[Logger / logging system]

    %% Arrows: Presentation → Business → Data → Storage
    CLI --> Parser
    CLI --> Validator

    Parser --> Validator
    Parser --> Exceptions
    Validator --> Exceptions

    Validator --> Repository
    Repository --> JSONDB
    Repository --> Exceptions

    %% Domain Layer
    Parser --> UserModel
    Validator --> UserModel
    Repository --> UserModel

    %% Cross-Cutting
    CLI --> Logger
    Parser --> Logger
    Validator --> Logger
    Repository --> Logger

    %% Styling
    style CLI fill:#e1f5ff
    style Parser fill:#fff3e0
    style Validator fill:#fff3e0
    style Repository fill:#e8f5e9
    style UserModel fill:#f3e5f5
    style Exceptions fill:#ffebee
    style Logger fill:#fffde7
    style JSONDB fill:#fce4ec

```

## Data flow diagram
```mermaid
graph TB
    %% External Actor / Input
    subgraph "External Actor / Input"
        User[User]
        CSVFile[CSV File]
    end

    %% Presentation Layer
    subgraph "Presentation Layer"
        CLI[CLI Interface / main.py]
    end

    %% Business Logic Layer
    subgraph "Business Logic Layer"
        Parser[CSVParser / parser.py]
        Validator[UserValidator / validator.py]
    end

    %% Data Access Layer
    subgraph "Data Access Layer"
        Repository[UserRepository / storage.py]
    end

    %% Domain Layer
    subgraph "Domain Layer"
        UserModel[User Model / models.py]
        Exceptions[Exceptions / exceptions.py]
    end

    %% Data Storage
    subgraph "Data Storage"
        JSONDB[(JSON Database)]
    end

    %% Cross-Cutting
    Logger[Logger / logging system]

    %% Main Data Flow
    User -->|runs CLI| CLI
    CLI -->|reads| CSVFile
    CLI --> Parser
    Parser --> Validator
    Validator --> Repository
    Repository --> JSONDB

    %% Domain interactions
    Parser --> UserModel
    Validator --> UserModel
    Repository --> UserModel

    %% Exception Handling
    Parser --> Exceptions
    Validator --> Exceptions
    Repository --> Exceptions

    %% Logging
    CLI --> Logger
    Parser --> Logger
    Validator --> Logger
    Repository --> Logger

    %% Styling
    style User fill:#e0f7fa
    style CSVFile fill:#fffde7
    style CLI fill:#e1f5ff
    style Parser fill:#fff3e0
    style Validator fill:#fff3e0
    style Repository fill:#e8f5e9
    style UserModel fill:#f3e5f5
    style Exceptions fill:#ffebee
    style Logger fill:#fffde7
    style JSONDB fill:#fce4ec
```