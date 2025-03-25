#!/bin/bash

# Create test directory structure
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/fixtures
mkdir -p tests/conftest

# Create initial test files
touch tests/conftest.py
touch tests/unit/test_config.py
touch tests/unit/test_git_helpers.py
touch tests/integration/test_app_startup.py
touch tests/integration/test_panels.py
touch tests/.coveragerc

echo "Testing directory structure created successfully!"
chmod +x setup_tests.sh
