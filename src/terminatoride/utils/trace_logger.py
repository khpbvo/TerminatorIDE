import json
from datetime import datetime
from pathlib import Path

LOG_PATH = Path.home() / ".terminatoride" / "logs" / "trace.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def write_trace_event(event: dict):
    event["timestamp"] = datetime.utcnow().isoformat() + "Z"
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
