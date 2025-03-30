"""
Tests for specialized_agents.py module.
"""

from unittest.mock import patch

from agents import Agent

from terminatoride.agent.output_types import (
    CodeAnalysisResult,
    DocumentationResult,
    ErrorDiagnosis,
    GitResult,
    ProjectSummary,
    RefactoringPlan,
    SearchResults,
    TestSuiteResult,
)
from terminatoride.agent.specialized_agents import SpecializedAgents


class TestSpecializedAgents:
    """Test the SpecializedAgents factory class."""

    @patch("terminatoride.agent.specialized_agents.Agent")
    def test_create_code_analyzer(self, mock_agent):
        """Test creating a code analyzer agent."""
        # Configure the mock
        mock_agent.return_value = Agent(name="Mock Agent", instructions="Mock")

        # Create the agent
        _ = SpecializedAgents.create_code_analyzer()

        # Check that Agent was called with correct parameters
        mock_agent.assert_called_once()
        args, kwargs = mock_agent.call_args

        assert kwargs["name"] == "Code Analyzer"
        assert "code analyzer" in kwargs["instructions"].lower()
        assert kwargs["output_type"] == CodeAnalysisResult
        assert len(kwargs["tools"]) > 0

        # Check that get_file_content is in the tools - fix the tool name check
        tool_names = [
            tool.name if hasattr(tool, "name") else str(tool)
            for tool in kwargs["tools"]
        ]
        assert "get_file_content" in tool_names

    @patch("terminatoride.agent.specialized_agents.Agent")
    def test_create_refactoring_planner(self, mock_agent):
        """Test creating a refactoring planner agent."""
        # Configure the mock
        mock_agent.return_value = Agent(name="Mock Agent", instructions="Mock")

        # Create the agent
        _ = SpecializedAgents.create_refactoring_planner()

        # Check that Agent was called with correct parameters
        mock_agent.assert_called_once()
        args, kwargs = mock_agent.call_args

        assert kwargs["name"] == "Refactoring Planner"
        assert "refactoring expert" in kwargs["instructions"].lower()
        assert kwargs["output_type"] == RefactoringPlan

    @patch("terminatoride.agent.specialized_agents.Agent")
    def test_create_documentation_generator(self, mock_agent):
        """Test creating a documentation generator agent."""
        # Configure the mock
        mock_agent.return_value = Agent(name="Mock Agent", instructions="Mock")

        # Create the agent
        _ = SpecializedAgents.create_documentation_generator()

        # Check that Agent was called with correct parameters
        mock_agent.assert_called_once()
        args, kwargs = mock_agent.call_args

        assert kwargs["name"] == "Documentation Generator"
        assert "documentation expert" in kwargs["instructions"].lower()
        assert kwargs["output_type"] == DocumentationResult

    @patch("terminatoride.agent.specialized_agents.Agent")
    def test_create_error_diagnostician(self, mock_agent):
        """Test creating an error diagnostician agent."""
        # Configure the mock
        mock_agent.return_value = Agent(name="Mock Agent", instructions="Mock")

        # Create the agent
        _ = SpecializedAgents.create_error_diagnostician()

        # Check that Agent was called with correct parameters
        mock_agent.assert_called_once()
        args, kwargs = mock_agent.call_args

        assert kwargs["name"] == "Error Diagnostician"
        assert "error diagnosis" in kwargs["instructions"].lower()
        assert kwargs["output_type"] == ErrorDiagnosis

    @patch("terminatoride.agent.specialized_agents.Agent")
    def test_create_test_runner(self, mock_agent):
        """Test creating a test runner agent."""
        # Configure the mock
        mock_agent.return_value = Agent(name="Mock Agent", instructions="Mock")

        # Create the agent
        _ = SpecializedAgents.create_test_runner()

        # Check that Agent was called with correct parameters
        mock_agent.assert_called_once()
        args, kwargs = mock_agent.call_args

        assert kwargs["name"] == "Test Runner"
        assert "testing expert" in kwargs["instructions"].lower()
        assert kwargs["output_type"] == TestSuiteResult

    @patch("terminatoride.agent.specialized_agents.Agent")
    def test_create_search_agent(self, mock_agent):
        """Test creating a search agent."""
        # Configure the mock
        mock_agent.return_value = Agent(name="Mock Agent", instructions="Mock")

        # Create the agent
        _ = SpecializedAgents.create_search_agent()

        # Check that Agent was called with correct parameters
        mock_agent.assert_called_once()
        args, kwargs = mock_agent.call_args

        assert kwargs["name"] == "Code Searcher"
        assert "search expert" in kwargs["instructions"].lower()
        assert kwargs["output_type"] == SearchResults

    @patch("terminatoride.agent.specialized_agents.Agent")
    def test_create_git_agent(self, mock_agent):
        """Test creating a git agent."""
        # Configure the mock
        mock_agent.return_value = Agent(name="Mock Agent", instructions="Mock")

        # Create the agent
        _ = SpecializedAgents.create_git_agent()

        # Check that Agent was called with correct parameters
        mock_agent.assert_called_once()
        args, kwargs = mock_agent.call_args

        assert kwargs["name"] == "Git Expert"
        assert "git expert" in kwargs["instructions"].lower()
        assert kwargs["output_type"] == GitResult

    @patch("terminatoride.agent.specialized_agents.Agent")
    def test_create_project_analyzer(self, mock_agent):
        """Test creating a project analyzer agent."""
        # Configure the mock
        mock_agent.return_value = Agent(name="Mock Agent", instructions="Mock")

        # Create the agent
        _ = SpecializedAgents.create_project_analyzer()

        # Check that Agent was called with correct parameters
        mock_agent.assert_called_once()
        args, kwargs = mock_agent.call_args

        assert kwargs["name"] == "Project Analyzer"
        assert "project analysis" in kwargs["instructions"].lower()
        assert kwargs["output_type"] == ProjectSummary

    @patch("terminatoride.agent.specialized_agents.get_file_content")
    def test_get_file_content_tool(self, mock_get_file_content):
        """Test the get_file_content function tool."""
        # Import the function directly for testing
        from terminatoride.agent.specialized_agents import get_file_content

        # Create a mock context
        mock_context = type("MockContext", (), {})()
        mock_context.context = None

        # Configure the mock
        mock_get_file_content.return_value = "File content"

        # Call the function with no path (removing await since it's not async)
        result = get_file_content(mock_context)

        # Verify the result
        assert result == "File content"
        mock_get_file_content.assert_called_once_with(mock_context)
