"""
Tests for structured output types integration with AgentManager.
"""

from unittest.mock import MagicMock, patch

import pytest
from agents import RunResult
from pydantic import BaseModel

from terminatoride.agent.agent_manager import AgentManager
from terminatoride.agent.output_types import (
    CodeAnalysisResult,
    CodeIssue,
    SeverityLevel,
)


class TestStructuredOutputs:
    """Test structured output types integration with AgentManager."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        mock_config = MagicMock()
        mock_config.openai.api_key = "test_api_key"
        mock_config.openai.model = "gpt-4o"
        return mock_config

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent instance."""
        mock_agent = MagicMock()
        mock_agent.name = "Test Agent"
        mock_agent.model = "gpt-4o"
        return mock_agent

    @pytest.fixture
    def agent_manager(self, mock_config):
        """Create an AgentManager instance for testing."""
        with patch(
            "terminatoride.agent.agent_manager.get_config", return_value=mock_config
        ):
            with patch("terminatoride.agent.agent_manager.set_default_openai_key"):
                with patch(
                    "terminatoride.agent.agent_manager.register_tools", return_value=[]
                ):
                    manager = AgentManager()
                    yield manager

    def test_create_agent_with_output_type(self, agent_manager):
        """Test creating an agent with a structured output type."""

        # Define a simple output type for testing
        class TestOutput(BaseModel):
            message: str
            score: int

        with patch("terminatoride.agent.agent_manager.Agent") as mock_agent_class:
            # Configure the mock to return a specific agent
            mock_agent = MagicMock()
            mock_agent.name = "Test Agent"
            mock_agent_class.return_value = mock_agent

            # Create the agent with an output type
            _ = agent_manager.create_agent(
                name="Test Agent",
                instructions="Test instructions",
                output_type=TestOutput,
            )

            # Verify Agent was created with the output type
            mock_agent_class.assert_called_once()
            args, kwargs = mock_agent_class.call_args
            assert kwargs["name"] == "Test Agent"
            assert kwargs["instructions"] == "Test instructions"
            assert kwargs["output_type"] == TestOutput

            # Verify the agent was registered
            assert agent_manager.get_agent("Test Agent") == mock_agent

    def test_create_specialized_agent(self, agent_manager):
        """Test creating a specialized agent with a structured output type."""
        with patch("terminatoride.agent.agent_manager.Agent") as mock_agent_class:
            # Configure the mock to return a specific agent
            mock_agent = MagicMock()
            mock_agent.name = "Code Analyzer"
            mock_agent_class.return_value = mock_agent

            # Create a specialized agent
            _ = agent_manager.create_specialized_agent(
                name="Code Analyzer",
                instructions="Analyze code for issues",
                specialty="Code Analysis",
                output_type=CodeAnalysisResult,
            )

            # Verify Agent was created with the correct parameters
            mock_agent_class.assert_called_once()
            args, kwargs = mock_agent_class.call_args
            assert kwargs["name"] == "Code Analyzer"
            assert kwargs["instructions"] == "Analyze code for issues"
            assert kwargs["output_type"] == CodeAnalysisResult

            # Verify the metadata was set
            assert hasattr(mock_agent, "metadata")
            assert mock_agent.metadata == {"specialty": "Code Analysis"}

    @pytest.mark.asyncio
    async def test_run_agent_with_structured_output(self, agent_manager, mock_agent):
        """Test running an agent that returns structured output."""
        # Set up a mock output for the agent
        issue = CodeIssue(
            line_number=10, message="Unused variable", severity=SeverityLevel.WARNING
        )
        structured_output = CodeAnalysisResult(
            language="python",
            issues=[issue],
            suggestions=[],
            summary="Code is generally well-structured",
        )

        # Create a mock RunResult that will return our structured output
        mock_result = MagicMock(spec=RunResult)
        mock_result.final_output = structured_output

        # Configure mocks
        with patch("terminatoride.agent.agent_manager.Runner") as mock_runner:
            # Set up the mock to return our result
            mock_runner.run = MagicMock(return_value=mock_result)

            # Set the mock_agent's output_type to CodeAnalysisResult
            mock_agent.output_type = CodeAnalysisResult
            agent_manager._agents["Code Analyzer"] = mock_agent

            # Run the agent
            result = await agent_manager.run_agent(
                agent="Code Analyzer", user_input="Analyze this code"
            )

            # Verify the Runner was called
            mock_runner.run.assert_called_once()

            # Verify the structured output was returned correctly
            assert result == mock_result
            assert isinstance(result.final_output, CodeAnalysisResult)
            assert result.final_output.language == "python"
            assert len(result.final_output.issues) == 1
            assert result.final_output.issues[0].line_number == 10
            assert result.final_output.issues[0].severity == SeverityLevel.WARNING
            assert result.final_output.summary == "Code is generally well-structured"

    def test_list_specialized_agents(self, agent_manager):
        """Test listing specialized agents."""
        # Create mock agents with metadata
        agent1 = MagicMock()
        agent1.metadata = {"specialty": "Code Analysis"}
        agent1.output_type = CodeAnalysisResult
        agent1.output_type.__name__ = "CodeAnalysisResult"

        agent2 = MagicMock()
        agent2.metadata = {"specialty": "Refactoring"}
        agent2.output_type = None

        agent3 = MagicMock()
        # No metadata

        # Add agents to manager
        agent_manager._agents = {
            "Code Analyzer": agent1,
            "Refactoring Planner": agent2,
            "Regular Agent": agent3,
        }

        # List specialized agents
        specialized = agent_manager.list_specialized_agents()

        # Verify the result
        assert len(specialized) == 2
        assert specialized[0]["name"] == "Code Analyzer"
        assert specialized[0]["specialty"] == "Code Analysis"
        assert specialized[0]["output_type"] == "CodeAnalysisResult"
        assert specialized[1]["name"] == "Refactoring Planner"
        assert specialized[1]["specialty"] == "Refactoring"
        assert specialized[1]["output_type"] is None

        # Regular agent should not be included
        agent_names = [agent["name"] for agent in specialized]
        assert "Regular Agent" not in agent_names
