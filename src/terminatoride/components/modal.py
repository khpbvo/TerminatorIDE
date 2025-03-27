"""Modal dialog component for TerminatorIDE."""

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static


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
        with Container(classes="modal"):
            yield Static(self.title, id="title")
            yield Static(self.content, id="content")

            with Container(id="buttons"):
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
        with Container(classes="modal"):
            yield Static(self.title, id="title")
            yield Static(self.content, id="content")

            with Container(id="buttons"):
                yield Button("Yes", id="yes", variant="success")
                yield Button("No", id="no", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        if button_id == "yes":
            self.dismiss(True)
        elif button_id == "no":
            self.dismiss(False)


class InputDialog(ModalDialog):
    """A dialog with an input field."""

    def __init__(self, title: str, prompt: str, default: str = "", *args, **kwargs):
        """Initialize the input dialog.

        Args:
            title: The title of the dialog.
            prompt: The prompt message.
            default: The default value for the input field.
        """
        super().__init__(title, prompt, *args, **kwargs)
        self.default = default

    def compose(self) -> ComposeResult:
        """Compose the input dialog."""
        from textual.widgets import Input

        with Container(classes="modal"):
            yield Static(self.title, id="title")
            yield Static(self.content, id="prompt")
            yield Input(value=self.default, id="input")

            with Container(id="buttons"):
                yield Button("OK", id="ok", variant="primary")
                yield Button("Cancel", id="cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        if button_id == "ok":
            input_value = self.query_one(Input).value
            self.dismiss(input_value)
        elif button_id == "cancel":
            self.dismiss(None)
