"""Custom folder selection dialog for TerminatorIDE."""

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from ..utils.logging import setup_logger

# Set up logger
logger = setup_logger("folder_dialog", "folder_dialog.log")


class FolderDialog(ModalScreen):
    """A simplified dialog for folder selection."""

    BINDINGS = []

    def __init__(self):
        """Initialize the dialog with default path."""
        super().__init__()
        self.path = str(Path.home())
        self.result = None
        logger.info("FolderDialog initialized")

    def compose(self) -> ComposeResult:
        """Compose the dialog."""
        with Center():
            with Vertical(id="dialog-container", classes="folder-dialog"):
                yield Label("Select Folder", id="dialog-title")
                yield Static("Enter folder path:", id="dialog-message")
                yield Input(value=self.path, id="folder-path-input")

                with Vertical(id="button-container"):
                    yield Button("Open", id="open-btn", variant="primary")
                    yield Button("Cancel", id="cancel-btn", variant="default")

    def on_mount(self) -> None:
        """Handle dialog mount."""
        logger.info("FolderDialog mounted")
        # Connect button handlers
        self.query_one("#open-btn").on_click = self._on_open
        self.query_one("#cancel-btn").on_click = self._on_cancel
        # Focus the input
        self.query_one("#folder-path-input").focus()

    async def _on_open(self) -> None:
        """Handle Open button click."""
        path = self.query_one("#folder-path-input").value
        logger.info(f"Open button clicked with path: {path}")
        # Store the result directly on the instance
        self.result = path
        # Close the screen
        self.app.pop_screen()

    def _on_cancel(self) -> None:
        """Handle Cancel button click."""
        logger.info("Cancel button clicked")
        # Set result to None
        self.result = None
        # Close the screen
        self.app.pop_screen()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in the input field."""
        path = self.query_one("#folder-path-input").value
        logger.info(f"Input submitted with path: {path}")
        # Store the result
        self.result = path
        # Close the screen
        self.app.pop_screen()
