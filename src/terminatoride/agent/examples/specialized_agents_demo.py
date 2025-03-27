"""
Example implementation of specialized agents with handoff capabilities.
This module demonstrates how to create and use specialized agents in TerminatorIDE.
"""

import asyncio
import logging
from typing import Any, Dict, List

from agents import RunContextWrapper, function_tool, trace
from pydantic import BaseModel

from terminatoride.agent.agent_manager import AgentManager
from terminatoride.agent.handoff import HandoffManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define output types for specialized agents
class CodeAnalysisResult(BaseModel):
    """Structured output for code analysis."""

    language: str
    complexity: str  # "low", "medium", "high"
    issues: List[str]
    suggestions: List[str]


class RefactoringPlan(BaseModel):
    """Structured output for code refactoring plans."""

    steps: List[str]
    rationale: str
    estimated_effort: str  # "low", "medium", "high"


class DebuggingResult(BaseModel):
    """Structured output for debugging results."""

    identified_issues: List[str]
    root_cause: str
    fix_suggestions: List[str]


# Helper tools that can be used by multiple agents
@function_tool
async def analyze_code_syntax(
    ctx: RunContextWrapper[Any], code: str, language: str
) -> Dict[str, Any]:
    """
    Analyze code syntax for potential issues.

    Args:
        code: The code to analyze
        language: The programming language

    Returns:
        Dictionary with syntax analysis results
    """
    # In a real implementation, this would use static analysis tools
    return {
        "valid_syntax": True,
        "potential_issues": [
            "Unused variable 'x' at line 5",
            "Missing return type annotation",
        ],
        "language_detected": language,
    }


@function_tool
async def get_language_best_practices(
    ctx: RunContextWrapper[Any], language: str
) -> List[str]:
    """
    Get best practices for a programming language.

    Args:
        language: The programming language

    Returns:
        List of best practices
    """
    best_practices = {
        "python": [
            "Use type hints for better code clarity",
            "Follow PEP 8 style guidelines",
            "Use context managers for resource management",
            "Prefer composition over inheritance",
            "Use virtual environments for dependency management",
        ],
        "javascript": [
            "Use const and let instead of var",
            "Use async/await for asynchronous code",
            "Follow ESLint rules for consistent style",
            "Use destructuring for cleaner code",
            "Consider TypeScript for larger projects",
        ],
        "typescript": [
            "Use strict type checking",
            "Leverage interfaces for better type safety",
            "Use enums for related constants",
            "Consider using the nullish coalescing operator",
            "Use discriminated unions for type narrowing",
        ],
    }

    return best_practices.get(
        language.lower(), ["No specific best practices available for this language"]
    )


