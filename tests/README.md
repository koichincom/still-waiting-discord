
# Still Waiting Discord - Test Suite

This folder contains all tests for the project. All tests are run with `pytest` and `uv`.

## Structure

- One test file per source file in `src/`
- Shared fixtures in `conftest.py`
- Test configuration in `pytest.ini`

## How to Run

Install dependencies (from project root):
    uv sync --dev

Run all tests:
    uv run pytest tests/ -v

Run a specific test file:
    uv run pytest tests/test_db.py -v

Run a specific test function:
    uv run pytest tests/test_db.py::TestFirestoreReminderCollection::test_save_message -v

Use `run_tests.py` or `test.sh` for convenience.

## Test Types

- Unit tests: test_config.py, test_db.py, test_handle_input.py, test_reminder.py, test_main.py
- Integration tests: test_integration.py

## Mocking

- Discord API and Firestore are fully mocked
- No real API calls or database writes

## Coverage

To generate a coverage report:
    uv run pytest tests/ --cov=src --cov-report=term

## Best Practices

- Each test is focused and atomic
- Use fixtures for common setup
- Mock all external dependencies

For more, see the main README.md in the project root.
