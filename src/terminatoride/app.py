from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Button, Footer, Header, Static

from terminatoride.agent.agent_sdk_trace_bridge import configure_sdk_tracing
from terminatoride.config import get_config
from terminatoride.panels.left_panel import LeftPanel
from terminatoride.screens.devconsole import DevConsoleScreen
from terminatoride.streaming_agent_panel import StreamingAgentPanel


class TerminatorIDE(App):
    """The main TerminatorIDE application with streaming capabilities."""

    TITLE = "TerminatorIDE"
    SUB_TITLE = "AI-Powered Terminal IDE"

    BINDINGS = [("f12", "open_dev_console", "Dev Console"), ("ctrl+q", "quit", "Quit")]

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

    .agent-message {
        background: $surface-darken-1;
        padding: 1;
        margin: 1 0;
    }

    .user-message {
        background: $primary-darken-3;
        padding: 1;
        margin: 1 0;
    }

    .agent-thinking {
        margin: 1 0;
    }

    .agent-tool-call, .agent-tool-result, .agent-handoff {
        background: $secondary-darken-2;
        padding: 1;
        margin: 1 0;
        color: $text;
    }

    .agent-error {
        background: $error;
        color: $text;
        padding: 1;
        margin: 1 0;
    }

    #streaming-options {
        margin: 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()

        # Left panel (File Explorer, Git, SSH)
        yield LeftPanel(id="left-panel")

        # Middle panel (Text Editor)
        with Container(id="editor-panel"):
            yield Static("Editor Panel")

        # Right panel (AI Agent with streaming capabilities)
        yield StreamingAgentPanel(id="agent-panel")

        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "test-agent":
            try:
                # Get the agent panel to ensure we can handle streaming updates
                agent_panel = self.query_one(StreamingAgentPanel)

                # Use the streaming agent through the panel's interface
                await agent_panel._on_send_click()

                # Notify that the test was completed
                self.notify(
                    "Agent streaming test completed successfully!",
                    severity="information",
                )

            except Exception as e:
                self.notify(f"Agent test failed: {e}", severity="error")

    def action_open_dev_console(self) -> None:
        """Open the developer console screen."""
        self.push_screen(DevConsoleScreen())


def main():
    # Get configuration
    config = get_config()

    # Configure tracing if enabled
    if getattr(config.app, "enable_tracing", True):
        try:
            configure_sdk_tracing()
            print("SDK tracing configured successfully")
        except Exception as e:
            print(f"Warning: Failed to configure SDK tracing: {e}")

    # Create and run the app
    app = TerminatorIDE()
    app.run()


if __name__ == "__main__":
    main()
