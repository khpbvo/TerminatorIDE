from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header, Static

from src.terminatoride.screens.devconsole import DevConsoleScreen


class TerminatorIDE(App):
    """The main TerminatorIDE application."""

    TITLE = "TerminatorIDE"
    SUB_TITLE = "AI-Powered Terminal IDE"

    BINDINGS = [("f12", "open_dev_console", "Dev Console")]

    CSS = """
    Screen {
        layout: grid;
        grid-size: 3;
        grid-columns: 1fr 2fr 1fr;
    }

    #left-panel {
        width: 100%;
        height: 100%;
        border: solid green;
    }

    #editor-panel {
        width: 100%;
        height: 100%;
        border: solid blue;
    }

    #agent-panel {
        width: 100%;
        height: 100%;
        border: solid red;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()

        # Left panel (File Explorer, Git, SSH)
        with Container(id="left-panel"):
            yield Static("File Explorer Panel")

        # Middle panel (Text Editor)
        with Container(id="editor-panel"):
            yield Static("Editor Panel")

        # Right panel (AI Agent)
        with Container(id="agent-panel"):
            yield Static("AI Agent Panel")

        yield Footer()

    def action_open_dev_console(self) -> None:
        """Open the developer console screen."""
        self.push_screen(DevConsoleScreen())


def main():
    app = TerminatorIDE()
    app.run()


if __name__ == "__main__":
    main()
