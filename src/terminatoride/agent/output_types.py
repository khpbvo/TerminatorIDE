"""
Structured output types for TerminatorIDE agents.
These Pydantic models define the structure of agent outputs for different tasks.

Usage:
    from terminatoride.agent.output_types import CodeAnalysisResult

    # Create an agent with a structured output type
    code_analysis_agent = Agent(
        name="Code Analyzer",
        instructions="Analyze code for issues and suggestions",
        output_type=CodeAnalysisResult,
        tools=[...]
    )

    # The result will be a structured CodeAnalysisResult object
    result = await Runner.run(code_analysis_agent, "Analyze this code: ...")
    analysis = result.final_output  # This will be a CodeAnalysisResult object

    # Access structured data
    print(f"Found {len(analysis.issues)} issues")
    for issue in analysis.issues:
        print(f"Line {issue.line_number}: {issue.message} ({issue.severity})")
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    """Severity level for issues and suggestions."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class CodeIssue(BaseModel):
    """A code issue identified in the analysis."""

    line_number: int = Field(description="Line number where the issue occurs")
    column: Optional[int] = Field(
        None, description="Column number where the issue occurs"
    )
    message: str = Field(description="Description of the issue")
    severity: SeverityLevel = Field(description="Severity level of the issue")
    suggestion: Optional[str] = Field(None, description="Suggested fix for the issue")


class CodeSuggestion(BaseModel):
    """A suggestion for improving code."""

    line_number: Optional[int] = Field(
        None, description="Line number for the suggestion"
    )
    original_code: Optional[str] = Field(None, description="Original code snippet")
    suggested_code: str = Field(description="Suggested code replacement")
    explanation: str = Field(description="Explanation of the suggestion")
    impact: str = Field(description="Expected impact of applying the suggestion")


class FileMetrics(BaseModel):
    """Metrics for a file."""

    lines_of_code: int = Field(
        description="Total lines of code (excluding blank lines and comments)"
    )
    comment_lines: int = Field(description="Number of comment lines")
    blank_lines: int = Field(description="Number of blank lines")
    function_count: int = Field(description="Number of functions/methods")
    class_count: Optional[int] = Field(None, description="Number of classes")
    complexity: Optional[float] = Field(None, description="Cyclomatic complexity score")


class CodeAnalysisResult(BaseModel):
    """Result of a code analysis operation."""

    language: str = Field(description="Programming language of the analyzed code")
    issues: List[CodeIssue] = Field(description="List of identified issues")
    suggestions: List[CodeSuggestion] = Field(
        description="List of code improvement suggestions"
    )
    metrics: Optional[FileMetrics] = Field(
        None, description="Code metrics if available"
    )
    summary: str = Field(description="Summary of the analysis results")


class RefactoringStep(BaseModel):
    """A single step in a refactoring plan."""

    step_number: int = Field(description="Order number of this step")
    description: str = Field(description="Description of what this step accomplishes")
    original_code: Optional[str] = Field(
        None, description="Original code to be refactored"
    )
    refactored_code: str = Field(description="Refactored code")
    file_path: Optional[str] = Field(None, description="File path if applicable")
    line_range: Optional[List[int]] = Field(
        None, description="Line range [start, end] if applicable"
    )


class RefactoringPlan(BaseModel):
    """A structured refactoring plan."""

    title: str = Field(description="Title summarizing the refactoring")
    rationale: str = Field(
        description="Explanation of why this refactoring is beneficial"
    )
    steps: List[RefactoringStep] = Field(
        description="Ordered steps to perform the refactoring"
    )
    estimated_effort: str = Field(
        description="Estimated effort (e.g., 'low', 'medium', 'high')"
    )
    prerequisites: Optional[List[str]] = Field(
        None, description="Prerequisites before starting refactoring"
    )
    expected_benefits: List[str] = Field(
        description="Expected benefits after applying the refactoring"
    )


