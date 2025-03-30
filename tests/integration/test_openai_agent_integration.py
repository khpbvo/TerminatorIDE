"""
Integration tests for the OpenAI Agent implementation.
These tests verify the agent works correctly within the application context.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from terminatoride.agent.context import AgentContext, FileContext
from terminatoride.agents.openai_agent import OpenAIAgent
from terminatoride.app import TerminatorIDE


class TestOpenAIAgentIntegration:
    """Test the OpenAI Agent integration with the application."""

    @pytest.fixture
    def setup_env(self):
        """Set up environment variables for testing."""
        # For integration tests, we want to use a real API key
        # Always try to load from .env file
        try:
            from dotenv import load_dotenv

            # Force reload to override any existing values
            load_dotenv(override=True)
            if (
                os.environ.get("OPENAI_API_KEY")
                and os.environ.get("OPENAI_API_KEY") != "test_api_key"
            ):
                print("Using real API key from .env for integration tests")
        except ImportError:
            print(
                "python-dotenv not installed. Install with: pip install python-dotenv"
            )

        # Fallback to test key only if no real key is available
        if (
            "OPENAI_API_KEY" not in os.environ
            or os.environ.get("OPENAI_API_KEY") == "test_api_key"
        ):
            print(
                "WARNING: No real API key found. Integration tests will fail with API errors."
            )

        os.environ["TERMINATOR_THEME"] = "dark"
        os.environ["TERMINATOR_EDITOR"] = "vim"
        os.environ["TERMINATOR_TEST_MODE"] = "True"
        yield
        # Clean up
        os.environ.pop("TERMINATOR_TEST_MODE", None)

    @pytest.fixture
    def mock_runner(self):
        """Mock Runner for testing."""
        with patch("terminatoride.agents.openai_agent.Runner") as mock_runner:
            # Create a mock result
            mock_result = MagicMock()
            mock_result.final_output = (
                "I analyzed your code and found it to be well-structured."
            )

            # Set up the run method to return the mock result
            mock_runner.run = AsyncMock(return_value=mock_result)
            yield mock_runner

    @pytest.mark.asyncio
    async def test_agent_singleton(self, setup_env, mock_runner):
        """Test that get_openai_agent returns a singleton instance."""
        import terminatoride.agents.openai_agent as oa

        oa._default_agent = None  # Reset the correct singleton variable

        # Patch where OpenAIAgent is DEFINED, not where it's imported
        with patch(
            "terminatoride.agents.openai_agent.OpenAIAgent", autospec=True
        ) as mock_agent_class:
            mock_agent = MagicMock()
            mock_agent_class.return_value = mock_agent

            # First call should create a new instance
            agent1 = (
                oa.get_openai_agent()
            )  # Use fully qualified call through the module

            mock_agent_class.assert_called_once()

            # Second call should return the same instance
            agent2 = oa.get_openai_agent()
            assert mock_agent_class.call_count == 1
            assert agent1 is agent2

    @pytest.mark.asyncio
    async def test_agent_with_file_context(self, setup_env, mock_runner):
        """Test the agent with file context."""
        # Create mock agent with file context
        agent = OpenAIAgent()

        # Create a file context
        file_context = FileContext(
            path="/test/example.py",
            content="def hello():\n    print('Hello, world!')",
            language="python",
            cursor_position=10,
        )

        # Create agent context with the file
        context = AgentContext()
        context.update_current_file(
            file_context.path, file_context.content, file_context.cursor_position
        )

        # Generate a response
        response = await agent.generate_response("Explain this code", context)

        # Verify the response
        assert isinstance(response, str)
        # Verify the context was passed to the Runner
        assert mock_runner.run.called
        args, kwargs = mock_runner.run.call_args
        assert kwargs["context"] == context

    @pytest.mark.skip(reason="This test requires a UI environment and can be slow")
    @pytest.mark.asyncio
    async def test_agent_in_app(self, setup_env, mock_runner):
        import asyncio

        """Test the agent integration in the app UI."""
        app = TerminatorIDE()

        async with app.run_test() as pilot:
            # Get the agent panel
            agent_panel = pilot.app.query_one("#agent-panel")

            # Find the input field and send button
            input_field = agent_panel.query_one("#agent-input")
            send_button = agent_panel.query_one("#send-button")

            # Type a message
            await pilot.press(*list("Can you help me with Python?"))
            assert input_field.value == "Can you help me with Python?"

            # Click the send button
            await pilot.click(send_button)

            # Wait for the agent to process
            await asyncio.sleep(0.1)

            # Check that the response appears in the conversation
            conversation = agent_panel.query_one("#conversation")
            messages = conversation.query("Static")

            # There should be at least an initial welcome message, the user message, and the response
            assert len(messages) >= 3

            # Check that the last message contains the agent's response
            assert "I analyzed your code" in messages[-1].renderable

    @pytest.mark.asyncio
    async def test_multiple_requests_rate_limiting(self, setup_env, mock_runner):
        """Test that multiple requests are properly rate limited."""
        agent = OpenAIAgent()

        # Set a very restrictive rate limit for testing
        agent.rate_limiter.max_requests = 3
        agent.rate_limiter.time_window = 1  # 1 second

        # Create several requests in quick succession
        responses = []
        for i in range(5):
            response = await agent.generate_response(f"Request {i+1}")
            responses.append(response)

        # First 3 should be normal responses
        for i in range(3):
            assert (
                responses[i]
                == "I analyzed your code and found it to be well-structured."
            )

        # The remaining should be rate limit messages
        for i in range(3, 5):
            assert "too many requests" in responses[i].lower()

        # The Runner should only have been called the allowed number of times
        assert mock_runner.run.call_count == 3

    @pytest.fixture
    def sample_python_file(self, tmp_path):
        """Create a sample Python file for testing."""
        file_path = tmp_path / "sample.py"
        file_path.write_text(
            """
def factorial(n):
    \"\"\"Calculate the factorial of n.\"\"\"
    if n <= 1:
        return 1
    return n * factorial(n-1)

print(factorial(5))
"""
        )
        return file_path

    @pytest.mark.asyncio
    async def test_agent_with_real_file(
        self, setup_env, mock_runner, sample_python_file
    ):
        """Test the agent with a real file from the filesystem."""
        agent = OpenAIAgent()

        # Create a context with the real file
        context = AgentContext()
        context.update_current_file(
            str(sample_python_file), sample_python_file.read_text(), 0
        )

        # Generate a response
        response = await agent.generate_response(
            "Explain this factorial function", context
        )

        # Verify the response
        assert isinstance(response, str)

        # Verify the file content was passed correctly
        assert mock_runner.run.called
        args, kwargs = mock_runner.run.call_args
        assert "factorial" in kwargs["context"].current_file.content
