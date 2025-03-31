"""File Explorer component for TerminatorIDE using Textual DirectoryTree."""

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widget import Widget
from textual.widgets import Button, DirectoryTree, Label

from ..utils.logging import setup_logger

# Set up logger
logger = setup_logger("file_explorer", "file_explorer.log")


class FileExplorer(Widget):
    """File explorer widget using DirectoryTree."""

    BINDINGS = [
        Binding("ctrl+o", "open_home", "Open Home"),
        Binding("ctrl+r", "refresh", "Refresh"),
    ]

    # Re-export messages for compatibility
    FileSelected = DirectoryTree.FileSelected

    def __init__(self, *args, **kwargs):
        """Initialize the file explorer."""
        super().__init__(*args, **kwargs)
        self.current_path = None
        logger.info("FileExplorer initialized")

    def compose(self) -> ComposeResult:
        """Compose the file explorer widget."""
        logger.info("Composing FileExplorer")

        # Ultra-compact header with fixed position
        yield Label("File Explorer", id="explorer-header")

        # Compact button bar with docked position
        with Horizontal(id="explorer-buttons"):
            yield Button("Home", id="home-btn", variant="primary")
            yield Button("Refresh", id="refresh-btn", variant="default")

        # Container for the main directory tree that fills available space
        with Container(id="tree-container"):
            # Default to home directory
            home_path = str(Path.home())
            self.current_path = Path(home_path)
            yield DirectoryTree(home_path, id="directory-tree")

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

            # Update header with short path name to save space
            path_name = path.name or str(path)
            self.query_one("#explorer-header").update(f"📁 {path_name}")

            # Get the tree and reload with new path
            tree = self.query_one(DirectoryTree)
            if str(path) != tree.path:
                # Replace the tree with a new one
                tree.remove()
                tree = DirectoryTree(str(path), id="directory-tree")
                self.query_one("#tree-container").mount(tree)
            else:
                # Just reload the current tree
                tree.reload()

        except Exception as e:
            logger.error(f"Error opening directory: {e}")
            self.notify(f"Error: {str(e)}", severity="error")

    def action_open_home(self) -> None:
        """Action to open home directory."""
        self._open_directory(Path.home())

    def action_refresh(self) -> None:
        """Action to refresh the current directory."""
        if self.current_path:
            self._open_directory(self.current_path)
