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
            raise Exception("Rate limit exceeded. Please try again later.")

        try:
            # Create context dict for the SDK
            context_dict = {}
            if hasattr(context, "user_query"):
                context_dict["user_query"] = context.user_query
            # Add other context fields as needed

            # Get streaming run result
            logger.info("Starting streaming request")
            run_result = Runner.run_streamed(
                self.base_agent.default_agent,
                input=user_message,
                context=context_dict,
            )

            # Track the final message content for return
            final_content = ""

            # Process streaming events
            try:
                async for event in run_result.stream_events():
                    # Log the event type for debugging
                    logger.debug(f"Received event type: {event.type}")

                    # Handle different event types
                    if event.type == "raw_response_event":
                        logger.debug(f"Raw response event received: {event}")
                        # Some events have a different structure
                        try:
                            if hasattr(event.data, "delta"):
                                delta = event.data.delta
                                if delta and on_text_delta:
                                    final_content += delta
                                    await on_text_delta(delta)
                            else:
                                logger.debug("No delta attribute found in event data")
                                # For the first event, extract initial text if available
                                if hasattr(event.data, "response") and hasattr(
                                    event.data.response, "text"
                                ):
                                    text = event.data.response.text
                                    if text and on_text_delta:
                                        await on_text_delta(text)
                                        final_content = text
                        except Exception as e:
                            logger.error(f"Error processing text delta: {e}")

                    # More event handling...
            except Exception as e:
                logger.error(f"Error processing streaming events: {e}")

            # Instead of awaiting run_result directly, use the content we've collected
            logger.info("Streaming complete, getting final result")

            # If we didn't get any content from streaming, try to get the final content
            if not final_content:
                try:
                    # Try to get the result through a different method
                    # Check if run_result has a get_result() method
                    if hasattr(run_result, "get_result"):
                        result = await run_result.get_result()
                        final_content = result.final_output
                    # If that fails, see if there's a result property
                    elif hasattr(run_result, "result"):
                        final_content = run_result.result
                    # Last resort - see if run_result itself has text content
                    elif hasattr(run_result, "final_output"):
                        final_content = run_result.final_output
                    else:
                        # We couldn't get any content
                        final_content = "Sorry, I couldn't generate a response."
                except Exception as e:
                    logger.error(f"Error getting final result: {e}")
                    final_content = f"Error completing response: {str(e)}"

            return final_content
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            return f"I encountered an error while processing your request: {str(e)}"


# Provide a singleton instance
_default_streaming_agent = None


def get_streaming_agent() -> StreamingAgent:
    """Get or create the default streaming agent instance."""
    global _default_streaming_agent
    if _default_streaming_agent is None:
        _default_streaming_agent = StreamingAgent()
    return _default_streaming_agent
