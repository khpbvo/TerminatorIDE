"""
Tests for the trace logger functionality.
"""

import json
from unittest.mock import patch

import pytest

from terminatoride.utils.trace_logger import write_trace_event


@pytest.fixture
def temp_log_path(tmp_path):
    """Create a temporary log path for testing."""
    log_file = tmp_path / "trace.log"
    return log_file


class TestTraceLogger:
    @patch("terminatoride.utils.trace_logger.LOG_PATH")
    def test_write_trace_event(self, mock_log_path, temp_log_path):
        """Test writing a trace event to the log file."""
        # Set the mock log path to our temporary file
        mock_log_path.return_value = temp_log_path
        mock_log_path.parent.mkdir.return_value = None

        # Create a sample event
        event = {
            "workflow": "test_workflow",
            "metadata": {"test": "value"},
            "status": "success",
            "duration_ms": 100,
        }

        # Write the event
        write_trace_event(event)

        # Check that the file was created and contains the event
        assert temp_log_path.exists()

        with open(temp_log_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse the JSON content
        log_event = json.loads(content.strip())

        # Verify the event data
        assert log_event["workflow"] == "test_workflow"
        assert log_event["metadata"] == {"test": "value"}
        assert log_event["status"] == "success"
        assert log_event["duration_ms"] == 100
        assert "timestamp" in log_event  # Timestamp should be added

    @patch("terminatoride.utils.trace_logger.LOG_PATH")
    def test_multiple_trace_events(self, mock_log_path, temp_log_path):
        """Test writing multiple trace events to the log file."""
        # Set the mock log path to our temporary file
        mock_log_path.return_value = temp_log_path
        mock_log_path.parent.mkdir.return_value = None

        # Create sample events
        events = [
            {
                "workflow": "workflow1",
                "status": "success",
                "duration_ms": 100,
            },
            {
                "workflow": "workflow2",
                "status": "error",
                "duration_ms": 200,
            },
        ]

        # Write the events
        for event in events:
            write_trace_event(event)

        # Check that the file contains both events
        with open(temp_log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 2

        first_event = json.loads(lines[0])
        second_event = json.loads(lines[1])

        assert first_event["workflow"] == "workflow1"
        assert first_event["status"] == "success"

        assert second_event["workflow"] == "workflow2"
        assert second_event["status"] == "error"

    def test_log_directory_creation(self, tmp_path):
        """Test that the log directory is created if it doesn't exist."""
        # Create a path that doesn't exist yet
        nonexistent_path = tmp_path / "nested" / "dir" / "trace.log"

        with patch("terminatoride.utils.trace_logger.LOG_PATH", nonexistent_path):
            # This should create the parent directories
            with patch("terminatoride.utils.trace_logger.open") as mock_open:
                # Mock the file open to avoid actually writing
                mock_open.return_value.__enter__.return_value.write.return_value = None

                # Call the function
                write_trace_event(
                    {"workflow": "test", "status": "success", "duration_ms": 100}
                )

            # Check that the parent directories were created
            assert nonexistent_path.parent.exists()

    @patch("terminatoride.utils.trace_logger.LOG_PATH")
    def test_trace_event_timestamp(self, mock_log_path, temp_log_path):
        """Test that a timestamp is added to the trace event."""
        # Set the mock log path to our temporary file
        mock_log_path.return_value = temp_log_path
        mock_log_path.parent.mkdir.return_value = None

        # Create a sample event without a timestamp
        event = {
            "workflow": "test_workflow",
            "status": "success",
            "duration_ms": 100,
        }

        # Write the event
        write_trace_event(event)

        # Check that the timestamp was added
        with open(temp_log_path, "r", encoding="utf-8") as f:
            content = f.read()

        log_event = json.loads(content.strip())
        assert "timestamp" in log_event

        # Verify it has the ISO format with Z suffix
        timestamp = log_event["timestamp"]
        assert timestamp.endswith("Z")

        # Basic format check (this is not exhaustive)
        parts = timestamp.rstrip("Z").split("T")
        assert len(parts) == 2  # Date and time parts
        date_part = parts[0].split("-")
        assert len(date_part) == 3  # Year, month, day
