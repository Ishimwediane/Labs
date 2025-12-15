# Git Workflow Guide

## Initial Setup
```bash
# Initialize Git
git init

# Create develop branch
git checkout -b develop

# First commit
git add .
git commit -m "chore: Initial project setup"
```

## Branch Naming Convention
feature/feature-name    # New features
bugfix/bug-name        # Bug fixes
hotfix/urgent-fix      # Critical fixes
docs/documentation     # Documentation only
test/test-name         # Test additions
## Feature Development Workflow

### 1. Start Feature
```bash
# Create feature branch from develop
git checkout develop
git checkout -b feature/csv-parser

# Work on feature...
```

### 2. Commit Changes
```bash
# Stage changes
git add src/parser.py

# Commit with proper message
git commit -m "feat(parser): Add CSV parsing logic"
```

### 3. Push Feature
```bash
# Push to remote
git push -u origin feature/csv-parser
```

### 4. Create Pull Request
- Go to GitHub
- Click "New Pull Request"
- Base: develop ← Compare: feature/csv-parser
- Fill out PR template
- Request review (self-review for lab)

### 5. Merge Feature
```bash
# After approval, merge on GitHub
# Then update local develop
git checkout develop
git pull origin develop

# Delete feature branch
git branch -d feature/csv-parser
git push origin --delete feature/csv-parser
```

## Commit Message Standards

### Format
<type>(<scope>): <subject>
<body>
<footer>
````
Types

feat: New feature
fix: Bug fix
docs: Documentation
style: Formatting
refactor: Code restructuring
test: Adding tests
chore: Maintenance

Examples
bashgit commit -m "feat(parser): Add CSV parsing with error handling"
git commit -m "test(validator): Add email validation tests"
git commit -m "docs(readme): Add installation instructions"
git commit -m "fix(storage): Handle corrupted JSON files"