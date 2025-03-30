"""
Tests for output_types.py Pydantic models.
"""

import json

import pytest
from pydantic import ValidationError

from terminatoride.agent.output_types import (
    CodeAnalysisResult,
    CodeIssue,
    CodeSuggestion,
    DocumentationElement,
    DocumentationResult,
    ErrorDiagnosis,
    ErrorSource,
    FileMetrics,
    GitOperation,
    GitResult,
    ProjectSummary,
    RefactoringPlan,
    RefactoringStep,
    SearchResult,
    SearchResults,
    SeverityLevel,
    TestResult,
    TestSuiteResult,
)


class TestOutputTypes:
    """Test the Pydantic output type models."""

    def test_code_issue_model(self):
        """Test the CodeIssue model."""
        # Test valid initialization
        issue = CodeIssue(
            line_number=10,
            message="Unused variable",
            severity=SeverityLevel.WARNING,
        )
        assert issue.line_number == 10
        assert issue.message == "Unused variable"
        assert issue.severity == SeverityLevel.WARNING
        assert issue.column is None
        assert issue.suggestion is None

        # Test with all fields
        issue = CodeIssue(
            line_number=15,
            column=5,
            message="Function too complex",
            severity=SeverityLevel.ERROR,
            suggestion="Consider breaking into smaller functions",
        )
        assert issue.line_number == 15
        assert issue.column == 5
        assert issue.message == "Function too complex"
        assert issue.severity == SeverityLevel.ERROR
        assert issue.suggestion == "Consider breaking into smaller functions"

        # Test invalid severity level
        with pytest.raises(ValidationError):
            CodeIssue(
                line_number=10,
                message="Test message",
                severity="not_a_valid_level",
            )

        # Test missing required field
        with pytest.raises(ValidationError):
            CodeIssue(
                line_number=10,
                # Missing 'message' field
                severity=SeverityLevel.INFO,
            )

    def test_code_suggestion_model(self):
        """Test the CodeSuggestion model."""
        # Test valid initialization
        suggestion = CodeSuggestion(
            suggested_code="def new_function():",
            explanation="Use a function for this logic",
            impact="Improves code organization",
        )
        assert suggestion.suggested_code == "def new_function():"
        assert suggestion.explanation == "Use a function for this logic"
        assert suggestion.impact == "Improves code organization"
        assert suggestion.line_number is None
        assert suggestion.original_code is None

        # Test with all fields
        suggestion = CodeSuggestion(
            line_number=25,
            original_code="x = x + 1",
            suggested_code="x += 1",
            explanation="Use augmented assignment",
            impact="Slightly more concise code",
        )
        assert suggestion.line_number == 25
        assert suggestion.original_code == "x = x + 1"
        assert suggestion.suggested_code == "x += 1"

        # Test missing required field
        with pytest.raises(ValidationError):
            CodeSuggestion(
                suggested_code="x += 1",
                # Missing 'explanation'
                impact="Makes code better",
            )

    def test_code_analysis_result_model(self):
        """Test the CodeAnalysisResult model."""
        # Create component objects
        issue = CodeIssue(
            line_number=10,
            message="Unused variable",
            severity=SeverityLevel.WARNING,
        )
        suggestion = CodeSuggestion(
            suggested_code="def new_function():",
            explanation="Use a function for this logic",
            impact="Improves code organization",
        )
        metrics = FileMetrics(
            lines_of_code=100,
            comment_lines=20,
            blank_lines=15,
            function_count=5,
        )

        # Test valid initialization
        analysis = CodeAnalysisResult(
            language="python",
            issues=[issue],
            suggestions=[suggestion],
            metrics=metrics,
            summary="Code is generally well-structured",
        )
        assert analysis.language == "python"
        assert len(analysis.issues) == 1
        assert analysis.issues[0].line_number == 10
        assert len(analysis.suggestions) == 1
        assert analysis.metrics.lines_of_code == 100
        assert analysis.summary == "Code is generally well-structured"

        # Test with minimal required fields
        analysis = CodeAnalysisResult(
            language="javascript",
            issues=[],
            suggestions=[],
            summary="No issues found",
        )
        assert analysis.language == "javascript"
        assert len(analysis.issues) == 0
        assert len(analysis.suggestions) == 0
        assert analysis.metrics is None

        # Test serialization to JSON
        json_str = analysis.model_dump_json()
        data = json.loads(json_str)
        assert data["language"] == "javascript"
        assert len(data["issues"]) == 0
        assert len(data["suggestions"]) == 0
        assert "metrics" in data
        assert data["metrics"] is None

    def test_refactoring_plan_model(self):
        """Test the RefactoringPlan model."""
        # Create a refactoring step
        step = RefactoringStep(
            step_number=1,
            description="Extract method",
            original_code="if x > 0: print(x)",
            refactored_code="def print_if_positive(x):\n    if x > 0: print(x)",
            line_range=[5, 7],
        )

        # Test valid initialization
        plan = RefactoringPlan(
            title="Refactor calculator class",
            rationale="Improve readability and maintainability",
            steps=[step],
            estimated_effort="medium",
            expected_benefits=["Better maintainability", "Less code duplication"],
        )
        assert plan.title == "Refactor calculator class"
        assert plan.rationale == "Improve readability and maintainability"
        assert len(plan.steps) == 1
        assert plan.steps[0].step_number == 1
        assert plan.estimated_effort == "medium"
        assert len(plan.expected_benefits) == 2
        assert plan.prerequisites is None

        # Test with prerequisites
        plan = RefactoringPlan(
            title="Refactor API module",
            rationale="Reduce coupling",
            steps=[step],
            estimated_effort="high",
            prerequisites=["Update dependencies", "Run tests"],
            expected_benefits=["Better maintainability"],
        )
        assert len(plan.prerequisites) == 2
        assert plan.prerequisites[0] == "Update dependencies"

    def test_documentation_result_model(self):
        """Test the DocumentationResult model."""
        # Create a documentation element
        element = DocumentationElement(
            element_type="function",
            name="calculate_sum",
            description="Calculates the sum of two numbers",
            parameters=[{"name": "a", "type": "int", "description": "First number"}],
            returns={"type": "int", "description": "The sum of a and b"},
        )

        # Test valid initialization
        doc_result = DocumentationResult(
            file_path="/path/to/math.py",
            language="python",
            elements=[element],
            summary="Math utility functions",
            markdown="# Math Module\n\nMath utility functions",
        )
        assert doc_result.file_path == "/path/to/math.py"
        assert doc_result.language == "python"
        assert len(doc_result.elements) == 1
        assert doc_result.elements[0].element_type == "function"
        assert doc_result.summary == "Math utility functions"
        assert "# Math Module" in doc_result.markdown

    def test_error_diagnosis_model(self):
        """Test the ErrorDiagnosis model."""
        # Test valid initialization
        diagnosis = ErrorDiagnosis(
            error_message="TypeError: cannot concatenate 'str' and 'int' objects",
            error_type="TypeError",
            source=ErrorSource.RUNTIME,
            explanation="You're trying to add a string and a number",
            fix_suggestions=[
                "Convert the integer to string",
                "Convert the string to integer",
            ],
        )
        assert (
            diagnosis.error_message
            == "TypeError: cannot concatenate 'str' and 'int' objects"
        )
        assert diagnosis.error_type == "TypeError"
        assert diagnosis.source == ErrorSource.RUNTIME
        assert diagnosis.line_number is None
        assert "add a string and a number" in diagnosis.explanation
        assert len(diagnosis.fix_suggestions) == 2
        assert diagnosis.prevention_tips is None

        # Test with all fields
        diagnosis = ErrorDiagnosis(
            error_message="IndentationError: unexpected indent",
            error_type="IndentationError",
            source=ErrorSource.SYNTAX,
            line_number=42,
            problematic_code="    x = 10",
            explanation="There's an unexpected indentation",
            fix_suggestions=["Remove the indentation"],
            prevention_tips=["Use a consistent indentation style"],
        )
        assert diagnosis.line_number == 42
        assert diagnosis.problematic_code == "    x = 10"
        assert len(diagnosis.prevention_tips) == 1

    def test_test_suite_result_model(self):
        """Test the TestSuiteResult model."""
        # Create test results
        test1 = TestResult(
            test_name="test_addition",
            passed=True,
            execution_time=0.05,
        )
        test2 = TestResult(
            test_name="test_division",
            passed=False,
            error_message="AssertionError: expected 2.5 but got 2",
            execution_time=0.03,
        )

        # Test valid initialization
        suite_result = TestSuiteResult(
            total_tests=2,
            passed_tests=1,
            failed_tests=1,
            execution_time=0.08,
            test_results=[test1, test2],
            summary="1 of 2 tests passed",
        )
        assert suite_result.total_tests == 2
        assert suite_result.passed_tests == 1
        assert suite_result.failed_tests == 1
        assert suite_result.skipped_tests is None
        assert suite_result.execution_time == 0.08
        assert len(suite_result.test_results) == 2
        assert suite_result.test_results[0].passed is True
        assert suite_result.test_results[1].passed is False
        assert suite_result.summary == "1 of 2 tests passed"

    def test_search_results_model(self):
        """Test the SearchResults model."""
        # Create search results
        result1 = SearchResult(
            file_path="/path/to/file1.py",
            line_number=10,
            context="def calculate_sum(a, b):\n    return a + b",
            match="calculate_sum",
        )
        result2 = SearchResult(
            file_path="/path/to/file2.py",
            line_number=25,
            context="sum_result = calculate_sum(x, y)",
            match="calculate_sum",
        )

        # Test valid initialization
        search_results = SearchResults(
            query="calculate_sum",
            total_matches=2,
            results=[result1, result2],
            summary="Found 2 matches in 2 files",
        )
        assert search_results.query == "calculate_sum"
        assert search_results.total_matches == 2
        assert len(search_results.results) == 2
        assert search_results.results[0].file_path == "/path/to/file1.py"
        assert search_results.results[1].line_number == 25
        assert search_results.summary == "Found 2 matches in 2 files"

    def test_git_result_model(self):
        """Test the GitResult model."""
        # Test valid initialization
        git_result = GitResult(
            operation=GitOperation.COMMIT,
            success=True,
            message="2 files changed, 10 insertions(+), 5 deletions(-)",
        )
        assert git_result.operation == GitOperation.COMMIT
        assert git_result.success is True
        assert "2 files changed" in git_result.message
        assert git_result.error is None
        assert git_result.action_items is None

        # Test with error
        git_result = GitResult(
            operation=GitOperation.PUSH,
            success=False,
            message="Failed to push to remote",
            error="Network error",
            action_items=["Check your internet connection", "Try again later"],
        )
        assert git_result.operation == GitOperation.PUSH
        assert git_result.success is False
        assert git_result.error == "Network error"
        assert len(git_result.action_items) == 2

        # Test invalid operation
        with pytest.raises(ValidationError):
            GitResult(
                operation="NOT_A_VALID_OPERATION",
                success=True,
                message="Test message",
            )

    def test_project_summary_model(self):
        """Test the ProjectSummary model."""
        # Test valid initialization
        summary = ProjectSummary(
            project_name="TerminatorIDE",
            file_count=42,
            total_lines=1000,
            languages={"python": 800, "javascript": 200},
            recommendations=["Add more tests", "Update documentation"],
            summary="A well-structured project with some areas for improvement",
        )
        assert summary.project_name == "TerminatorIDE"
        assert summary.file_count == 42
        assert summary.total_lines == 1000
        assert summary.languages["python"] == 800
        assert summary.dependencies is None
        assert len(summary.recommendations) == 2
        assert "well-structured" in summary.summary

        # Test with all fields
        summary = ProjectSummary(
            project_name="TerminatorIDE",
            file_count=42,
            total_lines=1000,
            languages={"python": 800, "javascript": 200},
            dependencies=["textual", "openai-agents"],
            structure_quality="good",
            recommendations=["Add more tests"],
            summary="A well-structured project",
        )
        assert len(summary.dependencies) == 2
        assert summary.structure_quality == "good"
