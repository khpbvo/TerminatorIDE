import asyncio
import json
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.widgets import Footer, Header, Static

LOG_PATH = Path.home() / ".terminatoride" / "logs" / "trace.log"

# Create log directory if it doesn't exist
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


class TraceViewer(App):
    TITLE = "Trace Viewer"
    CSS_PATH = None

    def compose(self) -> ComposeResult:
        yield Header()
        with ScrollableContainer():  # Using ScrollableContainer instead of ScrollView
            self.container = Vertical()
            yield self.container
        yield Footer()

    async def on_mount(self) -> None:
        asyncio.create_task(self.tail_log())

    async def tail_log(self):
        self.container.mount(Static(f"Watching log file: {LOG_PATH}"))

        try:
            if not LOG_PATH.exists():
                LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                LOG_PATH.touch()
                self.container.mount(Static("Created new log file"))

            with open(LOG_PATH, "r", encoding="utf-8") as f:
                f.seek(0, 2)  # move to end of file
                while True:
                    line = f.readline()
                    if not line:
                        await asyncio.sleep(0.2)
                        continue
                    try:
                        data = json.loads(line)
                        widget = Static(
                            f"{data['timestamp']} — {data['workflow']} — {data['status']} ({data['duration_ms']}ms)"
                        )
                        self.container.mount(widget)
                    except Exception:
                        continue
        except Exception as e:
            self.container.mount(Static(f"Error: {str(e)}"))


if __name__ == "__main__":
    app = TraceViewer()
    app.run()
