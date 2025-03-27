"""Help screen for displaying keyboard shortcuts."""

from textual.app import ComposeResult
from textual.containers import Container, Grid
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Header, Label, Static


class HelpScreen(ModalScreen):
    """A help screen that shows keyboard shortcuts and commands."""

    BINDINGS = [
        ("escape", "dismiss", "Close"),
        ("q", "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the help screen."""
        yield Header(show_clock=False)

        with Container(id="help-container"):
            yield Label("Keyboard Shortcuts", id="help-title")

            with Grid(id="shortcut-grid"):
                # Navigation shortcuts
                yield Label("Navigation", classes="category")
                yield Static("Ctrl+1", classes="shortcut")
                yield Static("Focus Left Panel", classes="description")

                yield Static("")
                yield Static("Ctrl+2", classes="shortcut")
                yield Static("Focus Editor", classes="description")

                yield Static("")
                yield Static("Ctrl+3", classes="shortcut")
                yield Static("Focus Agent", classes="description")

                # General shortcuts
                yield Label("General", classes="category")
                yield Static("F1", classes="shortcut")
                yield Static("Show Help", classes="description")

                yield Static("")
                yield Static("F2", classes="shortcut")
                yield Static("Show Notification", classes="description")

                yield Static("")
                yield Static("F3", classes="shortcut")
                yield Static("Show Modal Dialog", classes="description")

                yield Static("")
                yield Static("F10", classes="shortcut")
                yield Static("Toggle Theme", classes="description")

                yield Static("")
                yield Static("Ctrl+Q", classes="shortcut")
                yield Static("Quit", classes="description")

                yield Static("")
                yield Static("Escape", classes="shortcut")
                yield Static("Cancel/Close", classes="description")

            with Container(id="help-footer"):
                yield Button("Close", variant="primary", id="close-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "close-button":
            self.dismiss()


class KeyBindingHelp:
    """Utility class for generating help content from keybindings."""

    @staticmethod
    def get_binding_table(app):
        """Get a table of key bindings from the app."""
        bindings = app.bindings.shown_keys

        table = DataTable()
        table.add_column("Key", width=20)
        table.add_column("Action", width=30)
        table.add_column("Description", width=50)

        for binding in bindings:
            table.add_row(
                binding.key_display,
                binding.action,
                binding.description or "",
            )

        return table
