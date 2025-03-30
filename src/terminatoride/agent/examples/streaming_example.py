"""
Example demonstrating how to use the streaming capabilities of TerminatorIDE.
"""

import asyncio
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from terminatoride.agent.context import AgentContext, FileContext
from terminatoride.agent_streaming import get_streaming_agent


async def handle_text_delta(delta: str):
    """Handle streaming text deltas."""
    print(delta, end="", flush=True)


async def handle_tool_call(tool_info: dict):
    """Handle tool call events."""
    print(f"\n\n[TOOL CALL] {tool_info['name']}\n", flush=True)


async def handle_tool_result(result_info: dict):
    """Handle tool result events."""
    print(f"\n\n[TOOL RESULT] {result_info['output'][:50]}...\n", flush=True)


async def handle_handoff(handoff_info: dict):
    """Handle handoff events."""
    print(
        f"\n\n[HANDOFF] From {handoff_info['from_agent']} to {handoff_info['to_agent']}\n",
        flush=True,
    )


async def main():
    """Run the streaming example."""
    # Create a streaming agent
    streaming_agent = get_streaming_agent()

    # Create a context with a sample file
    context = AgentContext()
    file_context = FileContext(
        path="/example/example.py",
        content="""
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n-1)

print(factorial(5))
""",
        language="python",
    )
    context.update_current_file(file_context.path, file_context.content)

    # Example prompts to demonstrate streaming
    prompts = [
        "Explain this factorial function to me.",
        "What would happen if I called factorial with a negative number?",
        "Can you suggest an improvement to handle negative numbers gracefully?",
    ]

    for i, prompt in enumerate(prompts):
        print(f"\n\n--- Example {i+1}: {prompt} ---\n")
        print("YOU: ", prompt, "\n")
        print("ASSISTANT: ", end="", flush=True)

        # Use streaming to get response
        await streaming_agent.generate_streaming_response(
            prompt,
            context,
            on_text_delta=handle_text_delta,
            on_tool_call=handle_tool_call,
            on_tool_result=handle_tool_result,
            on_handoff=handle_handoff,
        )

        print("\n\n" + "=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
