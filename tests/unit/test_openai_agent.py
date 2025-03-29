"""
Tests for the OpenAI Agent implementation with rate limiting.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agents import RunResult

from terminatoride.agent.context import AgentContext
from terminatoride.agents.openai_agent import OpenAIAgent


class TestOpenAIAgent:
    """Test the OpenAI Agent implementation."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        mock_config = MagicMock()
        mock_config.openai.api_key = "test_api_key"
        mock_config.openai.model = "gpt-4o"
        return mock_config

    @pytest.fixture
    def mock_runner(self):
        """Mock Runner for testing."""
        with patch("terminatoride.agents.openai_agent.Runner") as mock_runner:
            # Create a mock result
            mock_result = MagicMock(spec=RunResult)
            mock_result.final_output = "This is a test response"

            # Set up the run method to return the mock result
            mock_runner.run = AsyncMock(return_value=mock_result)
            yield mock_runner

    @pytest.fixture
    def agent(self, mock_config):
        """Create an OpenAI agent instance for testing."""
        with patch(
            "terminatoride.agents.openai_agent.get_config", return_value=mock_config
        ):
            with patch("terminatoride.agents.openai_agent.set_default_openai_key"):
                with patch(
                    "terminatoride.agents.openai_agent.register_tools", return_value=[]
                ):
                    with patch("terminatoride.agents.openai_agent.Agent"):
                        agent = OpenAIAgent()
                        yield agent

    @pytest.mark.asyncio
    async def test_generate_response_basic(self, agent, mock_runner):
        """Test the basic generate_response functionality."""
        response = await agent.generate_response("Hello, how are you?")

        # Verify the response
        assert response == "This is a test response"

        # Verify the Runner was called properly
        mock_runner.run.assert_called_once()

        # Verify the rate limiter was used
        assert agent.rate_limiter.request_count == 1

    @pytest.mark.asyncio
    async def test_generate_response_with_context(self, agent, mock_runner):
        """Test generate_response with a context object."""
        context = AgentContext()
        response = await agent.generate_response("Hello", context)

        # Verify the response
        assert response == "This is a test response"

        # Verify the Runner was called with the context
        mock_runner.run.assert_called_once()
        args, kwargs = mock_runner.run.call_args
        assert kwargs["context"] == context

    @pytest.mark.asyncio
    async def test_run_specialized_agent(self, agent, mock_runner):
        """Test the run_specialized_agent method."""
        # Mock a specialized agent
        agent.specialized_agents = {"code_helper": MagicMock()}

        response = await agent.run_specialized_agent(
            "code_helper", "Help me with Python"
        )

        # Verify the response
        assert response == "This is a test response"

        # Verify the Runner was called properly
        mock_runner.run.assert_called_once()

        # Verify the rate limiter was used
        assert agent.rate_limiter.request_count == 1

    @pytest.mark.asyncio
    async def test_run_specialized_agent_not_found(self, agent):
        """Test run_specialized_agent with a non-existent agent."""
        with pytest.raises(
            ValueError, match="Specialized agent 'nonexistent' not found"
        ):
            await agent.run_specialized_agent("nonexistent", "Hello")

    @pytest.mark.asyncio
    async def test_rate_limiting(self, agent, mock_runner):
        """Test that rate limiting works correctly."""
        # Set a very restrictive rate limit for testing
        agent.rate_limiter.max_requests = 2
        agent.rate_limiter.time_window = 5  # 5 seconds

        # First request should be allowed
        response1 = await agent.generate_response("First request")
        assert response1 == "This is a test response"
        assert agent.rate_limiter.request_count == 1

        # Second request should be allowed
        response2 = await agent.generate_response("Second request")
        assert response2 == "This is a test response"
        assert agent.rate_limiter.request_count == 2

        # Third request should be rate limited
        response3 = await agent.generate_response("Third request")
        assert "too many requests" in response3.lower()
        # Request count should not increase since the request was denied
        assert agent.rate_limiter.request_count == 2

        # The Runner should only have been called twice
        assert mock_runner.run.call_count == 2

    @pytest.mark.asyncio
    async def test_rate_limiting_recovery(self, agent, mock_runner):
        """Test that rate limiting recovers after the time window expires."""
        # Set a very short time window for testing
        agent.rate_limiter.max_requests = 1
        agent.rate_limiter.time_window = 0.1  # 100ms

        # First request should be allowed
        response1 = await agent.generate_response("First request")
        assert response1 == "This is a test response"

        # Second request should be rate limited
        response2 = await agent.generate_response("Second request")
        assert "too many requests" in response2.lower()

        # Wait for rate limiting to reset
        await asyncio.sleep(0.2)  # Wait a bit longer than the time window

        # Third request should be allowed again
        response3 = await agent.generate_response("Third request")
        assert response3 == "This is a test response"

        # The Runner should have been called twice (first and third requests)
        assert mock_runner.run.call_count == 2

    @pytest.mark.asyncio
    async def test_specialized_agent_rate_limiting(self, agent, mock_runner):
        """Test that rate limiting works for specialized agents."""
        # Mock a specialized agent
        agent.specialized_agents = {"code_helper": MagicMock()}

        # Set a very restrictive rate limit for testing
        agent.rate_limiter.max_requests = 1
        agent.rate_limiter.time_window = 5  # 5 seconds

        # First request should be allowed
        response1 = await agent.run_specialized_agent("code_helper", "First request")
        assert response1 == "This is a test response"

        # Second request should be rate limited
        response2 = await agent.run_specialized_agent("code_helper", "Second request")
        assert "rate limit reached" in response2.lower()

        # The Runner should only have been called once
        assert mock_runner.run.call_count == 1

    @pytest.mark.asyncio
    async def test_error_handling(self, agent):
        """Test error handling in generate_response."""
        # Mock the Runner to raise an exception
        with patch(
            "terminatoride.agents.openai_agent.Runner.run",
            side_effect=Exception("Test error"),
        ):
            response = await agent.generate_response("Trigger an error")

            # Verify the error is properly handled
            assert "error" in response.lower()
            assert "test error" in response.lower()

    @pytest.mark.asyncio
    async def test_create_specialized_agent(self, agent):
        """Test creating a specialized agent."""
        with patch("terminatoride.agents.openai_agent.Agent") as mock_agent_class:
            # Call the method
            agent.create_specialized_agent(
                name="Code Expert",
                instructions="You are a coding expert.",
                model_type=None,  # Use default
            )

            # Verify Agent was created with correct parameters
            mock_agent_class.assert_called_once()
            args, kwargs = mock_agent_class.call_args
            assert kwargs["name"] == "Code Expert"
            assert "coding expert" in kwargs["instructions"].lower()

    def test_get_available_agents(self, agent):
        """Test getting available specialized agents."""
        # Add some specialized agents
        agent.specialized_agents = {
            "code_helper": MagicMock(),
            "writing_assistant": MagicMock(),
        }

        # Get the list of available agents
        available_agents = agent.get_available_agents()

        # Verify the result
        assert set(available_agents) == {"code_helper", "writing_assistant"}
