"""Left panel component for TerminatorIDE."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.events import Key
from textual.widget import Widget
from textual.widgets import Button, Static

from ..components.file_explorer import FileExplorer


class LeftPanel(Widget):
    """The left panel of the IDE containing file explorer, git integration, and SSH."""

    BINDINGS = [
        Binding("tab", "next_tab", "Next Tab"),
        Binding("shift+tab", "prev_tab", "Previous Tab"),
    ]

    # Re-export FileSelected message
    FileSelected = FileExplorer.FileSelected

    def __init__(self, path: str = ".", *args, **kwargs):
        """Initialize the left panel.

        Args:
            path: The directory path to explore.
        """
        super().__init__(*args, **kwargs)
        self.path = path
        self.current_tab = "files"
        self._tab_content = None

    def compose(self) -> ComposeResult:
        """Compose the left panel widget."""
        # Simple tab bar instead of TabbedContent for more control
        with Horizontal(id="tab-buttons"):
            yield Button("Files", id="files-tab-btn", variant="primary")
            yield Button("Git", id="git-tab-btn", variant="default")
            yield Button("SSH", id="ssh-tab-btn", variant="default")

        # Content area for the selected tab
        with Container(id="tab-content"):
            # File Explorer (initially visible)
            yield FileExplorer(
                self.path, id="file-explorer", classes="tab-panel active"
            )

            # Git Integration (initially hidden)
            yield Static(
                "Git integration coming soon...", id="git-panel", classes="tab-panel"
            )

            # SSH Remote Editing (initially hidden)
            yield Static(
                "SSH remote editing coming soon...", id="ssh-panel", classes="tab-panel"
            )

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        # Connect tab button handlers
        self.query_one("#files-tab-btn").on_click = self._show_files_tab
        self.query_one("#git-tab-btn").on_click = self._show_git_tab
        self.query_one("#ssh-tab-btn").on_click = self._show_ssh_tab

        # Hide git and ssh panels initially
        self.query_one("#git-panel").display = False
        self.query_one("#ssh-panel").display = False

        # Set initial focus to the file explorer
        self.query_one("#file-explorer").focus()

        print("LeftPanel mounted")

    def on_key(self, event: Key) -> None:
        """Handle key events directly for debugging."""
        print(f"Key pressed in LeftPanel: {event.key}")

    def _show_files_tab(self) -> None:
        """Show the files tab."""
        self._set_active_tab("files")

    def _show_git_tab(self) -> None:
        """Show the git tab."""
        self._set_active_tab("git")

    def _show_ssh_tab(self) -> None:
        """Show the ssh tab."""
        self._set_active_tab("ssh")

    def _set_active_tab(self, tab_id: str) -> None:
        """Set the active tab.

        Args:
            tab_id: The ID of the tab to activate ("files", "git", or "ssh").
        """
        print(f"Switching to tab: {tab_id}")

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

        # Update panel visibility
        self.query_one("#file-explorer").display = tab_id == "files"
        self.query_one("#git-panel").display = tab_id == "git"
        self.query_one("#ssh-panel").display = tab_id == "ssh"

        # Set focus to the active panel
        if tab_id == "files":
            self.query_one("#file-explorer").focus()

        # Update current tab
        self.current_tab = tab_id

    def on_file_explorer_file_selected(self, event: FileExplorer.FileSelected) -> None:
        """Handle file selection events from the file explorer."""
        # Forward the event to the parent
        self.post_message(event)

    def action_next_tab(self) -> None:
        """Switch to the next tab."""
        tabs = ["files", "git", "ssh"]
        current_index = tabs.index(self.current_tab)
        next_index = (current_index + 1) % len(tabs)
        self._set_active_tab(tabs[next_index])

    def action_prev_tab(self) -> None:
        """Switch to the previous tab."""
        tabs = ["files", "git", "ssh"]
        current_index = tabs.index(self.current_tab)
        prev_index = (current_index - 1) % len(tabs)
        self._set_active_tab(tabs[prev_index])
