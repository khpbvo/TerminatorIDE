.PHONY: test test-unit test-integration test-coverage lint format check pre-commit clean

# Run all tests
test:
	PYTHONPATH=.:src python -m pytest

# Run unit tests only
test-unit:
	PYTHONPATH=.:src python -m pytest tests/unit

# Run integration tests only
test-integration:
	PYTHONPATH=.:src python -m pytest tests/integration

# Run tests with coverage report
test-coverage:
	PYTHONPATH=.:src python -m pytest --cov=src/terminatoride --cov-report=term --cov-report=html
	open htmlcov/index.html

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

# Run pre-commit hooks on all files
pre-commit:
	pre-commit run --all-files

# Clean up temporary files
clean:
	rm -rf .pytest_cache htmlcov .coverage coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
