"""
Specialized agents for TerminatorIDE using structured output types.
This module demonstrates how to create agents with Pydantic model outputs.
"""

from typing import Any, Optional

from agents import Agent, RunContextWrapper, function_tool

from terminatoride.agent.context import AgentContext
from terminatoride.agent.models import ModelSelector, ModelType
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


@function_tool
async def get_file_content(
    ctx: RunContextWrapper[Any], file_path: Optional[str] = None
) -> str:
    """
    Get the content of the current file or a specified file.

    Args:
        ctx: The run context wrapper
        file_path: Optional path to the file to get content from

    Returns:
        The content of the file
    """
    agent_context = ctx.context

    if isinstance(agent_context, AgentContext):
        if file_path and file_path != agent_context.current_file.path:
            # In a real implementation, you would read the file from disk
            return f"Content of {file_path} would be loaded here"
        elif agent_context.current_file:
            return agent_context.current_file.content

    return "No file content available"


class SpecializedAgents:
    """
    Factory for creating specialized agents with structured outputs.
    """

    @staticmethod
    def create_code_analyzer() -> Agent:
        """
        Create a code analyzer agent that uses CodeAnalysisResult as output.

        Returns:
            A configured agent for code analysis
        """
        return Agent(
            name="Code Analyzer",
            instructions="""
            You are a code analyzer for TerminatorIDE. Analyze code to identify:
            1. Potential bugs and issues
            2. Performance concerns
            3. Style violations
            4. Security vulnerabilities
            5. Architectural problems

            Provide a comprehensive analysis with line numbers, severity levels,
            and concrete suggestions for improvement.
            """,
            model=ModelSelector.get_model_string(ModelType.GPT4O),
            tools=[get_file_content],
            output_type=CodeAnalysisResult,
        )

    @staticmethod
    def create_refactoring_planner() -> Agent:
        """
        Create a refactoring planner agent that uses RefactoringPlan as output.

        Returns:
            A configured agent for planning code refactoring
        """
        return Agent(
            name="Refactoring Planner",
            instructions="""
            You are a refactoring expert for TerminatorIDE. When given code to refactor:
            1. Identify code smells and architectural issues
            2. Create a step-by-step refactoring plan
            3. Show the original and refactored code for each step
            4. Explain the rationale for each change
            5. Estimate the effort required

            Focus on maintainability, readability, and performance improvements.
            """,
            model=ModelSelector.get_model_string(ModelType.GPT4O),
            tools=[get_file_content],
            output_type=RefactoringPlan,
        )

    @staticmethod
    def create_documentation_generator() -> Agent:
        """
        Create a documentation generator agent that uses DocumentationResult as output.

        Returns:
            A configured agent for generating code documentation
        """
        return Agent(
            name="Documentation Generator",
            instructions="""
            You are a documentation expert for TerminatorIDE. Create comprehensive
            documentation for code, including:
            1. Classes, methods, and functions
            2. Parameters and return values
            3. Usage examples
            4. Edge cases and limitations

            Follow the documentation style appropriate for the language.
            Generate documentation that is clear, concise, and helpful.
            """,
            model=ModelSelector.get_model_string(ModelType.GPT4O),
            tools=[get_file_content],
            output_type=DocumentationResult,
        )

    @staticmethod
    def create_error_diagnostician() -> Agent:
        """
        Create an error diagnostician agent that uses ErrorDiagnosis as output.

        Returns:
            A configured agent for diagnosing code errors
        """
        return Agent(
            name="Error Diagnostician",
            instructions="""
            You are an error diagnosis expert for TerminatorIDE. When given code and an error:
            1. Identify the root cause of the error
            2. Explain the error in simple terms
            3. Provide specific solutions
            4. Suggest how to prevent similar errors

            Be thorough, educational, and provide concrete fixes.
            """,
            model=ModelSelector.get_model_string(ModelType.GPT4O),
            tools=[get_file_content],
            output_type=ErrorDiagnosis,
        )

    @staticmethod
    def create_test_runner() -> Agent:
        """
        Create a test runner agent that uses TestSuiteResult as output.

        Returns:
            A configured agent for running and analyzing tests
        """
        return Agent(
            name="Test Runner",
            instructions="""
            You are a testing expert for TerminatorIDE. When asked to run tests:
            1. Execute the requested tests
            2. Analyze the test results
            3. Report on successes and failures
            4. Suggest fixes for failing tests

            Provide a comprehensive test report with actionable insights.
            """,
            model=ModelSelector.get_model_string(ModelType.GPT4O),
            tools=[get_file_content],
            output_type=TestSuiteResult,
        )

    @staticmethod
    def create_search_agent() -> Agent:
        """
        Create a search agent that uses SearchResults as output.

        Returns:
            A configured agent for searching code
        """
        return Agent(
            name="Code Searcher",
            instructions="""
            You are a code search expert for TerminatorIDE. When given a search query:
            1. Find all occurrences matching the search criteria
            2. Show the context around each match
            3. Organize results by relevance
            4. Provide a summary of the findings

            Return comprehensive search results that help the user understand the codebase.
            """,
            model=ModelSelector.get_model_string(ModelType.GPT4O),
            tools=[get_file_content],
            output_type=SearchResults,
        )

    @staticmethod
    def create_git_agent() -> Agent:
        """
        Create a git agent that uses GitResult as output.

        Returns:
            A configured agent for git operations
        """
        return Agent(
            name="Git Expert",
            instructions="""
            You are a Git expert for TerminatorIDE. When asked to perform Git operations:
            1. Execute the requested Git command
            2. Interpret the results
            3. Explain what happened
            4. Suggest next steps if appropriate

            Provide clear, helpful information about Git operations.
            """,
            model=ModelSelector.get_model_string(ModelType.GPT4O),
            output_type=GitResult,
        )

    @staticmethod
    def create_project_analyzer() -> Agent:
        """
        Create a project analyzer agent that uses ProjectSummary as output.

        Returns:
            A configured agent for analyzing projects
        """
        return Agent(
            name="Project Analyzer",
            instructions="""
            You are a project analysis expert for TerminatorIDE. When analyzing a project:
            1. Assess the project structure
            2. Identify the languages and frameworks used
            3. Calculate metrics like file count and lines of code
            4. Evaluate the overall quality
            5. Provide recommendations for improvement

            Deliver a comprehensive project analysis with actionable insights.
            """,
            model=ModelSelector.get_model_string(ModelType.GPT4O),
            tools=[get_file_content],
            output_type=ProjectSummary,
        )
