import asyncio
import json
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Footer, Header, ScrollView, Static

LOG_PATH = Path.home() / ".terminatoride" / "logs" / "trace.log"


class TraceViewer(App):
    TITLE = "Trace Viewer"
    CSS_PATH = None

    def compose(self) -> ComposeResult:
        yield Header()
        with ScrollView():
            self.container = Vertical()
            yield self.container
        yield Footer()

    async def on_mount(self) -> None:
        asyncio.create_task(self.tail_log())

    async def tail_log(self):
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


if __name__ == "__main__":
    app = TraceViewer()
    app.run()
