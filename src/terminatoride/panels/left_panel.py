"""Left panel component for TerminatorIDE."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widget import Widget
from textual.widgets import Button, Static

from ..components.file_explorer import FileExplorer
from ..utils.logging import setup_logger

# Set up logger
logger = setup_logger("left_panel", "left_panel.log")


class LeftPanel(Widget):
    """The left panel of the IDE containing file explorer, git integration, and SSH."""

    BINDINGS = [
        Binding("tab", "next_tab", "Next Tab"),
        Binding("shift+tab", "prev_tab", "Previous Tab"),
    ]

    # Re-export FileSelected message
    FileSelected = FileExplorer.FileSelected

    def __init__(self, *args, **kwargs):
        """Initialize the left panel."""
        super().__init__(*args, **kwargs)
        self.current_tab = "files"
        logger.info("LeftPanel initialized")

    def compose(self) -> ComposeResult:
        """Compose the left panel widget."""
        logger.info("Composing LeftPanel")

        # Tab buttons
        with Horizontal(id="tab-buttons"):
            yield Button("Files", id="files-tab-btn", variant="primary")
            yield Button("Git", id="git-tab-btn", variant="default")
            yield Button("SSH", id="ssh-tab-btn", variant="default")

        # Content area for the selected tab
        with Container(id="tab-content"):
            # File Explorer (initially visible)
            yield FileExplorer(id="file-explorer", classes="tab-panel")

            # Git Integration (initially hidden)
            yield Static(
                "Git integration coming soon...",
                id="git-panel",
                classes="tab-panel hidden",
            )

            # SSH Remote Editing (initially hidden)
            yield Static(
                "SSH remote editing coming soon...",
                id="ssh-panel",
                classes="tab-panel hidden",
            )

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        logger.info("LeftPanel mounted")

        # Connect tab button handlers
        self.query_one("#files-tab-btn").on_click = self._show_files_tab
        self.query_one("#git-tab-btn").on_click = self._show_git_tab
        self.query_one("#ssh-tab-btn").on_click = self._show_ssh_tab

        # Set initial focus to the file explorer
        self.query_one("#file-explorer").focus()

    def _show_files_tab(self) -> None:
        """Show the files tab."""
        logger.debug("Show files tab called")
        self._set_active_tab("files")

    def _show_git_tab(self) -> None:
        """Show the git tab."""
        logger.debug("Show git tab called")
        self._set_active_tab("git")

    def _show_ssh_tab(self) -> None:
        """Show the ssh tab."""
        logger.debug("Show SSH tab called")
        self._set_active_tab("ssh")

    def _set_active_tab(self, tab_id: str) -> None:
        """Set the active tab."""
        logger.info(f"Switching to tab: {tab_id}")

        # Update button styles
        self.query_one("#files-tab-btn").variant = (
            "primary" if tab_id == "files" else "default"
        )
        self.query_one("#git-tab-btn").variant = (
            "primary" if tab_id == "git" else "default"
        )
        self.query_one("#ssh-tab-btn").variant = (
            "primary" if tab_id == "ssh" else "default"
        )

        # Update panel visibility using classes
        for panel_id in ["file-explorer", "git-panel", "ssh-panel"]:
            panel = self.query_one(f"#{panel_id}")
            if (
                f"{tab_id}-tab-btn".replace("files-tab-btn", "file-explorer")
                == panel_id
            ):
                panel.remove_class("hidden")
            else:
                panel.add_class("hidden")

        # Set focus to the active panel if it's the file explorer
        if tab_id == "files":
            self.query_one("#file-explorer").focus()

        # Update current tab
        self.current_tab = tab_id

    def on_file_explorer_file_selected(self, event: FileExplorer.FileSelected) -> None:
        """Handle file selection events from the file explorer."""
        logger.info(f"LeftPanel received file selection: {event.path}")
        # Store locally, don't re-post (to avoid infinite loops)
        self.current_file = event.path
