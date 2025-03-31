"""File Explorer component for TerminatorIDE."""

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, DirectoryTree, Label, Static

from ..utils.logging import setup_logger

# Set up logger
logger = setup_logger("file_explorer", "file_explorer.log")


class FileExplorer(Widget):
    """Simple file explorer widget using DirectoryTree."""

    BINDINGS = [
        Binding("ctrl+o", "open_home", "Open Home"),
        Binding("ctrl+r", "refresh", "Refresh"),
    ]

    # Re-export messages
    class FileSelected(Message):
        """Message sent when a file is selected."""

        def __init__(self, path: Path) -> None:
            self.path = path
            super().__init__()

    def __init__(self, *args, **kwargs):
        """Initialize the file explorer."""
        super().__init__(*args, **kwargs)
        self.current_path = None
        logger.info("FileExplorer initialized")

    def compose(self) -> ComposeResult:
        """Compose the file explorer widget."""
        logger.info("Composing FileExplorer")

        # Container for the whole explorer
        with Vertical(id="explorer-main"):
            # Header
            yield Label("File Explorer", id="explorer-header")

            # Button bar
            with Horizontal(id="explorer-buttons"):
                yield Button("Home", id="home-btn", variant="primary")
                yield Button("Refresh", id="refresh-btn", variant="default")

            # Content area - either directory tree or welcome message
            with Vertical(id="explorer-content"):
                # Welcome message (initially visible)
                yield Static(
                    "Click 'Home' to open your home directory", id="welcome-msg"
                )

                # Directory tree will be mounted dynamically

    def on_mount(self) -> None:
        """Handle mount event."""
        logger.info("FileExplorer mounted")
        # Connect button handlers
        self.query_one("#home-btn").on_click = self._on_home_click
        self.query_one("#refresh-btn").on_click = self._on_refresh_click

    def _on_home_click(self) -> None:
        """Handle home button click."""
        logger.info("Home button clicked")
        self._open_directory(Path.home())

    def _on_refresh_click(self) -> None:
        """Handle refresh button click."""
        logger.info("Refresh button clicked")
        if self.current_path:
            self._open_directory(self.current_path)

    def _open_directory(self, path: Path) -> None:
        """Open a directory in the explorer."""
        logger.info(f"Opening directory: {path}")
        try:
            # Update current path
            self.current_path = path

            # Update header
            self.query_one("#explorer-header").update(f"📁 {path}")

            # Hide welcome message
            welcome = self.query_one("#welcome-msg")
            welcome.display = False

            # Remove any existing directory tree
            try:
                existing_tree = self.query("#directory-tree").first()
                if existing_tree:
                    existing_tree.remove()
                    logger.debug("Removed existing directory tree")
            except Exception as e:
                logger.debug(f"No existing tree to remove: {e}")

            # Create new directory tree
            content = self.query_one("#explorer-content")
            tree = DirectoryTree(str(path), id="directory-tree")
            content.mount(tree)
            logger.info("Mounted new directory tree")

            # Refresh UI
            self.refresh()

        except Exception as e:
            logger.error(f"Error opening directory: {e}")
            self.notify(f"Error: {str(e)}", severity="error")

    def on_directory_tree_file_selected(
        self, message: DirectoryTree.FileSelected
    ) -> None:
        """Handle file selection."""
        path = message.path
        logger.info(f"File selected: {path}")
        self.post_message(self.FileSelected(path))

    def on_directory_tree_directory_selected(
        self, message: DirectoryTree.DirectorySelected
    ) -> None:
        """Handle directory selection."""
        path = message.path
        logger.info(f"Directory selected: {path}")
        # DirectoryTree handles this automatically

    def action_open_home(self) -> None:
        """Action to open home directory."""
        self._open_directory(Path.home())

    def action_refresh(self) -> None:
        """Action to refresh the current directory."""
        if self.current_path:
            self._open_directory(self.current_path)