class DocumentationElement(BaseModel):
    """A documentation element for a code component."""

    element_type: str = Field(
        description="Type of element (class, method, function, etc.)"
    )
    name: str = Field(description="Name of the element")
    description: str = Field(description="Description of the element")
    parameters: Optional[List[Dict[str, str]]] = Field(
        None, description="Parameters (name, type, description)"
    )
    returns: Optional[Dict[str, str]] = Field(
        None, description="Return value (type, description)"
    )
    examples: Optional[List[str]] = Field(None, description="Usage examples")
    notes: Optional[List[str]] = Field(None, description="Additional notes")


class DocumentationResult(BaseModel):
    """Generated documentation for code."""

    file_path: str = Field(description="Path to the documented file")
    language: str = Field(description="Programming language")
    elements: List[DocumentationElement] = Field(description="Documented elements")
    summary: str = Field(description="Overall summary of the file")
    markdown: str = Field(description="Complete markdown documentation")


class ErrorSource(str, Enum):
    """Source of an error in the code."""

    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    RUNTIME = "runtime"
    LOGIC = "logic"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


class ErrorDiagnosis(BaseModel):
    """Diagnosis of an error in code."""

    error_message: str = Field(description="Original error message")
    error_type: str = Field(description="Type of the error")
    source: ErrorSource = Field(description="Source of the error")
    line_number: Optional[int] = Field(
        None, description="Line number where the error occurs"
    )
    problematic_code: Optional[str] = Field(
        None, description="The problematic code snippet"
    )
    explanation: str = Field(description="Explanation of the error in simple terms")
    fix_suggestions: List[str] = Field(description="Suggestions to fix the error")
    prevention_tips: Optional[List[str]] = Field(
        None, description="Tips to prevent similar errors"
    )


class ExecutionTestResult(BaseModel):
    """Result of a test case."""

    test_name: str = Field(description="Name of the test")
    passed: bool = Field(description="Whether the test passed")
    error_message: Optional[str] = Field(
        None, description="Error message if test failed"
    )
    execution_time: Optional[float] = Field(
        None, description="Execution time in seconds"
    )


class ExecutionTestSuiteResult(BaseModel):
    """Results of running a test suite."""

    total_tests: int = Field(description="Total number of tests run")
    passed_tests: int = Field(description="Number of tests that passed")
    failed_tests: int = Field(description="Number of tests that failed")
    skipped_tests: Optional[int] = Field(
        None, description="Number of tests that were skipped"
    )
    execution_time: float = Field(description="Total execution time in seconds")
    test_results: List[ExecutionTestResult] = Field(
        description="Individual test results"
    )
    summary: str = Field(description="Summary of the test results")


class SearchResult(BaseModel):
    """A single search result."""

    file_path: str = Field(description="Path to the file containing the match")
    line_number: int = Field(description="Line number of the match")
    context: str = Field(description="Code context around the match")
    match: str = Field(description="The matching text")


class SearchResults(BaseModel):
    """Results of a search operation."""

    query: str = Field(description="Search query")
    total_matches: int = Field(description="Total number of matches found")
    results: List[SearchResult] = Field(description="List of search results")
    summary: Optional[str] = Field(None, description="Summary of the search results")


class GitOperation(str, Enum):
    """Git operations that can be performed."""

    COMMIT = "commit"
    PUSH = "push"
    PULL = "pull"
    BRANCH = "branch"
    MERGE = "merge"
    CHECKOUT = "checkout"
    STATUS = "status"


class GitResult(BaseModel):
    """Result of a Git operation."""

    operation: GitOperation = Field(description="The Git operation that was performed")
    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="Output message from Git")
    error: Optional[str] = Field(
        None, description="Error message if the operation failed"
    )
    action_items: Optional[List[str]] = Field(None, description="Suggested next steps")


class ProjectSummary(BaseModel):
    """Summary of a project analysis."""

    project_name: str = Field(description="Name of the project")
    file_count: int = Field(description="Total number of files")
    total_lines: int = Field(description="Total lines of code")
    languages: Dict[str, int] = Field(
        description="Languages used (language name to line count)"
    )
    dependencies: Optional[List[str]] = Field(None, description="Project dependencies")
    structure_quality: Optional[str] = Field(
        None, description="Assessment of project structure quality"
    )
    recommendations: List[str] = Field(description="Recommendations for improvement")
    summary: str = Field(description="Overall project summary")
