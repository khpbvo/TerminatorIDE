"""File Explorer component for TerminatorIDE."""

import os
from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Input, Label, Tree

from .file_operations import FileOperations
from .modal import ConfirmDialog, InputDialog


class FileExplorer(Widget):
    """A file explorer widget that displays and manages files and directories."""

    # Define key bindings with explicit key combinations
    BINDINGS = [
        Binding("f", "focus_search", "Search"),
        Binding("n", "new_file", "New File"),
        Binding("d", "new_dir", "New Directory"),
        Binding("r", "rename", "Rename"),
        Binding("delete", "delete", "Delete"),
        Binding("ctrl+r", "refresh", "Refresh"),
    ]

    class FileSelected(Message):
        """Message sent when a file is selected."""

        def __init__(self, path: Path) -> None:
            self.path = path
            super().__init__()

    def __init__(self, path: str = ".", *args, **kwargs):
        """Initialize the file explorer.

        Args:
            path: The directory path to explore.
        """
        super().__init__(*args, **kwargs)

        # Make sure the path is absolute for reliable file browsing
        self.path = Path(os.path.expanduser(path)).absolute()
        self.current_selection = None

        # For debugging
        print(f"File Explorer initialized with path: {self.path}")
        if not self.path.exists():
            print(f"WARNING: Path {self.path} does not exist!")
        elif not self.path.is_dir():
            print(f"WARNING: Path {self.path} is not a directory!")

    def compose(self) -> ComposeResult:
        """Compose the file explorer widget."""
        # Header with path display
        yield Label(f"📁 {self.path}", id="file-explorer-title")

        # Search input
        yield Input(placeholder="Search files...", id="file-search")

        # Button bar for file operations
        with Horizontal(id="button-bar"):
            yield Button("New File", id="new-file-btn", variant="primary")
            yield Button("New Dir", id="new-dir-btn", variant="primary")
            yield Button("Rename", id="rename-btn", variant="primary")
            yield Button("Delete", id="delete-btn", variant="error")
            yield Button("Refresh", id="refresh-btn", variant="default")

        # Directory tree - use a simple Tree widget instead of DirectoryTree for better control
        with VerticalScroll(id="file-tree-container"):
            yield Tree("Root", id="file-tree")

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        # Hide the search input initially
        self.query_one("#file-search").display = False

        # Get the tree and set it up
        tree = self.query_one(Tree)
        tree.root.label = self.path.name or str(self.path)
        tree.root.data = str(self.path)

        # Connect button handlers with direct binding
        new_file_btn = self.query_one("#new-file-btn")
        new_file_btn.on_click = self._on_new_file_click

        new_dir_btn = self.query_one("#new-dir-btn")
        new_dir_btn.on_click = self._on_new_dir_click

        rename_btn = self.query_one("#rename-btn")
        rename_btn.on_click = self._on_rename_click

        delete_btn = self.query_one("#delete-btn")
        delete_btn.on_click = self._on_delete_click

        refresh_btn = self.query_one("#refresh-btn")
        refresh_btn.on_click = self._on_refresh_click

        # Populate the tree
        self._populate_tree()

        # Focus the tree
        tree.focus()

        print("FileExplorer mounted and initialized")

    # Button click handlers with proper async handling
    async def _on_new_file_click(self) -> None:
        """Handle new file button click."""
        print("New file button clicked")
        await self.action_new_file()

    async def _on_new_dir_click(self) -> None:
        """Handle new directory button click."""
        print("New directory button clicked")
        await self.action_new_dir()

    async def _on_rename_click(self) -> None:
        """Handle rename button click."""
        print("Rename button clicked")
        await self.action_rename()

    async def _on_delete_click(self) -> None:
        """Handle delete button click."""
        print("Delete button clicked")
        await self.action_delete()

    def _on_refresh_click(self) -> None:
        """Handle refresh button click."""
        print("Refresh button clicked")
        self.action_refresh()

    def _populate_tree(self) -> None:
        """Populate the file tree with the contents of the current directory."""
        tree = self.query_one(Tree)
        tree.root.remove_children()

        try:
            # Special parent directory node to enable navigation up
            if self.path != Path("/"):
                parent_node = tree.root.add(
                    ".. (Parent Directory)", data=str(self.path.parent)
                )
                parent_node.expand()

            # List directories first, then files, alphabetically
            dirs = []
            files = []

            for item in sorted(self.path.iterdir(), key=lambda p: p.name.lower()):
                try:
                    if item.is_dir():
                        dirs.append(item)
                    else:
                        files.append(item)
                except (PermissionError, OSError) as e:
                    print(f"Error accessing {item}: {e}")

            # Add directories
            for directory in dirs:
                node = tree.root.add(f"📁 {directory.name}", data=str(directory))
                # Add a placeholder child to show the expand button
                if any(True for _ in directory.iterdir()):
                    node.add("⏳ Loading...")

            # Add files
            for file in files:
                # Choose icon based on file type
                icon = self._get_file_icon(file)
                tree.root.add(f"{icon} {file.name}", data=str(file))

            # Expand the root by default
            tree.root.expand()

            # Update the title to show current path
            self.query_one("#file-explorer-title").update(f"📁 {self.path}")

        except (PermissionError, OSError) as e:
            print(f"Error populating tree: {e}")
            self.notify(f"Error accessing directory: {str(e)}", severity="error")

    def _get_file_icon(self, file_path: Path) -> str:
        """Get an appropriate icon for a file based on its extension.

        Args:
            file_path: The file path.

        Returns:
            A string with an appropriate icon.
        """
        ext = file_path.suffix.lower()

        if ext in [".py", ".pyw"]:
            return "🐍"  # Python
        elif ext in [".js", ".jsx", ".ts", ".tsx"]:
            return "📜"  # JavaScript/TypeScript
        elif ext in [".html", ".htm", ".xhtml"]:
            return "🌐"  # HTML
        elif ext in [".css", ".scss", ".sass", ".less"]:
            return "🎨"  # CSS
        elif ext in [".json", ".yaml", ".yml", ".toml", ".xml"]:
            return "📄"  # Data files
        elif ext in [".md", ".txt", ".rst"]:
            return "📝"  # Text/Markdown
        elif ext in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"]:
            return "🖼️"  # Images
        elif ext in [".mp3", ".wav", ".ogg", ".flac"]:
            return "🎵"  # Audio
        elif ext in [".mp4", ".avi", ".mov", ".mkv"]:
            return "🎬"  # Video
        elif ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"]:
            return "📑"  # Documents
        elif ext in [".zip", ".rar", ".tar", ".gz", ".7z"]:
            return "📦"  # Archives
        else:
            return "📄"  # Default file icon

    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        """Handle tree node expansion."""
        # Only load contents if this is not the root node
        if event.node is not self.query_one(Tree).root:
            # Remove the placeholder child
            event.node.remove_children()

            # Get the directory path
            path = Path(event.node.data)
            if path.is_dir():
                try:
                    # List directories first, then files, alphabetically
                    dirs = []
                    files = []

                    for item in sorted(path.iterdir(), key=lambda p: p.name.lower()):
                        try:
                            if item.is_dir():
                                dirs.append(item)
                            else:
                                files.append(item)
                        except (PermissionError, OSError) as e:
                            print(f"Error accessing {item}: {e}")

                    # Add directories
                    for directory in dirs:
                        node = event.node.add(
                            f"📁 {directory.name}", data=str(directory)
                        )
                        # Add a placeholder child to show the expand button
                        if any(True for _ in directory.iterdir()):
                            node.add("⏳ Loading...")

                    # Add files
                    for file in files:
                        # Choose icon based on file type
                        icon = self._get_file_icon(file)
                        event.node.add(f"{icon} {file.name}", data=str(file))

                except (PermissionError, OSError) as e:
                    print(f"Error populating tree: {e}")
                    self.notify(
                        f"Error accessing directory: {str(e)}", severity="error"
                    )

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection."""
        if event.node.data:
            path = Path(event.node.data)
            self.current_selection = path
            self.post_message(self.FileSelected(path))

            # If it's a directory and we double-click, navigate to it
            if path.is_dir() and event.node.label.startswith(("📁", "..")):
                # Check if this is a double click (can only approximate it with selection)
                self.path = path
                self._populate_tree()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submitted events."""
        if event.input.id == "file-search":
            self.search_files(event.value)

    def search_files(self, query: str) -> None:
        """Search for files matching the query.

        Args:
            query: The search query.
        """
        if not query:
            return

        tree = self.query_one(Tree)

        # Clear selection
        self.current_selection = None

        # Reset tree
        tree.reset()

        # Use os.walk for a fast recursive search
        matches = []

        try:
            for root, dirs, files in os.walk(str(self.path)):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith(".")]

                # Check directory names
                for dir_name in dirs:
                    if query.lower() in dir_name.lower():
                        matches.append(Path(root) / dir_name)

                # Check file names
                for file_name in files:
                    if query.lower() in file_name.lower():
                        matches.append(Path(root) / file_name)

            # Display search results
            if matches:
                # Recreate tree with just matches
                tree.root.remove_children()
                tree.root.label = f"Search: {query}"

                # Add paths to tree
                for path in sorted(matches, key=lambda p: str(p).lower()):
                    rel_path = path.relative_to(self.path)
                    parts = list(rel_path.parts)

                    # Build the path in the tree
                    current = tree.root
                    for i, part in enumerate(parts):
                        # Check if this part already exists as a child
                        child = next(
                            (c for c in current.children if c.label == part), None
                        )

                        if child is None:
                            # Create the node
                            if i == len(parts) - 1:  # Last part (file/dir name)
                                child = current.add(part, data=str(path))
                            else:
                                child = current.add(
                                    part, data=str(self.path.joinpath(*parts[: i + 1]))
                                )

                        current = child

                # Expand all nodes
                for node in tree.walk_nodes():
                    if node.children:
                        node.expand()

                self.notify(
                    f"Found {len(matches)} matches for '{query}'",
                    severity="information",
                )
            else:
                self.notify(f"No matches found for '{query}'", severity="warning")

        except Exception as e:
            self.notify(f"Error during search: {str(e)}", severity="error")

        # Hide search input after search
        self.query_one("#file-search").display = False
        tree.focus()

    def action_focus_search(self) -> None:
        """Focus the search input."""
        search = self.query_one("#file-search")
        search.display = True
        search.focus()

    def action_refresh(self) -> None:
        """Refresh the file tree."""
        self._populate_tree()
        self.notify("File tree refreshed", severity="information")

    async def action_new_file(self) -> None:
        """Create a new file."""
        # Determine parent directory based on current selection
        parent_dir = self._get_parent_directory()

        # Show input dialog for filename
        filename = await self.app.push_screen(
            InputDialog("New File", "Enter filename:", "")
        )

        if filename:
            # Create the file
            path = parent_dir / filename
            success, message = FileOperations.create_file(path)

            # Show notification
            severity = "information" if success else "error"
            self.notify(message, severity=severity)

            # Refresh tree if successful
            if success:
                self.action_refresh()

    async def action_new_dir(self) -> None:
        """Create a new directory."""
        # Determine parent directory based on current selection
        parent_dir = self._get_parent_directory()

        # Show input dialog for directory name
        dirname = await self.app.push_screen(
            InputDialog("New Directory", "Enter directory name:", "")
        )

        if dirname:
            # Create the directory
            path = parent_dir / dirname
            success, message = FileOperations.create_directory(path)

            # Show notification
            severity = "information" if success else "error"
            self.notify(message, severity=severity)

            # Refresh tree if successful
            if success:
                self.action_refresh()

    async def action_rename(self) -> None:
        """Rename the selected file or directory."""
        if not self.current_selection:
            self.notify("No file selected", severity="error")
            return

        # Show input dialog for new name
        new_name = await self.app.push_screen(
            InputDialog(
                "Rename",
                f"Rename {self.current_selection.name} to:",
                self.current_selection.name,
            )
        )

        if new_name and new_name != self.current_selection.name:
            # Create the new path
            new_path = self.current_selection.parent / new_name

            # Rename the file or directory
            success, message = FileOperations.rename(self.current_selection, new_path)

            # Show notification
            severity = "information" if success else "error"
            self.notify(message, severity=severity)

            # Update current selection and refresh tree if successful
            if success:
                self.current_selection = new_path
                self.action_refresh()

    async def action_delete(self) -> None:
        """Delete the selected file or directory."""
        if not self.current_selection:
            self.notify("No file selected", severity="error")
            return

        # Show confirmation dialog
        confirmed = await self.app.push_screen(
            ConfirmDialog(
                "Confirm Delete",
                f"Are you sure you want to delete {self.current_selection.name}?",
            )
        )

        if confirmed:
            # Delete the file or directory
            success, message = FileOperations.delete(self.current_selection)

            # Show notification
            severity = "information" if success else "error"
            self.notify(message, severity=severity)

            # Clear current selection and refresh tree if successful
            if success:
                self.current_selection = None
                self.action_refresh()

    def _get_parent_directory(self) -> Path:
        """Get the parent directory for new file/directory operations.

        Returns:
            The parent directory path.
        """
        if not self.current_selection:
            return self.path

        if self.current_selection.is_dir():
            return self.current_selection

        return self.current_selection.parent

    def notify(self, message: str, severity: str = "information") -> None:
        """Show a notification.

        Args:
            message: The message to display.
            severity: The severity level (information, warning, error).
        """
        # This will be connected to the app's notification system
        level_map = {"information": "info", "warning": "warning", "error": "error"}
        level = level_map.get(severity, "info")
        self.app.show_notification(message, level=level)
