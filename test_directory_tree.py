#!/usr/bin/env python
"""Simple test script for DirectoryTree implementation."""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import DirectoryTree, Label


class DirectoryTreeApp(App):
    """A simple app to test the DirectoryTree widget."""

    def compose(self) -> ComposeResult:
        """Create app layout."""
        with Vertical():
            yield Label("Directory Tree Test", id="title")
            yield DirectoryTree(str(Path.home()), id="tree")

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.title = "Directory Tree Test"

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Handle file selection."""
        self.title = f"Selected: {event.path}"


if __name__ == "__main__":
    app = DirectoryTreeApp()
    app.run()
