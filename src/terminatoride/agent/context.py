"""
Context management for TerminatorIDE agents.
Provides shared context between the IDE and agents.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


@dataclass
class FileContext:
    """Context for a file being edited."""

    path: str
    content: str = ""
    language: str = ""
    cursor_position: int = 0

    @property
    def filename(self) -> str:
        """Get the file name without path."""
        return Path(self.path).name

    @property
    def extension(self) -> str:
        """Get the file extension."""
        return Path(self.path).suffix.lstrip(".")


@dataclass
class ProjectContext:
    """Context for the current project."""

    root_path: str = ""
    git_enabled: bool = False
    current_branch: Optional[str] = None

    def is_initialized(self) -> bool:
        """Check if the project context is initialized."""
        return bool(self.root_path)


@dataclass
class TerminalContext:
    """Context for the terminal."""

    last_command: str = ""
    last_output: str = ""
    current_directory: str = ""


@dataclass
class EditorContext:
    """Context for the editor."""

    last_search: str = ""
    selection: str = ""


class AgentContext(BaseModel):
    """
    Comprehensive context for agents in TerminatorIDE.
    This context is passed to agents during execution.
    """

    user_query: Optional[str] = None
    current_file: Optional[FileContext] = None
    selected_text: Optional[str] = None
    file_content: Optional[str] = None
    cursor_position: Optional[int] = None
    file_path: Optional[str] = None
    file_language: Optional[str] = None

    # This tells Pydantic to allow arbitrary methods/attributes
    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "allow",
    }

    def update_from_dict(self, data: dict):
        """Safely handle potential None values."""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    def update_current_file(
        self, path: str, content: str, cursor_position: int = 0, language: str = ""
    ):
        """Update the current file context.

        Args:
            path: Path to the file
            content: Content of the file
            cursor_position: Current cursor position in the file
            language: Programming language of the file
        """
        self.file_path = path
        self.file_content = content
        self.cursor_position = cursor_position
        self.file_language = language
        self.current_file = FileContext(
            path=path,
            content=content,
            language=language,
            cursor_position=cursor_position,
        )
        return self
