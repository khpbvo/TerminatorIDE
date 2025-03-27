import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class GitStatus:
    is_repo: bool
    current_branch: Optional[str] = None
    changes: List[Dict[str, str]] = None
    untracked: List[str] = None


def is_git_repo(path: Path) -> bool:
    """Check if the given path is within a git repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except Exception:
        return False


def get_git_status(path: Path) -> GitStatus:
    """Get the git status for the given path."""
    if not is_git_repo(path):
        return GitStatus(is_repo=False)

    # Get current branch
    try:
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        current_branch = branch_result.stdout.strip()
    except Exception:
        current_branch = None

    # Get status of files
    try:
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        changes = []
        untracked = []

        for line in status_result.stdout.splitlines():
            if not line.strip():
                continue

            status = line[:2]
            file_path = line[3:].strip()

            if status.startswith("??"):
                untracked.append(file_path)
            else:
                changes.append({"file": file_path, "status": status})

        return GitStatus(
            is_repo=True,
            current_branch=current_branch,
            changes=changes,
            untracked=untracked,
        )
    except Exception:
        # Return partial information if we got the branch but status failed
        return GitStatus(
            is_repo=True, current_branch=current_branch, changes=[], untracked=[]
        )


def git_init(path: Path) -> bool:
    """Initialize a git repository at the given path."""
    try:
        subprocess.run(
            ["git", "init"],
            cwd=path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except Exception:
        return False


def git_add(path: Path, files: List[str]) -> bool:
    """Add files to git staging area."""
    try:
        subprocess.run(
            ["git", "add", *files],
            cwd=path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except Exception:
        return False


def git_commit(path: Path, message: str) -> bool:
    """Commit staged changes with the given message."""
    try:
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        return True
    except Exception:
        return False
