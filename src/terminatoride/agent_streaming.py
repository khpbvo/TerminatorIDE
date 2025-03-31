"""
Streaming implementation for the OpenAI Agent.
This module extends the OpenAI Agent with streaming capabilities.
"""

import logging
import os
from typing import Any, Callable, Dict, Optional

from agents import Runner

from terminatoride.agent.context import AgentContext
from terminatoride.agents.openai_agent import OpenAIAgent, get_openai_agent
from terminatoride.utils.error_handling import RateLimitHandler

# Set up detailed logging for debugging
logger = logging.getLogger("terminatoride.agent_streaming")

# Create a file handler for detailed logging
try:
    log_dir = os.path.join(os.path.expanduser("~"), ".terminatoride", "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Create file handler
    file_handler = logging.FileHandler(os.path.join(log_dir, "streaming_debug.log"))
    file_handler.setLevel(logging.DEBUG)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)

    # Add handler to logger
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    # Also log to console for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info("Streaming debug logging initialized")
except Exception as e:
    print(f"Error setting up logging: {e}")
    # Set up a basic console logger as fallback
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


# Type aliases for callback functions
TextDeltaCallback = Callable[[str], None]
ToolCallCallback = Callable[[Dict[str, Any]], None]
ToolResultCallback = Callable[[Dict[str, Any]], None]
HandoffCallback = Callable[[Dict[str, Any]], None]

# Add this at the module level (outside any function)
_STREAMING_AGENT_INSTANCE = None


class StreamingAgent:
    """Provides streaming capabilities for the OpenAI Agent."""

    def __init__(self, base_agent: Optional[OpenAIAgent] = None):
        """Initialize the streaming agent with a base agent.

        Args:
            base_agent: The base OpenAI agent to use. If None, a new one is created.
        """
        self.base_agent = (
            base_agent or get_openai_agent()
        )  # Changed from self.agent to self.base_agent
        self.rate_limiter = self.base_agent.rate_limiter or RateLimitHandler()

    async def generate_streaming_response(
        self,
        user_message: str,
        context: AgentContext,
        on_text_delta=None,
        on_tool_call=None,
        on_tool_result=None,
        on_handoff=None,
    ) -> str:
        """Generate a streaming response to the user query."""
        # Check if rate limiting allows the request
        if not self.base_agent.rate_limiter.can_make_request():
            wait_time = self.base_agent.rate_limiter.time_until_next_request()
            return f"Too many requests. Please try again in {wait_time:.1f} seconds."

        try:
            # Create a runner for our agent
            runner = Runner()

            # Get run context
            run_context = context if context is not None else AgentContext()

            # Use the default agent from base_agent
            agent = self.base_agent.default_agent

            # Execute the streaming run (using same pattern as in OpenAIAgent.generate_response)
            stream_result = runner.run_streamed(
                starting_agent=agent, input=user_message, context=run_context
            )

            # Process the streaming events
            final_response = ""
            async for event in stream_result.stream_events():
                # Alternative approach if you don't have access to the event classes
                if hasattr(event, "delta") and on_text_delta:
                    delta = event.delta
                    final_response += delta
                    await on_text_delta(delta)

                elif hasattr(event, "tool_name") and on_tool_call:
                    tool_info = {
                        "name": event.tool_name,
                        "input": getattr(event, "tool_input", ""),
                        "id": getattr(event, "tool_call_id", ""),
                    }
                    await on_tool_call(tool_info)

                elif (
                    hasattr(event, "output")
                    and hasattr(event, "tool_call_id")
                    and on_tool_result
                ):
                    result_info = {
                        "output": event.output,
                        "tool_call_id": event.tool_call_id,
                    }
                    await on_tool_result(result_info)

                elif (
                    hasattr(event, "from_agent_id")
                    and hasattr(event, "to_agent_id")
                    and on_handoff
                ):
                    handoff_info = {
                        "from_agent": event.from_agent_id,
                        "to_agent": event.to_agent_id,
                    }
                    await on_handoff(handoff_info)

            # Return the final output or accumulated response
            return stream_result.final_output or final_response

        except Exception as e:
            # Log and return error
            logger.error(f"Error in streaming response: {e}", exc_info=True)
            return f"Error processing request: {str(e)}"


def get_streaming_agent():
    """Get or create a streaming agent (singleton)."""
    global _STREAMING_AGENT_INSTANCE

    if _STREAMING_AGENT_INSTANCE is None:
        logger.info("Creating new streaming agent instance")
        # Initialize the agent
        _STREAMING_AGENT_INSTANCE = StreamingAgent()
    else:
        logger.info("Returning existing streaming agent instance")

    return _STREAMING_AGENT_INSTANCE


# Add this function to the module
def reset_streaming_agent_for_tests():
    """Reset the streaming agent singleton (for testing only)."""
    global _STREAMING_AGENT_INSTANCE
    _STREAMING_AGENT_INSTANCE = None
    logger.info("Reset streaming agent singleton for testing")
