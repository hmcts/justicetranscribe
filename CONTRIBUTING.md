# Contributing to JusticeTranscribe

## Development Workflow

We have two development approaches depending on what you're working on:

### Backend-only Changes

**Use Makefile recipes for faster development:**

**Why:** The Makefile approach uses `npm run dev` which is faster and has more
lenient TypeScript checking, perfect for backend development. It'll also allow
hot reloading for quick iteration on the frontend.

### Frontend Changes (or Full-stack)

**Use Docker Compose for production-like testing:**
```bash
docker compose build    # Build with strict TypeScript compilation
docker compose up       # Run the full stack
```

**Why:** Docker Compose runs `npm run build` which enforces strict TypeScript
compilation and production-ready linting. This catches type errors and
formatting issues that would break CI/CD.

When making changes to the frontend, please check the accessibility of your
amendments with a tool like WAVE. They provide
[Browser Extensions](https://wave.webaim.org/extension/) for testing
accessibility in localhost. This helps our users who rely on screen readers to
navigate the app and ensures we are compliant with Government Digital Service
Standard.

## Testing

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

### Network Request Isolation

PyTest is configured to disable external network calls by default to ensure test isolation. Integration tests automatically enable network access.

```bash
cd backend/
python -m pytest                   # Network calls blocked
python -m pytest --integration     # Network calls enabled for integration tests
python -m pytest --allow-network   # Enable network for specific tests
```

Use `httpx_mock` fixture for mocking HTTP requests in tests.

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

## Testing Onboarding Flow

To test onboarding repeatedly in development:

1. Add to your backend `.env`:
   ```env
   FORCE_ONBOARDING_DEV=true
   ```

2. Restart your backend

3. You'll see a warning banner and onboarding will never be marked "complete"

## Code Quality

### Pre-commit Checks
Before submitting a pull request:
- [ ] All tests pass: `python -m pytest`
- [ ] Code is formatted: `ruff format .`
- [ ] No linting issues: `ruff check .`
- [ ] Coverage is maintained or improved

## Pull Request Process

### Before Submitting a PR

- **Backend-only changes:** Makefile testing is sufficient
- **Frontend changes:** Always run `docker compose build` to ensure it passes strict compilation
- **When in doubt:** Use Docker Compose - it mirrors the CI/CD environment

### After Submitting a PR

1. **Monitor CI/CD workflows** - Check that all automated tests pass
2. **Review Cursor bug bot findings** - Address any exceptions or issues identified in your diff
3. **Fix any pipeline failures** - Resolve build errors, test failures
4. **Only then** Once complete indicate to a colleague that the PR is ready for review

### General Process

1. Create a feature branch from `main`
2. Make your changes following the guidelines above
3. Add or update tests for your changes
4. Run the full test suite from the backend directory
5. Submit a pull request with clear description of changes
