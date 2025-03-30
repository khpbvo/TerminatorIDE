import os
import site
import sys
from pathlib import Path

import pytest


# Try to fix the import issue early
def pytest_configure(config):
    """Configure pytest and try to fix imports."""
    # Get site-packages directories and add them to path
    site_packages = site.getsitepackages()
    for sp in site_packages:
        if sp not in sys.path:
            sys.path.insert(0, sp)

    # Try to preload the problematic module
    try:
        import importlib

        importlib.import_module("agents")
        print("Successfully pre-loaded agents module")
    except ImportError as e:
        print(f"Failed to pre-load agents module: {e}")


# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))  # Add this line


# Set up test environment variables
@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Set up test environment variables."""
    # Only set a test API key if not already set in environment
    # This allows integration tests to use a real key from .env
    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = "test_api_key"

    os.environ["TERMINATOR_THEME"] = "test"
    os.environ["TERMINATOR_EDITOR"] = "nano"
    os.environ["TERMINATOR_SHOW_LINE_NUMBERS"] = "True"
    os.environ["TERMINATOR_AUTO_SAVE"] = "False"

    # Ensure we're in test mode
    os.environ["TERMINATOR_TEST_MODE"] = "True"

    yield

    # Clean up if needed
    if "TERMINATOR_TEST_MODE" in os.environ:
        del os.environ["TERMINATOR_TEST_MODE"]


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file for testing."""
    config_path = tmp_path / "config.json"
    config_content = """
    {
        "openai": {
            "model": "gpt-3.5-turbo",
            "temperature": 0.5
        },
        "app": {
            "theme": "dark",
            "editor_type": "nano",
            "show_line_numbers": true,
            "auto_save": false
        }
    }
    """
    config_path.write_text(config_content)
    return config_path


@pytest.fixture
def mock_git_repo(tmp_path):
    """Create a mock git repository for testing git functionality."""
    from terminatoride.utils.git_helpers import git_add, git_commit, git_init

    # Set up a temporary git repo
    repo_path = tmp_path / "git_test_repo"
    repo_path.mkdir()

    # Create a test file
    test_file = repo_path / "test.txt"
    test_file.write_text("Test content")

    # Initialize git repo
    git_init(repo_path)
    git_add(repo_path, ["test.txt"])
    git_commit(repo_path, "Initial commit")

    return repo_path
