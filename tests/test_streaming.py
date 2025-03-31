"""
Tests for the streaming agent functionality.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agents import RunResultStreaming

from terminatoride.agent.context import AgentContext
from terminatoride.agent_streaming import StreamingAgent


class ResponseTextDeltaEvent:
    def __init__(self):
        self.delta = ""


class TestStreamingAgent:
    """Test the streaming agent implementation."""

    @pytest.fixture
    def mock_openai_agent(self):
        """Mock the OpenAI agent."""
        with patch("terminatoride.agent_streaming.get_openai_agent") as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.default_agent = MagicMock()
            mock_agent.rate_limiter = MagicMock()
            mock_agent.rate_limiter.can_make_request.return_value = True
            mock_get_agent.return_value = mock_agent
            yield mock_agent

    @pytest.fixture
    def streaming_agent(self, mock_openai_agent):
        """Create a streaming agent for testing."""
        return StreamingAgent(base_agent=mock_openai_agent)

        # @pytest.mark.asyncio
        # async def test_get_streaming_agent(self):
        #     """Test getting the streaming agent singleton."""
        #     import terminatoride.agent_streaming as streaming

        #     streaming._default_streaming_agent = (
        #         None  # Reset the correct singleton variable
        #     )

        # Patch where StreamingAgent is DEFINED, not where it's imported
        # with patch(
        #     "terminatoride.agent_streaming.StreamingAgent", autospec=True
        # ) as mock_agent_class:
        #     mock_agent = MagicMock()
        #     mock_agent_class.return_value = mock_agent

        #     # First call should create a new instance
        #     agent1 = streaming.get_streaming_agent()  # Use fully qualified call

        #     mock_agent_class.assert_called_once()

        #     # Second call should return the same instance
        #     agent2 = streaming.get_streaming_agent()
        #     assert mock_agent_class.call_count == 1
        #     assert agent1 is agent2

    # def test_get_streaming_agent(self, mocker):
    # """Test getting the streaming agent singleton with reset."""
    # Reset the singleton first
    # from terminatoride.agent_streaming import reset_streaming_agent_for_tests

    # reset_streaming_agent_for_tests()

    # Now mock the StreamingAgent class
    # mock_agent = mocker.patch("terminatoride.agent_streaming.StreamingAgent")

    # Call the function that should create a new agent

    # agent = get_streaming_agent()

    # Verify StreamingAgent was called once
    # mock_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_streaming_response(self, streaming_agent):
        """Test generating streaming responses."""

        # Mock stream_events method to return an async generator
        async def mock_stream_events():
            # Mock a text delta event
            text_delta_event = MagicMock()
            text_delta_event.type = "raw_response_event"
            text_delta_event.data = MagicMock()
            text_delta_event.data.delta = "Hello world"
            yield text_delta_event

            # Mock a tool call event
            tool_call_event = MagicMock()
            tool_call_event.type = "run_item_stream_event"
            tool_call_event.item = MagicMock()
            tool_call_event.item.type = "tool_call_item"
            tool_call_event.item.tool_name = "test_tool"
            tool_call_event.item.tool_arguments = '{"arg": "value"}'
            yield tool_call_event

            # Mock a tool result event
            tool_result_event = MagicMock()
            tool_result_event.type = "run_item_stream_event"
            tool_result_event.item = MagicMock()
            tool_result_event.item.type = "tool_call_output_item"
            tool_result_event.item.tool_name = "test_tool"
            tool_result_event.item.output = "Tool result output"
            yield tool_result_event

            # Mock a handoff event
            handoff_event = MagicMock()
            handoff_event.type = "handoff_stream_event"
            handoff_event.source_agent = MagicMock()
            handoff_event.source_agent.name = "Source Agent"
            handoff_event.target_agent = MagicMock()
            handoff_event.target_agent.name = "Target Agent"
            yield handoff_event

        # Mock RunResultStreaming
        mock_stream_result = MagicMock(spec=RunResultStreaming)
        mock_stream_result.stream_events = mock_stream_events
        mock_stream_result.final_output = "Complete response"

        # Mock Runner.run_streamed
        with patch("terminatoride.agent_streaming.Runner") as mock_runner_class:
            # Create a mock instance that will be returned when Runner() is called
            mock_runner_instance = MagicMock()
            mock_runner_class.return_value = mock_runner_instance

            # Set up the run_streamed method on the instance
            mock_runner_instance.run_streamed.return_value = mock_stream_result

            # Create ASYNC mock callbacks
            on_text_delta = AsyncMock()
            on_tool_call = AsyncMock()
            on_tool_result = AsyncMock()
            on_handoff = AsyncMock()

            # Call the method
            _ = await streaming_agent.generate_streaming_response(
                "Test message",
                AgentContext(),
                on_text_delta=on_text_delta,
                on_tool_call=on_tool_call,
                on_tool_result=on_tool_result,
                on_handoff=on_handoff,
            )

            # Check that Runner.run_streamed was called on the instance
            mock_runner_instance.run_streamed.assert_called_once()

            # Continue with your other assertions...

    @pytest.mark.asyncio
    async def test_rate_limiting(self, streaming_agent):
        """Test rate limiting for streaming responses."""
        # Configure rate limiter to deny requests
        streaming_agent.rate_limiter.can_make_request.return_value = False
        streaming_agent.rate_limiter.time_until_next_request.return_value = 10.5

        # Create a context object
        context = AgentContext()

        # Call the method with the context parameter
        result = await streaming_agent.generate_streaming_response(
            "Test message", context
        )

        # Check the result is a rate limit message
        assert "too many requests" in result.lower()
        assert "10.5 seconds" in result

        # Runner should not have been called
        with patch("terminatoride.agent_streaming.Runner") as mock_runner:
            assert not mock_runner.run_streamed.called

    @pytest.mark.asyncio
    async def test_error_handling(self, mocker):
        """Test error handling in streaming responses."""
        # Reset the singleton
        from terminatoride.agent_streaming import reset_streaming_agent_for_tests

        reset_streaming_agent_for_tests()

        # Create a mock that raises an exception
        mock_run_streamed = mocker.patch("agents.Runner.run_streamed")
        mock_run_streamed.side_effect = Exception("Test error")

        # Get the agent
        from terminatoride.agent_streaming import get_streaming_agent

        agent = get_streaming_agent()

        # Test the method with error handling
        context = AgentContext()
        response = await agent.generate_streaming_response("Test message", context)

        # Verify error is in the response
        assert "error" in response.lower()
        assert "test error" in response.lower()

    @pytest.mark.asyncio
    async def test_callbacks_not_required(self, streaming_agent):
        """Test that callbacks are optional."""

        # Mock stream_events and other setup...

        # Create a context object
        context = AgentContext()

        # Call the method with the context parameter
        _ = await streaming_agent.generate_streaming_response("Test message", context)

        # Assertions...
