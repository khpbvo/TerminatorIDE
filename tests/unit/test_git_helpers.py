import pytest
from pathlib import Path
from terminatoride.utils.git_helpers import (
    is_git_repo, get_git_status, git_init, git_add, git_commit
)

class TestGitHelpers:
    
    def test_is_git_repo(self, mock_git_repo, tmp_path):
        """Test checking if a path is a git repository."""
        # Test with a valid git repo
        assert is_git_repo(mock_git_repo) is True
        
        # Test with a non-git directory
        non_git_dir = tmp_path / "not_git"
        non_git_dir.mkdir()
        assert is_git_repo(non_git_dir) is False
    
    def test_get_git_status(self, mock_git_repo):
        """Test getting git status."""
        # Get status of the mock repo
        status = get_git_status(mock_git_repo)
        
        # Verify the status
        assert status.is_repo is True
        assert status.current_branch is not None
        
        # Create a new file to check for untracked files
        new_file = mock_git_repo / "untracked.txt"
        new_file.write_text("Untracked content")
        
        # Get updated status
        updated_status = get_git_status(mock_git_repo)
        
        # Check for untracked file
        assert len(updated_status.untracked) > 0
        assert "untracked.txt" in updated_status.untracked
    
    def test_git_operations(self, tmp_path):
        """Test git init, add, and commit operations."""
        # Create a test directory
        test_dir = tmp_path / "git_test"
        test_dir.mkdir()
        
        # Create a test file
        test_file = test_dir / "test.txt"
        test_file.write_text("Test content")
        
        # Initialize git
        assert git_init(test_dir) is True
        
        # Add the file
        assert git_add(test_dir, ["test.txt"]) is True
        
        # Commit the changes
        assert git_commit(test_dir, "Test commit") is True
        
        # Verify repo status
        status = get_git_status(test_dir)
        assert status.is_repo is True
        assert len(status.changes) == 0  # All changes should be committed
