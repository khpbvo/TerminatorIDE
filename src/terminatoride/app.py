import asyncio
import os
import sys
import time
import traceback
from datetime import datetime

from textual.app import App, ComposeResult
from textual.widgets import Button, Footer, Header

from terminatoride.agent.agent_sdk_trace_bridge import configure_sdk_tracing
from terminatoride.config import get_config
from terminatoride.panels.editor_panel import EditorPanel
from terminatoride.panels.left_panel import LeftPanel
from terminatoride.panels.streaming_agent_panel import StreamingAgentPanel
from terminatoride.screens.devconsole import DevConsoleScreen

# Import the event loop monitor directly here
from terminatoride.utils.event_loop_monitor import EventLoopMonitor

# Create a global reference to ensure it doesn't get garbage collected
_global_monitor = None


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
        # Print startup messages to console
        print(f"[{datetime.now().isoformat()}] App mounting - PID: {os.getpid()}")

        # Connect panels for communication
        try:
            self.connect_panels()
            print(f"[{datetime.now().isoformat()}] Panels connected successfully")
        except Exception as e:
            print(f"[{datetime.now().isoformat()}] Error connecting panels: {e}")
            traceback.print_exc()

        # Start the event loop monitor
        try:
            print(
                f"[{datetime.now().isoformat()}] Starting event loop monitor from on_mount"
            )
            self.run_worker(self._setup_event_loop_monitor(), name="event_loop_monitor")
            print(f"[{datetime.now().isoformat()}] Event loop monitor worker started")
        except Exception as e:
            print(
                f"[{datetime.now().isoformat()}] Error starting event loop monitor: {e}"
            )
            traceback.print_exc()

    async def _setup_event_loop_monitor(self):
        """Set up the event loop monitor as a background worker."""
        global _global_monitor

        try:
            print(
                f"[{datetime.now().isoformat()}] Setting up event loop monitor worker"
            )

            # Create direct marker file
            marker_path = os.path.expanduser("~/terminatoride_monitor_start.txt")
            with open(marker_path, "w") as f:
                f.write(f"Monitor startup initiated at: {datetime.now().isoformat()}\n")
                f.write(f"PID: {os.getpid()}\n")
                f.write(f"CWD: {os.getcwd()}\n")
                f.write(f"Python: {sys.executable}\n")
            print(f"[{datetime.now().isoformat()}] Created marker file: {marker_path}")

            # Create monitor instance
            _global_monitor = EventLoopMonitor()
            print(
                f"[{datetime.now().isoformat()}] Monitor instance created: {_global_monitor}"
            )

            # Start the monitor
            print(f"[{datetime.now().isoformat()}] Calling monitor.start()")
            start_time = time.time()
            await _global_monitor.start()
            print(
                f"[{datetime.now().isoformat()}] Monitor.start() completed in {time.time() - start_time:.2f}s"
            )

            # Update marker file
            with open(marker_path, "a") as f:
                f.write(
                    f"Monitor started successfully at: {datetime.now().isoformat()}\n"
                )

            # Keep the worker alive and print status periodically
            counter = 0
            print(f"[{datetime.now().isoformat()}] Entering monitor keep-alive loop")

            while True:
                if counter % 10 == 0:  # Every 10 seconds
                    print(
                        f"[{datetime.now().isoformat()}] Event loop monitor running for {counter}s"
                    )
                    # Update marker file occasionally
                    if counter % 60 == 0:  # Every minute
                        try:
                            with open(marker_path, "a") as f:
                                f.write(
                                    f"Monitor still running at: {datetime.now().isoformat()} (t+{counter}s)\n"
                                )
                        except Exception as e:
                            print(f"Error updating marker file: {e}")

                await asyncio.sleep(1)
                counter += 1

        except Exception as e:
            print(
                f"[{datetime.now().isoformat()}] CRITICAL ERROR in event loop monitor worker: {e}"
            )
            traceback.print_exc()

            # Try to log the error directly to a file
            try:
                error_path = os.path.expanduser("~/terminatoride_monitor_error.txt")
                with open(error_path, "w") as f:
                    f.write(f"Monitor error at {datetime.now().isoformat()}: {e}\n")
                    f.write(traceback.format_exc())
                print(
                    f"[{datetime.now().isoformat()}] Wrote error details to: {error_path}"
                )
            except Exception as nested_error:
                print(
                    f"[{datetime.now().isoformat()}] Failed to write error file: {nested_error}"
                )


def main():
    # Get configuration
    config = get_config()

    # Create direct console output at startup
    print(
        f"\n{'='*80}\n[{datetime.now().isoformat()}] STARTING TERMINATORIDE APP\n{'='*80}"
    )
    print(f"Process ID: {os.getpid()}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Command line: {' '.join(sys.argv)}")
    print(f"{'='*80}\n")

    # Configure tracing if enabled
    if getattr(config.app, "enable_tracing", True):
        try:
            configure_sdk_tracing()
            print(f"[{datetime.now().isoformat()}] SDK tracing configured successfully")
        except Exception as e:
            print(
                f"[{datetime.now().isoformat()}] Warning: Failed to configure SDK tracing: {e}"
            )

    # Create the app
    app = TerminatorIDE()

    # Run the app - this will start the app and handle setup in on_mount
    print(f"[{datetime.now().isoformat()}] Starting Textual app.run()")
    app.run()


if __name__ == "__main__":
    main()
