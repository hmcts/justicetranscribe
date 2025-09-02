# Contributing to JusticeTranscribe

## Testing and Coverage

### Important: Working Directory for Tests

When running pytest and coverage commands, always run them from the `backend/` directory:

```bash
# Correct - run from backend directory
cd backend/
python -m pytest tests/unit/
coverage run -m pytest tests/unit/
coverage report

# Incorrect - do not run from project root
python -m pytest backend/tests/unit/  # This may cause issues
```

### Running Tests

```bash
cd backend/
python -m pytest                    # Run all unit tests
python -m pytest --integration      # Include integration tests
python -m pytest -m e2e            # E2E tests only
```

### Coverage Reporting

```bash
cd backend/
coverage erase
coverage run -m pytest tests/unit/
coverage report
coverage html                       # HTML report at htmlcov/index.html
```

## Code Quality

### Pre-commit Checks
Before submitting a pull request:
- [ ] All tests pass: `python -m pytest`
- [ ] Code is formatted: `ruff format .`
- [ ] No linting issues: `ruff check .`
- [ ] Coverage is maintained or improved

## Writing Tests

### Test Organization
```
backend/tests/
├── unit/           # Fast, isolated unit tests
├── integration/    # Tests with multiple components
└── e2e/           # End-to-end workflow tests
```

### Test Best Practices
- Use descriptive test names
- Add descriptive failure messages to assertions
- Use fixtures for reusable test data
- Test edge cases including error conditions
- Keep tests independent

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes following the guidelines above
3. Add or update tests for your changes
4. Run the full test suite from the backend directory
5. Submit a pull request with clear description of changes
