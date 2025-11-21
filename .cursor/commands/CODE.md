Guidance for writing code that passes this project's compliance checks.

# General Principles

* **DRY** - Don't repeat yourself
* **Functional purity** - Minimize side effects; prefer pure functions that return values rather than mutating state
* **Documentation** - All public functions, classes, and modules must have clear docstrings
* **Testing** - Write tests for new features and bug fixes

# Running Compliance Checks

## Backend
```bash
# Run pre-commit on backend only
pre-commit run --files backend/**/*

# Or run directly via ruff
cd backend && uv run ruff check . --fix
```

## Frontend
```bash
cd frontend && npm run lint
cd frontend && npm run build  # Runs TypeScript checks
```

# Frontend Guidelines

* **TypeScript**: Use strict type checking; avoid `any` types
* **Component structure**: Use functional components with TypeScript interfaces for props
* **Imports**: Group imports (React, Next.js, third-party, local) with blank lines between groups
* **Accessibility**: Follow WCAG 2.1 AA standards (see ACCESSIBILITY.md)
* **Error handling**: Always handle loading and error states in components
* **Testing**: Run `npm test` before committing

# Backend Guidelines

## API Design

### Separation of Concerns: Endpoints vs Business Logic

**Principle**: Endpoints should orchestrate and delegate, not duplicate business logic or error handling.

**Endpoint Responsibilities (routes.py)**:
- Request validation and deserialization
- Authentication/authorization checks
- HTTP-specific concerns (status codes, response formatting)
- Delegating to business logic functions
- Converting business exceptions to HTTP responses

**Business Logic Responsibilities (e.g., llm_calls.py, services/)**:
- Core application logic
- Error handling specific to the operation
- State management (e.g., creating error minute versions)
- Data transformations and processing

## Code Style

* **Linting**: All code must pass `ruff` checks defined in `backend/pyproject.toml`
* **PEP compliance**: Follow PEP 8 (style), PEP 257 (docstrings), PEP 484 (type hints)
* **Docstrings**: Use NumPy style with complete type annotations

Example:
```python
def process_audio(file_path: str, sample_rate: int = 16000) -> dict[str, Any]:
    """
    Process audio file for transcription.
    
    Parameters
    ----------
    file_path : str
        Path to the audio file
    sample_rate : int, default 16000
        Target sample rate in Hz
        
    Returns
    -------
    dict[str, Any]
        Processed audio metadata
        
    Raises
    ------
    FileNotFoundError
        If the audio file doesn't exist
    """
```

## Testing & Imports

* **Test isolation**: System Under Test (SUT) modules should not trigger side effects on import
  - ❌ Bad: Module-level API calls, database connections, file I/O
  - ✅ Good: Initialize resources in functions/methods, use dependency injection

* **No closure arguments**: Avoid passing closures as function arguments in module scope
  ```python
  # ❌ Bad - eager evaluation on import
  DEFAULT_PROCESSOR = lambda x: process_data(x, load_config())
  
  # ✅ Good - deferred evaluation
  def get_default_processor():
      config = load_config()
      return lambda x: process_data(x, config)
  ```

## Lint Exceptions

When using `# noqa` or `# type: ignore`, always add an explanatory comment:
```python
result = unsafe_operation()  # noqa: S603 - subprocess call required for ffmpeg integration
```

## Path Handling

* Use `pathlib.Path` instead of `os.path` (enforced by PTH rules)
* Scripts directory has relaxed rules for CLI convenience

## Running Tests

```bash
cd backend && uv run pytest
cd backend && uv run pytest --cov  # With coverage
```
