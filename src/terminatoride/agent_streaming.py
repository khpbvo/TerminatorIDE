"""
Streaming implementation for the OpenAI Agent.
This module extends the OpenAI Agent with streaming capabilities.
"""

import asyncio
import logging
import os
from typing import Any, Callable, Dict, Optional

from agents import Runner

from terminatoride.agent.context import AgentContext
from terminatoride.agents.openai_agent import OpenAIAgent, get_openai_agent
from terminatoride.utils.error_handling import RateLimitHandler

# Set up detailed logging for debugging
logger = logging.getLogger(__name__)

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
            # Create context dict for the SDK - handle None values
            context_dict = {}
            if hasattr(context, "user_query") and context.user_query is not None:
                context_dict["user_query"] = context.user_query

            # Add file context if available
            if context.current_file is not None:
                context_dict["file_content"] = context.current_file.content
                context_dict["file_path"] = context.current_file.path
                context_dict["language"] = context.current_file.language
            elif context.file_content is not None:
                context_dict["file_content"] = context.file_content
                context_dict["file_path"] = context.file_path
                context_dict["language"] = context.file_language

            # Helper function to safely call callbacks
            async def safe_call_callback(callback, *args, **kwargs):
                if callback is None:
                    return
                if asyncio.iscoroutinefunction(callback):
                    await callback(*args, **kwargs)
                else:
                    callback(*args, **kwargs)

            # Process streaming events
            runner = Runner()
            result = await runner.run_streamed(
                self.base_agent.agent,
                user_message,
                context=context_dict,
            )

            all_text = ""
            async for event in result.stream_events():
                if event.type == "raw_response_event" and hasattr(event.data, "delta"):
                    all_text += event.data.delta
                    await safe_call_callback(on_text_delta, event.data.delta)
                elif event.type == "run_item_stream_event":
                    if event.item.type == "tool_call_item":
                        tool_info = {
                            "name": event.item.tool_name,
                            "arguments": event.item.tool_arguments,
                        }
                        await safe_call_callback(on_tool_call, tool_info)
                    elif event.item.type == "tool_call_output_item":
                        result_info = {
                            "tool_name": event.item.tool_name,
                            "output": event.item.output,
                        }
                        await safe_call_callback(on_tool_result, result_info)
                elif event.type == "handoff_stream_event":
                    handoff_info = {
                        "from_agent": event.source_agent.name,
                        "to_agent": event.target_agent.name,
                        "reason": getattr(event, "reason", "No reason provided"),
                    }
                    await safe_call_callback(on_handoff, handoff_info)

            return all_text or result.final_output

        except Exception as e:
            # Log the specific exception for debugging
            import traceback

            print(f"Streaming error: {str(e)}")
            print(traceback.format_exc())
            return f"Error processing request: {str(e)}"


# Provide a singleton instance
_default_streaming_agent = None


def get_streaming_agent() -> StreamingAgent:
    """Get or create the default streaming agent instance."""
    global _default_streaming_agent
    if _default_streaming_agent is None:
        _default_streaming_agent = StreamingAgent()
    return _default_streaming_agent
