"""Left panel for TerminatorIDE with file browser, git integration, and terminal."""

import os

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import DirectoryTree, Label, Static, TabbedContent, TabPane


class LeftPanel(Container):
    """The left panel of the IDE containing file browser, git info, and terminal."""

    DEFAULT_CSS = """
    LeftPanel {
        width: 25%;  /* Change from 100% to 25% */
        height: 100%;
        background: #252526;
        color: #cccccc;
    }

    #panel-title {
        background: #007acc;
        color: #ffffff;
        text-align: center;
        padding: 1 0;
        height: auto;
    }

    TabbedContent {
        width: 100%;
        height: 1fr;
    }

    DirectoryTree {
        width: 100%;
        height: 1fr;  /* Change from 100% to 1fr */
    }

    #git-info {
        width: 100%;
        padding: 1;
        height: auto;
        background: #303030;
        border-top: solid #3f3f3f;
    }

    #branch-info {
        color: #e5c07b;
    }

    #status-info {
        color: #98c379;
    }

    #terminal-container {
        width: 100%;
        height: 100%;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.directory_path = os.path.expanduser("~")

    def compose(self) -> ComposeResult:
        """Compose the left panel widget."""
        with Vertical():
            yield Label("TerminatorIDE", id="panel-title")

            with TabbedContent():
                with TabPane("Files", id="files-tab"):
                    # Fix: Actually yield the DirectoryTree widget
                    yield DirectoryTree(self.directory_path, id="directory-tree")

                with TabPane("Git", id="git-tab"):
                    yield Static("Git integration will appear here", id="git-info")
                    yield Label("Branch: main", id="branch-info")
                    yield Label("Status: Clean", id="status-info")

                with TabPane("Terminal", id="terminal-tab"):
                    yield Static(
                        "Terminal access will appear here", id="terminal-container"
                    )

    def on_mount(self) -> None:
        """Handle panel mount."""
        print("\n----- DEBUGGING LEFT PANEL -----")
        print("LeftPanel mounting...")

        try:
            # Check TabbedContent initialization
            tabs = self.query_one(TabbedContent)
            print(f"Found tabs: {tabs}")
            print(f"Tab IDs: {[tab.id for tab in tabs.query(TabPane)]}")
            print(f"Initial active tab: {tabs.active}")

            # Force tab activation with a slight delay
            async def activate_tab():
                import asyncio

                await asyncio.sleep(0.5)
                tabs.active = "files-tab"
                print(f"After delay, active tab: {tabs.active}")

            self.app.run_worker(activate_tab())

            # Rest of your code...
        except Exception as e:
            print(f"Error initializing tabs: {e}")
            import traceback

            print(traceback.format_exc())

        try:
            tree = self.query_one(DirectoryTree)
            print(f"DirectoryTree representation: {tree!r}")
            print(f"DirectoryTree path: {tree.path}")
            print(f"DirectoryTree visible: {tree.styles.visibility}")
            print(f"DirectoryTree display: {tree.styles.display}")

            # Force visibility
            tree.styles.visibility = "visible"
            tree.styles.display = "block"
        except Exception as e:
            print(f"Error checking DirectoryTree: {e}")

        print("----- END DEBUGGING LEFT PANEL -----\n")

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Handle file selection in the directory tree."""
        # Forward the event to the editor panel
        editor_panel = self.app.query_one("#editor-panel")
        if hasattr(editor_panel, "on_file_selected"):
            editor_panel.on_file_selected(event)
        else:
            self.app.notify(
                "Editor panel doesn't support file selection", severity="warning"
            )

    def change_directory(self, path: str) -> None:
        """Change the current directory in the file browser."""
        directory_tree = self.query_one(DirectoryTree)
        try:
            real_path = os.path.abspath(os.path.expanduser(path))
            if os.path.isdir(real_path):
                directory_tree.path = real_path
                # Refresh the tree
                directory_tree.reload()
            else:
                self.app.notify(f"Not a valid directory: {path}", severity="error")
        except Exception as e:
            self.app.notify(f"Error changing directory: {str(e)}", severity="error")

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        """Handle tab activation."""
        print(f"Tab activated: {event.tab.id}")

        if event.tab.id == "files-tab":
            # Make sure DirectoryTree is visible
            directory_tree = self.query_one(DirectoryTree)
            directory_tree.styles.visibility = "visible"
            directory_tree.styles.display = "block"

            # Reload in case it wasn't loaded
            try:
                directory_tree.reload()
            except Exception as e:
                print(f"Error reloading DirectoryTree: {e}")
