# Update tests/agent/test_agent_sdk_trace_bridge.py

"""
Tests for the Agent SDK trace bridge.
"""

from unittest.mock import MagicMock, patch

import pytest

from terminatoride.agent.agent_sdk_trace_bridge import (
    configure_sdk_tracing,
    trace_agent_run,
    wrap_sdk_span,
)


class TestAgentSDKTraceBridge:

    def test_wrap_sdk_span(self):
        """Test that the SDK span wrapper works correctly."""
        # Create a mock span function
        mock_span_func = MagicMock()

        # Wrap it with our function
        wrapped_func = wrap_sdk_span(mock_span_func)

        with patch("terminatoride.agent.tracing.LoggedTrace.__enter__"), patch(
            "terminatoride.agent.tracing.LoggedTrace.__exit__"
        ):
            # Call the wrapped function
            wrapped_func(name="test_span", metadata={"test": "value"})

            # Verify the original function was called
            mock_span_func.assert_called_once()

    @pytest.mark.asyncio
    async def test_trace_agent_run(self):
        """Test that the agent run tracer works correctly."""
        # Create a mock async function
        mock_func = MagicMock()
        mock_func.return_value = MagicMock()
        mock_func.return_value.raw_responses = [
            MagicMock(
                usage=MagicMock(
                    prompt_tokens=100, completion_tokens=50, total_tokens=150
                )
            )
        ]

        # Create an awaitable mock
        async def async_mock(*args, **kwargs):
            return mock_func(*args, **kwargs)

        # Wrap it with our decorator
        wrapped_func = trace_agent_run("test_agent", "gpt-4")(async_mock)

        with patch("terminatoride.agent.tracing.LoggedTrace.__enter__"), patch(
            "terminatoride.agent.tracing.LoggedTrace.__exit__"
        ):
            # Call the wrapped function
            await wrapped_func()

            # Verify the original function was called
            mock_func.assert_called_once()


def test_configure_sdk_tracing():
    """Test that SDK tracing configuration works."""
    from terminatoride.agent.tracing import trace

    # Mock the tracing write function based on the SDK documentation
    with patch(
        "terminatoride.agent.tracing.write_trace_event"
    ) as mock_write_event:  # Call the configuration function
        configure_sdk_tracing()

        # Trigger een dummy trace event om te forceren dat write_trace_event wordt aangeroepen
        with trace("dummy_workflow"):
            pass

        # Controleer dat write_trace_event is aangeroepen
        assert (
            mock_write_event.called
        ), "Tracing method 'write_trace_event' was not called"
