"""
Context management for TerminatorIDE agents.
Provides shared context between the IDE and agents.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

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

    @property
    def app(self) -> Any:
        """Get the app reference."""
        return getattr(self, "_app", None)

    @app.setter
    def app(self, value: Any):
        """Set the app reference."""
        self._app = value

    def get_editor_panel(self):
        """Get the editor panel from the app."""
        if self.app and hasattr(self.app, "query_one"):
            try:
                return self.app.query_one("#editor-panel")
            except Exception:
                return None
        return None

    def apply_code_changes(self, new_content: str, show_diff: bool = True):
        """
        Apply code changes to the current file.

        Args:
            new_content: The new code content
            show_diff: Whether to show a diff before applying changes

        Returns:
            True if changes were applied, False otherwise
        """
        editor_panel = self.get_editor_panel()
        if editor_panel and self.current_file:
            if show_diff:
                editor_panel.show_diff(self.current_file.content, new_content)
            else:
                editor_panel.apply_changes(new_content)
            return True
        return False

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
