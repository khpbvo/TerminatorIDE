import json
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

LOG_PATH = Path.home() / ".terminatoride" / "logs" / "trace.log"


class DevConsoleScreen(Screen):
    BINDINGS = [
        ("escape", "app.pop_screen", "Close"),
        ("f12", "app.pop_screen", "Close Dev Console"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with ScrollableContainer():
            self.container = Vertical()
            yield self.container
        yield Footer()

    def on_mount(self) -> None:
        self.load_recent_traces()

    def load_recent_traces(self):
        self.container.mount(Static("Developer Trace Console", classes="title"))
        if not LOG_PATH.exists():
            self.container.mount(Static("No trace log found."))
            return

        with open(LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()[-100:]

        for line in lines:
            try:
                data = json.loads(line)
                self.container.mount(
                    Static(
                        f"{data['timestamp']} — {data['workflow']} — {data['status']} ({data['duration_ms']}ms)"
                    )
                )
            except Exception:
                continue
