"""
Simple test script to diagnose streaming issues.
"""

import asyncio
import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from terminatoride.agent.context import AgentContext
from terminatoride.agent_streaming import get_streaming_agent


async def handle_text_delta(delta: str):
    """Handle streaming text deltas."""
    print(f"TEXT: {delta}", end="", flush=True)


async def handle_tool_call(tool_info: dict):
    """Handle tool call events."""
    print(f"\n\n[TOOL CALL] {tool_info}\n", flush=True)


async def handle_tool_result(result_info: dict):
    """Handle tool result events."""
    print(f"\n\n[TOOL RESULT] {result_info}\n", flush=True)


async def handle_handoff(handoff_info: dict):
    """Handle handoff events."""
    print(
        f"\n\n[HANDOFF] {handoff_info}\n",
        flush=True,
    )


async def main():
    """Run the streaming test."""
    print("Starting streaming test...")

    # Create a streaming agent
    streaming_agent = get_streaming_agent()
    print("Agent created")

    # Create a context with a sample file
    context = AgentContext()
    print("Context created")

    # Test prompt
    prompt = "Hello, introduce yourself in 2-3 sentences."
    print(f"Test prompt: {prompt}")

    try:
        print("Starting streaming request...")
        result = await streaming_agent.generate_streaming_response(
            prompt,
            context,
            on_text_delta=handle_text_delta,
            on_tool_call=handle_tool_call,
            on_tool_result=handle_tool_result,
            on_handoff=handle_handoff,
        )
        print(f"\n\nFinal result: {result}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
