"""Editor panel for TerminatorIDE."""

from pathlib import Path

from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Button, Label, Static


class EditorPanel(Container):
    """The middle panel of the IDE containing the code editor with syntax highlighting."""

    class FileChanged(Message):
        """Message sent when the file content is changed."""

        def __init__(self, path: str, content: str) -> None:
            self.path = path
            self.content = content
            super().__init__()

    # Reactive attributes for tracking state
    current_path = reactive("")
    current_content = reactive("")
    language = reactive("")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_line_numbers = True
        self.current_file = None
        self.diff_view_active = False
        self._original_content = ""

    def compose(self) -> ComposeResult:
        """Compose the editor panel widget."""
        yield Label("Editor", id="editor-title")

        # Container for editor actions/buttons
        with Container(id="editor-actions"):
            yield Static("", id="file-path-display")
            with Container(id="editor-buttons"):
                yield Button("Accept Changes", id="accept-btn", variant="success")
                yield Button("Toggle Diff", id="diff-btn", variant="primary")
                yield Button("Save", id="save-btn", variant="primary")

        # Main editor area with syntax highlighting
        with ScrollableContainer(id="editor-content-container"):
            yield Static("No file opened", id="editor-content")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id

        if button_id == "accept-btn":
            self.accept_changes()
        elif button_id == "diff-btn":
            self.toggle_diff_view()
        elif button_id == "save-btn":
            self.save_file()

    def save_file(self) -> None:
        """Save the current file."""
        if not self.current_path:
            self.app.notify("No file to save", severity="warning")
            return

        try:
            path = Path(self.current_path)
            path.write_text(self.current_content, encoding="utf-8")
            self.app.notify(f"Saved {path.name}", severity="information")

            # Update original content to match current
            self._original_content = self.current_content
            self.diff_view_active = False
            self.update_display()
        except Exception as e:
            self.app.notify(f"Error saving file: {str(e)}", severity="error")

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        # Initialize empty editor
        self.update_display()

    def update_display(self) -> None:
        """Update the editor display with current content."""
        content_widget = self.query_one("#editor-content", Static)
        path_display = self.query_one("#file-path-display", Static)

        if not self.current_path:
            content_widget.update("No file opened")
            path_display.update("")
            return

        path_display.update(f"📄 {self.current_path}")

        # Determine language for syntax highlighting
        if not self.language:
            self.language = self._detect_language(self.current_path)

        # If in diff view, show the diff
        if self.diff_view_active:
            diff_content = self._generate_diff(
                self._original_content, self.current_content
            )
            # Use syntax highlighting for the diff
            content_widget.update(
                Syntax(diff_content, "diff", line_numbers=self.show_line_numbers)
            )
        else:
            # Regular syntax highlighting view
            content_widget.update(
                Syntax(
                    self.current_content,
                    self.language,
                    line_numbers=self.show_line_numbers,
                    word_wrap=True,
                )
            )

    def open_file(self, path: str, content: str) -> None:
        """Open a file in the editor."""
        self.current_path = path
        self.current_content = content
        self._original_content = content
        self.language = self._detect_language(path)
        self.diff_view_active = False
        self.update_display()

    def update_content(self, content: str, show_diff: bool = False) -> None:
        """Update the content in the editor, optionally showing a diff."""
        if not self.current_path:
            return

        if show_diff:
            self.diff_view_active = True
            self.current_content = content
        else:
            self.diff_view_active = False
            self.current_content = content
            self._original_content = content

        self.update_display()

        # Send a message that the file has changed
        self.post_message(self.FileChanged(self.current_path, content))

    def toggle_diff_view(self) -> None:
        """Toggle between diff view and normal view."""
        self.diff_view_active = not self.diff_view_active
        self.update_display()

    def accept_changes(self) -> None:
        """Accept the current changes, making them the new baseline."""
        if self.diff_view_active:
            self._original_content = self.current_content
            self.diff_view_active = False
            self.update_display()

    def _detect_language(self, path: str) -> str:
        """Detect the language based on file extension."""
        ext = Path(path).suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".md": "markdown",
            ".txt": "text",
            ".sh": "bash",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "cpp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".sql": "sql",
        }
        return language_map.get(ext, "text")

    def _generate_diff(self, original: str, modified: str) -> str:
        """Generate a diff between original and modified content."""
        import difflib

        # Generate unified diff
        diff_lines = list(
            difflib.unified_diff(
                original.splitlines(),
                modified.splitlines(),
                fromfile="Original",
                tofile="Modified",
                lineterm="",
            )
        )

        return "\n".join(diff_lines)
