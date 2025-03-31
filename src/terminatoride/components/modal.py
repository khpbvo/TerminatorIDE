"""Modal dialogs for TerminatorIDE."""

from textual.app import ComposeResult
from textual.containers import Center, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static

from ..utils.logging import setup_logger

# Set up logger
logger = setup_logger("modals", "modals.log")


class ModalDialog(ModalScreen):
    """A modal dialog that can be used for user interactions."""

    def __init__(self, title: str, content: str, *args, **kwargs):
        """Initialize the modal dialog.

        Args:
            title: The title of the dialog.
            content: The content of the dialog.
        """
        super().__init__(*args, **kwargs)
        self.title = title
        self.content = content

    def compose(self) -> ComposeResult:
        """Compose the modal dialog."""
        with Center():
            with Vertical(id="dialog-container"):
                yield Label(self.title, id="title")
                yield Static(self.content, id="content")

                with Vertical(id="button-container"):
                    yield Button("OK", id="ok", variant="primary")
                    yield Button("Cancel", id="cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        if button_id == "ok":
            self.dismiss(True)
        elif button_id == "cancel":
            self.dismiss(False)


class ConfirmDialog(ModalDialog):
    """A confirmation dialog with Yes/No buttons."""

    def compose(self) -> ComposeResult:
        """Compose the confirmation dialog."""
        with Center():
            with Vertical(id="dialog-container"):
                yield Label(self.title, id="title")
                yield Static(self.content, id="content")

                with Vertical(id="button-container"):
                    yield Button("Yes", id="yes", variant="success")
                    yield Button("No", id="no", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        if button_id == "yes":
            self.dismiss(True)
        elif button_id == "no":
            self.dismiss(False)


class InputDialog(ModalScreen):
    """A dialog for text input."""

    DEFAULT_CSS = """
    #dialog-container {
        width: 60%;
        padding: 1;
        border: solid $accent;
        background: $surface;
    }

    #dialog-title {
        text-align: center;
        width: 100%;
        background: $accent;
        color: $text;
        padding: 1 0;
    }

    #dialog-message {
        margin: 1 0;
    }

    #dialog-input {
        margin: 1 0;
    }

    #button-container {
        margin-top: 1;
        width: 100%;
        height: auto;
        align-horizontal: center;
    }

    Button {
        margin: 0 1;
        min-width: 8;
    }
    """

    def __init__(
        self, title: str, message: str, default_value: str = "", name: str = None
    ):
        super().__init__(name=name)
        self.title_text = title
        self.message = message
        self.default_value = default_value
        logger.debug(f"InputDialog initialized: {title}")

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="dialog-container"):
                yield Label(self.title_text, id="dialog-title")
                yield Static(self.message, id="dialog-message")
                yield Input(value=self.default_value, id="dialog-input")
                with Vertical(id="button-container"):
                    yield Button("OK", id="confirm", variant="primary")
                    yield Button("Cancel", id="cancel", variant="default")

    def on_mount(self) -> None:
        logger.debug("InputDialog mounted")
        self.query_one("#dialog-input").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "confirm":
            input_value = self.query_one("#dialog-input").value
            logger.info(f"Dialog confirmed with value: {input_value}")
            # Make sure we're returning a string value, not None
            self.dismiss(input_value if input_value else "")
        else:
            logger.info("Dialog cancelled")
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (pressing Enter)."""
        input_value = self.query_one("#dialog-input").value
        logger.info(f"Input submitted with value: {input_value}")
        # Make sure we're returning a string value, not None
        self.dismiss(input_value if input_value else "")

    def key_escape(self) -> None:
        """Handle escape key press."""
        logger.info("Dialog cancelled with escape key")
        self.dismiss(None)