class SpecializedAgentsDemo:
    """
    Demonstrates how to create and use specialized agents with handoffs.
    """

    def __init__(self):
        """Initialize the specialized agents demo."""
        self.agent_manager = AgentManager(enable_tracing=True, verbose_logging=True)
        self._setup_specialized_agents()

    def _setup_specialized_agents(self):
        """Set up the specialized agents with their respective capabilities."""

        # Create specialized code analysis agents for different languages
        self.python_agent = self.agent_manager.create_specialized_agent(
            name="Python Expert",
            instructions=HandoffManager.with_recommended_prompt(
                """
            You are a Python code expert who specializes in analyzing Python code.
            When provided with Python code, you will:
            1. Identify potential issues, bugs, and inefficiencies
            2. Suggest improvements based on best practices and Python idioms
            3. Provide code examples for implementation
            4. Consider performance implications of the code

            Be specific and detailed in your analysis, but remain concise.
            """
            ),
            specialty="Python",
            output_type=CodeAnalysisResult,
        )

        self.javascript_agent = self.agent_manager.create_specialized_agent(
            name="JavaScript Expert",
            instructions=HandoffManager.with_recommended_prompt(
                """
            You are a JavaScript code expert who specializes in analyzing JavaScript code.
            When provided with JavaScript code, you will:
            1. Identify potential issues, bugs, and inefficiencies
            2. Suggest improvements based on modern JavaScript best practices
            3. Provide code examples for implementation
            4. Consider browser compatibility issues when relevant

            Be specific and detailed in your analysis, but remain concise.
            """
            ),
            specialty="JavaScript",
            output_type=CodeAnalysisResult,
        )

        # Create specialized refactoring agent
        self.refactoring_agent = self.agent_manager.create_specialized_agent(
            name="Code Refactoring Expert",
            instructions=HandoffManager.with_recommended_prompt(
                """
            You are a code refactoring expert who specializes in improving code structure.
            When provided with code and an analysis, you will:
            1. Create a step-by-step refactoring plan
            2. Prioritize changes by impact and difficulty
            3. Explain the rationale behind each refactoring step
            4. Estimate the effort required for implementation

            Focus on practical improvements that will have the greatest positive impact.
            """
            ),
            specialty="Refactoring",
            output_type=RefactoringPlan,
        )

        # Create specialized debugging agent
        self.debugging_agent = self.agent_manager.create_specialized_agent(
            name="Debugging Expert",
            instructions=HandoffManager.with_recommended_prompt(
                """
            You are a debugging expert who specializes in finding and fixing bugs.
            When provided with code and error messages, you will:
            1. Identify the root cause of the issues
            2. Explain why the bug is occurring
            3. Provide specific solutions to fix the problems
            4. Suggest ways to prevent similar bugs in the future

            Be methodical in your approach and explain your reasoning clearly.
            """
            ),
            specialty="Debugging",
            output_type=DebuggingResult,
            tools=[analyze_code_syntax],
        )

        # Create triage agent that coordinates between specialized agents
        self.triage_agent = self.agent_manager.create_triage_agent(
            name="Code Assistant",
            base_instructions="""
            You are a helpful code assistant that helps users with their code-related questions.
            You have access to specialized agents for different programming languages and tasks.
            When a user asks a question, identify what kind of help they need:

            1. If they need help with Python code, handoff to the Python Expert
            2. If they need help with JavaScript code, handoff to the JavaScript Expert
            3. If they need help refactoring code, handoff to the Code Refactoring Expert
            4. If they need help debugging an error, handoff to the Debugging Expert

            Only hand off when you're confident the specialized agent can better handle the request.
            For simple questions that don't require specialized expertise, you can answer directly.
            """,
        )

        # Set up handoff paths between agents
        self.agent_manager.create_handoff(
            source_agent=self.python_agent,
            target_agent=self.refactoring_agent,
            description="Handoff to the refactoring expert for code restructuring",
        )

        self.agent_manager.create_handoff(
            source_agent=self.javascript_agent,
            target_agent=self.refactoring_agent,
            description="Handoff to the refactoring expert for code restructuring",
        )

        # Set up escalation path for complex issues
        self.agent_manager.create_escalation_path(
            from_agent=self.debugging_agent,
            to_agent=self.triage_agent,
            reason_required=True,
        )

    async def run_demo(self, user_query: str) -> Any:
        """
        Run the demo with a user query.

        Args:
            user_query: The user's question or code to analyze

        Returns:
            The result from the agent interaction
        """
        with trace(workflow_name="Code Assistant Demo"):
            # Start with the triage agent
            result = await self.agent_manager.run_agent(
                agent=self.triage_agent, user_input=user_query
            )

            return result

    async def run_demo_with_streaming(self, user_query: str) -> None:
        """
        Run the demo with streaming outputs to showcase handoffs.

        Args:
            user_query: The user's question or code to analyze
        """

        # Define callbacks for streaming events
        def on_text_delta(delta: str):
            print(delta, end="", flush=True)

        def on_tool_call(tool_info: Dict[str, Any]):
            print(f"\n[TOOL CALL] {tool_info['name']}\n", flush=True)

        def on_tool_result(result_info: Dict[str, Any]):
            print(f"\n[TOOL RESULT] {result_info['output'][:50]}...\n", flush=True)

        def on_handoff(handoff_info: Dict[str, Any]):
            print(
                f"\n[HANDOFF] From {handoff_info['from_agent']} to {handoff_info['to_agent']}: {handoff_info['reason']}\n",
                flush=True,
            )

        with trace(workflow_name="Code Assistant Streaming Demo"):
            # Start with the triage agent and stream the results
            await self.agent_manager.run_agent_streamed(
                agent=self.triage_agent,
                user_input=user_query,
                on_text_delta=on_text_delta,
                on_tool_call=on_tool_call,
                on_tool_result=on_tool_result,
                on_handoff=on_handoff,
            )


# Example usage
async def main():
    demo = SpecializedAgentsDemo()

    # Example queries that should trigger different specialized agents
    python_query = """
    Can you help me improve this Python code?

    def calculate(x, y):
        if x > 0:
            result = x + y
        else:
            result = x - y
        return result
    """

    javascript_query = """
    Is there a better way to write this JavaScript code?

    function fetchData() {
        var data = null;
        var xhr = new XMLHttpRequest();
        xhr.open('GET', 'https://api.example.com/data');
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                data = JSON.parse(xhr.responseText);
                console.log(data);
            }
        };
        xhr.send();
        return data; // This will always return null!
    }
    """

    debug_query = """
    I'm getting this error in my Python code:
    TypeError: can't multiply sequence by non-int of type 'float'

    Here's my code:

    def multiply_list(lst, factor):
        return lst * factor

    result = multiply_list([1, 2, 3], 2.5)
    print(result)
    """

    print("=== PYTHON ANALYSIS DEMO ===")
    await demo.run_demo_with_streaming(python_query)

    print("\n\n=== JAVASCRIPT ANALYSIS DEMO ===")
    await demo.run_demo_with_streaming(javascript_query)

    print("\n\n=== DEBUGGING DEMO ===")
    await demo.run_demo_with_streaming(debug_query)


if __name__ == "__main__":
    asyncio.run(main())
