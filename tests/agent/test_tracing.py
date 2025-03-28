"""
Tests for the tracing functionality.
"""

import time
from unittest.mock import patch

import pytest

from terminatoride.agent.tracing import LoggedTrace, trace


class TestTracing:
    @patch("terminatoride.agent.tracing.write_trace_event")
    def test_trace_context_manager_success(self, mock_write_trace_event):
        """Test that trace context manager logs events properly on success."""
        workflow_name = "test_workflow"
        metadata = {"test_key": "test_value"}

        # Use the context manager
        with trace(workflow_name, metadata):
            # Simulate some work
            time.sleep(0.01)

        # Verify the trace event was written
        mock_write_trace_event.assert_called_once()
        args = mock_write_trace_event.call_args[0][0]

        assert args["workflow"] == workflow_name
        assert args["metadata"] == metadata
        assert args["status"] == "success"
        assert isinstance(args["duration_ms"], int)
        assert args["duration_ms"] > 0

    @patch("terminatoride.agent.tracing.write_trace_event")
    def test_trace_context_manager_error(self, mock_write_trace_event):
        """Test that trace context manager handles exceptions properly."""
        workflow_name = "test_workflow"

        # Use the context manager with an exception
        with pytest.raises(ValueError):
            with trace(workflow_name):
                # Simulate an exception
                raise ValueError("Test exception")

        # Verify the trace event was written with error status
        mock_write_trace_event.assert_called_once()
        args = mock_write_trace_event.call_args[0][0]

        assert args["workflow"] == workflow_name
        assert args["status"] == "error"
        assert isinstance(args["duration_ms"], int)

    @patch("terminatoride.agent.tracing.write_trace_event")
    def test_trace_direct_instantiation(self, mock_write_trace_event):
        """Test that LoggedTrace can be used directly."""
        workflow_name = "test_workflow"

        # Use LoggedTrace directly
        tracer = LoggedTrace(workflow_name)
        tracer.__enter__()
        time.sleep(0.01)
        tracer.__exit__(None, None, None)

        # Verify the trace event was written
        mock_write_trace_event.assert_called_once()
        args = mock_write_trace_event.call_args[0][0]

        assert args["workflow"] == workflow_name
        assert args["status"] == "success"

    @patch("terminatoride.agent.tracing.write_trace_event")
    def test_nested_traces(self, mock_write_trace_event):
        """Test that nested traces work properly."""
        outer_workflow = "outer_workflow"
        inner_workflow = "inner_workflow"

        # Create nested traces
        with trace(outer_workflow):
            time.sleep(0.01)
            with trace(inner_workflow):
                time.sleep(0.01)

        # Verify both trace events were written
        assert mock_write_trace_event.call_count == 2

        # Check the inner trace was written first (LIFO order)
        first_call_args = mock_write_trace_event.call_args_list[0][0][0]
        assert first_call_args["workflow"] == inner_workflow

        # Check the outer trace was written second
        second_call_args = mock_write_trace_event.call_args_list[1][0][0]
        assert second_call_args["workflow"] == outer_workflow

    @patch("terminatoride.agent.tracing.write_trace_event")
    def test_duration_calculation(self, mock_write_trace_event):
        """Test that duration is calculated correctly."""
        workflow_name = "test_workflow"
        sleep_duration = 0.1  # 100ms

        with trace(workflow_name):
            time.sleep(sleep_duration)

        args = mock_write_trace_event.call_args[0][0]
        # Duration should be at least the sleep time (in ms)
        assert args["duration_ms"] >= int(sleep_duration * 1000)
        # But not too much more (allow some overhead)
        assert args["duration_ms"] < int(sleep_duration * 1000) + 50
