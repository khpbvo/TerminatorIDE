"""
Integration tests for structured output types.
These tests verify the integration between agents, structured outputs, and the agent manager.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agents import Agent, Runner

from terminatoride.agent.agent_manager import AgentManager
from terminatoride.agent.context import AgentContext
from terminatoride.agent.output_types import (
    CodeAnalysisResult,
    CodeIssue,
    CodeSuggestion,
    SeverityLevel,
)
from terminatoride.agent.specialized_agents import SpecializedAgents


@pytest.fixture
def mock_agent_run():
    """Mock Runner.run to return predictable structured outputs."""

    async def mock_run_implementation(
        starting_agent, input, context=None, run_config=None
    ):
        """Generate mock responses based on the agent type."""
        output_type = getattr(starting_agent, "output_type", None)

        if output_type == CodeAnalysisResult:
            # For code analyzer agent, return a structured analysis
            mock_result = MagicMock()
            mock_result.final_output = CodeAnalysisResult(
                language="python",
                issues=[
                    CodeIssue(
                        line_number=10,
                        message="Unused variable 'x'",
                        severity=SeverityLevel.WARNING,
                    ),
                    CodeIssue(
                        line_number=15,
                        message="Function is too complex",
                        severity=SeverityLevel.ERROR,
                    ),
                ],
                suggestions=[
                    CodeSuggestion(
                        line_number=10,
                        original_code="x = 5",
                        suggested_code="# Remove unused variable",
                        explanation="Variable 'x' is never used",
                        impact="Removes clutter",
                    )
                ],
                summary="The code needs improvement",
            )
            return mock_result
        else:
            # Default response for other agent types
            mock_result = MagicMock()
            mock_result.final_output = "Generic response"
            return mock_result

    with patch("terminatoride.agent.agent_manager.Runner") as mock_runner:
        mock_runner.run = AsyncMock(side_effect=mock_run_implementation)
        yield mock_runner


@pytest.mark.asyncio
class TestStructuredOutputsIntegration:
    """Integration tests for structured output types."""

    async def test_code_analyzer_integration(self, mock_agent_run):
        """Test using a code analyzer agent with structured output."""
        # Initialize the agent manager
        with patch("terminatoride.agent.agent_manager.get_config"):
            with patch("terminatoride.agent.agent_manager.set_default_openai_key"):
                agent_manager = AgentManager()

        # Use the SpecializedAgents factory to create an agent
        with patch("terminatoride.agent.specialized_agents.Agent") as mock_agent_class:
            # Make the mock return a real Agent instance that has the correct output_type
            mock_agent = Agent(
                name="Code Analyzer",
                instructions="Analyze code",
                output_type=CodeAnalysisResult,
            )
            mock_agent_class.return_value = mock_agent

            # Create the specialized agent
            code_analyzer = SpecializedAgents.create_code_analyzer()

            # Register it with the agent manager
            agent_manager._agents["Code Analyzer"] = code_analyzer

        # Create a context with a sample file
        sample_code = """
def example():
    x = 5  # Unused variable
    y = 10
    return y + 20

def complex_function():
    # This is a complex function with too many branches
    for i in range(10):
        if i % 2 == 0:
            if i % 3 == 0:
                pass
            else:
                pass
        else:
            pass
    return True
"""
        context = AgentContext()
        context.update_current_file(path="/example/test.py", content=sample_code)

        # Run the agent with our context
        result = await agent_manager.run_agent(
            agent="Code Analyzer",
            user_input="Analyze this Python code",
            context=context,
        )

        # Get the structured output
        analysis = result.final_output

        # Verify the structured output
        assert isinstance(analysis, CodeAnalysisResult)
        assert analysis.language == "python"
        assert len(analysis.issues) == 2
        assert len(analysis.suggestions) == 1

        # Check issue details
        assert analysis.issues[0].line_number == 10
        assert "Unused variable" in analysis.issues[0].message
        assert analysis.issues[0].severity == SeverityLevel.WARNING

        assert analysis.issues[1].line_number == 15
        assert "too complex" in analysis.issues[1].message
        assert analysis.issues[1].severity == SeverityLevel.ERROR

        # Check suggestion details
        assert analysis.suggestions[0].line_number == 10
        assert "never used" in analysis.suggestions[0].explanation.lower()
        # Check summary
        assert "needs improvement" in analysis.summary

    @pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"), reason="No API key available"
    )
    async def test_live_agent_with_structured_output(self):
        """
        Test with a real OpenAI API call if an API key is available.

        This test is skipped if no API key is found in the environment.
        """
        # Initialize the agent manager
        with patch("terminatoride.agent.agent_manager.get_config"):
            with patch("terminatoride.agent.agent_manager.set_default_openai_key"):
                agent_manager = AgentManager()

        # Create a code analyzer agent
        code_analyzer = agent_manager.create_specialized_agent(
            name="Live Code Analyzer",
            instructions="""
            You are a code analyzer. Analyze the provided code and identify issues.
            Be specific and detailed in your analysis.
            """,
            specialty="Code Analysis",
            output_type=CodeAnalysisResult,
        )

        # Create a context with a simple buggy function
        buggy_code = """
def divide(a, b):
    return a / b

result = divide(10, 0)  # Will cause division by zero
"""
        context = AgentContext()
        context.update_current_file(path="/example/buggy.py", content=buggy_code)

        # Run with real API (will be skipped if no API key)
        with patch("terminatoride.agent.agent_manager.Runner", Runner):
            result = await agent_manager.run_agent(
                agent=code_analyzer,
                user_input="Find bugs in this code",
                context=context,
            )

            # Check if we got a structured result
            analysis = result.final_output
            assert isinstance(analysis, CodeAnalysisResult)

            # The actual content will depend on the model's response,
            # but we can check the structure is correct
            assert analysis.language is not None
            assert isinstance(analysis.issues, list)
            assert isinstance(analysis.suggestions, list)
            assert analysis.summary is not None

            # We should have found the division by zero issue
            found_division_issue = False
            for issue in analysis.issues:
                if (
                    "zero" in issue.message.lower()
                    or "division" in issue.message.lower()
                ):
                    found_division_issue = True
                    break

            assert found_division_issue, "Should have found division by zero issue"
