from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Button, Footer, Header, Static

from terminatoride.agent.agent_sdk_trace_bridge import configure_sdk_tracing
from terminatoride.agents.openai_agent import get_openai_agent
from terminatoride.config import get_config
from terminatoride.screens.devconsole import (
    DevConsoleScreen,  # Note the fixed import path
)


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
            yield Button("Test Agent", id="test-agent")

        yield Footer()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "test-agent":
            try:
                agent = get_openai_agent()
                response = await agent.generate_response(
                    "Hello, can you help me test the agent tracing?"
                )

                # Display the response in the agent panel
                agent_panel = self.query_one("#agent-panel")
                agent_panel.mount(
                    Static(f"Agent response: {response}", classes="response")
                )

                print("Agent test completed successfully!")
            except Exception as e:
                print(f"Agent test failed: {e}")

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
