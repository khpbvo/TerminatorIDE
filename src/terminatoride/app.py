import asyncio

from textual.app import App, ComposeResult
from textual.widgets import Button, Footer, Header

from terminatoride.agent.agent_sdk_trace_bridge import configure_sdk_tracing
from terminatoride.config import get_config
from terminatoride.panels.editor_panel import EditorPanel
from terminatoride.panels.left_panel import LeftPanel
from terminatoride.panels.streaming_agent_panel import StreamingAgentPanel
from terminatoride.screens.devconsole import DevConsoleScreen


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
        layout: vertical;
    }

    #agent-title {
        dock: top;
        width: 100%;
        height: auto;
    }

    #conversation-container {
        width: 100%;
        height: 1fr;
        overflow: auto;
    }

    #input-container {
        dock: bottom;
        width: 100%;
        height: auto;
        padding: 1;
        background: $surface-darken-1;
        border-top: solid $primary;
        layout: horizontal;
    }

    #agent-input {
        width: 1fr;
        margin-right: 1;
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

        # Middle panel (Text Editor) - Use the EditorPanel class
        yield EditorPanel(id="editor-panel")

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

    def connect_panels(self):
        """Connect the panels for inter-panel communication."""
        try:
            # Get panel references
            _ = self.query_one("#left-panel")
            _ = self.query_one("#editor-panel")
            agent_panel = self.query_one("#agent-panel")

            # Connect the agent context to the app
            if hasattr(agent_panel, "streaming_agent") and hasattr(
                agent_panel.streaming_agent, "context"
            ):
                agent_panel.streaming_agent.context.app = self
                print("Successfully connected agent context to app")

            # Register code tools
            from terminatoride.agent.code_tools import (
                analyze_code,
                apply_code_changes,
                improve_code,
                suggest_code_changes,
            )

            # Extend agent tools if tools registry exists
            if hasattr(agent_panel.streaming_agent, "base_agent") and hasattr(
                agent_panel.streaming_agent.base_agent, "tools"
            ):
                tools = agent_panel.streaming_agent.base_agent.tools

                # Add our code tools - don't add duplicates
                tool_names = [getattr(t, "name", str(t)) for t in tools]

                for tool in [
                    analyze_code,
                    apply_code_changes,
                    improve_code,
                    suggest_code_changes,
                ]:
                    tool_name = getattr(tool, "name", str(tool))
                    if tool_name not in tool_names:
                        tools.append(tool)
                        print(f"Added tool: {tool_name}")

            print("Panels connected successfully")
        except Exception as e:
            print(f"Error connecting panels: {e}")
            import traceback

            print(traceback.format_exc())

    def on_mount(self):
        """Handle app mount."""
        # Connect panels for communication
        self.connect_panels()

        # Start the event loop monitor
        self.run_worker(self._setup_event_loop_monitor(), name="event_loop_monitor")

    async def _setup_event_loop_monitor(self):
        """Set up the event loop monitor as a background worker."""
        try:
            from terminatoride.utils.event_loop_monitor import EventLoopMonitor

            monitor = EventLoopMonitor()
            await monitor.start()
            print("Event loop monitor started successfully")

            # Keep the worker alive until the app exits
            while True:
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Error starting event loop monitor: {e}")
            import traceback

            print(traceback.format_exc())


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

    # Create the app
    app = TerminatorIDE()

    # Run the app - this will start the app and handle setup in on_mount
    app.run()


if __name__ == "__main__":
    main()
