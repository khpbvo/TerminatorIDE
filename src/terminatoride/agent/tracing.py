import time

from terminatoride.utils.trace_logger import write_trace_event


class LoggedTrace:
    def __init__(self, workflow_name: str, metadata: dict = None):
        self.workflow_name = workflow_name
        self.metadata = metadata or {}

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = int((time.time() - self.start_time) * 1000)
        status = "error" if exc_type else "success"
        write_trace_event(
            {
                "workflow": self.workflow_name,
                "metadata": self.metadata,
                "status": status,
                "duration_ms": duration_ms,
            }
        )


def trace(workflow_name: str, metadata: dict = None):
    return LoggedTrace(workflow_name, metadata)


__all__ = ["trace"]
