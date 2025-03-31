"""Diff view screen for TerminatorIDE."""

from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Static


class DiffViewScreen(ModalScreen):
    """Screen to view diffs and confirm changes."""

    BINDINGS = [
        ("escape", "dismiss", "Cancel"),
        ("enter", "apply", "Apply"),
    ]

    DEFAULT_CSS = """
    #diff-scroll {
        width: 100%;
        height: 1fr;
        border: solid $accent;
        margin: 1;
        padding: 1;
    }

    #diff-content {
        width: 100%;
        height: 100%;
        background: $surface-darken-1;
    }

    #button-container {
        width: 100%;
        height: auto;
        padding: 1;
        display: flex;
        justify-content: center;
        margin-top: 1;
    }

    #button-container Button {
        margin: 0 1;
        min-width: 20;
    }

    #explanation {
        margin: 1;
        padding: 1;
        border-left: solid $accent;
        background: $surface-darken-2;
    }
    """

    def __init__(
        self,
        diff_text: str,
        apply_callback,
        title: str = "Code Changes",
        explanation: str = "",
    ):
        super().__init__()
        self.diff_text = diff_text
        self.apply_callback = apply_callback
        self.title = title
        self.explanation = explanation

    def compose(self) -> ComposeResult:
        """Compose the screen widgets."""
        yield Header(self.title)

        if self.explanation:
            yield Static(self.explanation, id="explanation")

        with ScrollableContainer(id="diff-scroll"):
            # Use Rich's Syntax for syntax highlighting of the diff
            diff_syntax = Syntax(
                self.diff_text, "diff", theme="monokai", line_numbers=True
            )
            yield Static(diff_syntax, id="diff-content")

        with Vertical(id="button-container"):
            yield Button("Apply Changes", id="apply-button", variant="primary")
            yield Button("Cancel", id="cancel-button", variant="error")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "apply-button":
            self.action_apply()
        else:
            self.dismiss()

    def action_apply(self) -> None:
        """Apply the changes and dismiss the screen."""
        if self.apply_callback:
            self.apply_callback()
        self.dismiss()
