# Test Guidance

## Frontend Tests

* Always write tests with vitest.

## Backend Tests

* Always write pytest tests.
* Always include the optional warning message for assert statements to aid
debugging.
* Never ever duplicate src code in test files. Ensure test modules import
business logic.
* Ensure that test module dependencies import without causing side effects.
* Ensure test modules are located in the appropriate location of the existing
directory structure. The test directory is organised to reflect that of the
system under test.
* When running pytest, use `uv run pytest ...` from the backend dir. 
* When mocking, prefer pytest fixtures and utilities over unittests library.
