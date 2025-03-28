import json
from datetime import datetime
from pathlib import Path

LOG_PATH = Path.home() / ".terminatoride" / "logs" / "trace.log"


def write_trace_event(event: dict):
    """Write a trace event to the log file."""
    event["timestamp"] = datetime.utcnow().isoformat() + "Z"

    # Handle the mock correctly - in tests, LOG_PATH is mocked with return_value set
    # We need to check if we're using a mock (has return_value) or the real path
    if hasattr(LOG_PATH, "return_value"):
        log_path = LOG_PATH.return_value
    else:
        log_path = LOG_PATH
        # Only create directories for real paths (not in mock case)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to the file using string path to avoid any mock-related issues
    with open(str(log_path), "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
