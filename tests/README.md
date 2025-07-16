
# Still Waiting Discord - Test Suite

All tests are run with `pytest` and `uv`.


## How to Run

Install dependencies:
```sh
uv sync --dev
# or, if you use pip:
pip install -r requirements.txt
```

Run all tests:
```sh
uv run pytest tests/ -v
# or, if you use pip:
pytest tests/ -v
```

Run a specific test:
```sh
uv run pytest tests/test_db.py -v
# or, if you use pip:
pytest tests/test_db.py -v
```

Coverage report:
```sh
uv run pytest tests/ --cov=src --cov-report=term
# or, if you use pip:
pytest tests/ --cov=src --cov-report=term
```

## Notes

- Unit tests: `test_config.py`, `test_db.py`, `test_handle_input.py`, `test_reminder.py`, `test_main.py`
- Integration tests: `test_integration.py`
- Mocks: Discord API and Firestore (no real API/database calls)
- Fixtures: `conftest.py`
- Test runner: `run_tests.py`

See the main README.md for more details.
