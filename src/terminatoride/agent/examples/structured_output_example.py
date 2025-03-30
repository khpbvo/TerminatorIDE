"""
Example script demonstrating the use of structured output types with agents.
"""

import asyncio
import json
import os

from dotenv import load_dotenv

from terminatoride.agent.agent_manager import AgentManager
from terminatoride.agent.context import AgentContext, FileContext
from terminatoride.agent.specialized_agents import SpecializedAgents


async def run_example():
    """Run the example script."""
    # Load environment variables
    load_dotenv()

    # Ensure we have an API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print(
            "Error: No OpenAI API key found. Set the OPENAI_API_KEY environment variable."
        )
        return

    # Initialize agent manager
    agent_manager = AgentManager(verbose_logging=True)

    # Sample Python code to analyze
    sample_code = """
def calculate_factorial(n):
    result = 1
    for i in range(1, n + 1):
        result = result * i
    return result

def is_prime(num):
    if num < 2:
        return False
    for i in range(2, num):
        if num % i == 0:
            return False
    return True

# Test the functions
print(calculate_factorial(5))
print(is_prime(7))
print(is_prime(10))
"""

    # Create a file context with the sample code
    file_context = FileContext(
        path="/example/math_utils.py",
        content=sample_code,
        language="python",
    )

    # Create agent context
    context = AgentContext()
    context.update_current_file(file_context.path, file_context.content)

    print("=" * 80)
    print("Running Code Analysis with structured output")
    print("=" * 80)

    # Create a code analyzer agent
    code_analyzer = SpecializedAgents.create_code_analyzer()

    # Run the code analyzer
    result = await agent_manager.run_agent(
        agent=code_analyzer,
        user_input="Analyze this Python code for issues and suggest improvements.",
        context=context,
    )

    # The result is now a CodeAnalysisResult object
    analysis = result.final_output

    # Display the structured output
    print(f"\nAnalysis Summary: {analysis.summary}")
    print(f"Language: {analysis.language}")
    print(f"Found {len(analysis.issues)} issues:")

    for issue in analysis.issues:
        print(f"  Line {issue.line_number}: {issue.message} ({issue.severity})")

    print(f"\nSuggestions ({len(analysis.suggestions)}):")
    for i, suggestion in enumerate(analysis.suggestions):
        print(f"  {i+1}. {suggestion.explanation}")
        if suggestion.original_code and suggestion.suggested_code:
            print(f"     From: {suggestion.original_code.strip()}")
            print(f"     To:   {suggestion.suggested_code.strip()}")

    print("\n" + "=" * 80)
    print("Running Refactoring Planner with structured output")
    print("=" * 80)

    # Create a refactoring planner agent
    refactoring_planner = SpecializedAgents.create_refactoring_planner()

    # Run the refactoring planner
    result = await agent_manager.run_agent(
        agent=refactoring_planner,
        user_input="Create a refactoring plan to improve this code.",
        context=context,
    )

    # The result is now a RefactoringPlan object
    plan = result.final_output

    # Display the structured output
    print(f"\nRefactoring Plan: {plan.title}")
    print(f"Rationale: {plan.rationale}")
    print(f"Estimated Effort: {plan.estimated_effort}")

    print("\nSteps:")
    for step in plan.steps:
        print(f"  Step {step.step_number}: {step.description}")
        if step.original_code and step.refactored_code:
            print(f"    From:\n{step.original_code.strip()}")
            print(f"    To:\n{step.refactored_code.strip()}")

    print("\nExpected Benefits:")
    for benefit in plan.expected_benefits:
        print(f"  - {benefit}")

    # Example of serializing to JSON
    print("\nJSON Serialization Example:")
    # Convert to dict and then to JSON string
    json_str = json.dumps(analysis.model_dump(), indent=2)
    # Print the first 500 characters to avoid overwhelming output
    print(json_str[:500] + "...")


if __name__ == "__main__":
    asyncio.run(run_example())
