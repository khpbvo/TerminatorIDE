.PHONY: test test-unit test-integration test-coverage lint format check

# Run all tests
test:
	python -m pytest

# Run unit tests only
test-unit:
	python -m pytest tests/unit

# Run integration tests only
test-integration:
	python -m pytest tests/integration

# Run tests with coverage report
test-coverage:
	python -m pytest --cov=src/terminatoride --cov-report=term --cov-report=html

# Run linting checks
lint:
	black --check src tests
	isort --check-only src tests
	mypy src

# Format code
format:
	black src tests
	isort src tests

# Run all code quality checks
check: lint test
