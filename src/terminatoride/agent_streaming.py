"""
Streaming implementation for the OpenAI Agent.
This module extends the OpenAI Agent with streaming capabilities.
"""

import logging
from typing import Any, Callable, Dict, Optional

from agents import Runner

from terminatoride.agent.context import AgentContext
from terminatoride.agent.tracing import trace
from terminatoride.agents.openai_agent import OpenAIAgent, get_openai_agent
from terminatoride.utils.error_handling import RateLimitHandler

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
        self.agent = base_agent or get_openai_agent()
        self.rate_limiter = self.agent.rate_limiter or RateLimitHandler()

    async def generate_streaming_response(
        self,
        user_message: str,
        context: Optional[AgentContext] = None,
        on_text_delta: Optional[TextDeltaCallback] = None,
        on_tool_call: Optional[ToolCallCallback] = None,
        on_tool_result: Optional[ToolResultCallback] = None,
        on_handoff: Optional[HandoffCallback] = None,
    ) -> str:
        """Generate a streaming response to the user's message.

        Args:
            user_message: The user's input message
            context: Optional agent context with IDE state
            on_text_delta: Callback for text deltas
            on_tool_call: Callback for tool calls
            on_tool_result: Callback for tool results
            on_handoff: Callback for handoffs

        Returns:
            The complete final response after streaming
        """
        # Check rate limits before proceeding
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.time_until_next_request()
            if wait_time > 0:
                logger.warning(
                    f"Rate limit reached. Need to wait {wait_time:.2f} seconds"
                )
                return f"I'm receiving too many requests right now. Please try again in {wait_time:.1f} seconds."

        try:
            # Prepare context for the agent run
            run_context = context if context is not None else AgentContext()

            with trace("Streaming Agent Run"):
                # Use the streaming API from Agent SDK
                streaming_result = Runner.run_streamed(
                    starting_agent=self.agent.default_agent,
                    input=user_message,
                    context=run_context,
                )

                # Collect the full response as we stream
                full_response = ""

                # Process the streaming events
                async for event in streaming_result.stream_events():
                    if event.type == "raw_response_event":
                        # Handle text deltas for displaying token by token
                        # Instead of checking instance type, check for delta attribute
                        if hasattr(event.data, "delta") and event.data.delta:
                            if on_text_delta:
                                await on_text_delta(event.data.delta)
                                full_response += event.data.delta

                    elif event.type == "run_item_stream_event":
                        item = event.item
                        # Handle different item types
                        if item.type == "tool_call_item" and on_tool_call:
                            tool_info = {
                                "name": item.tool_name,
                                "arguments": item.tool_arguments,
                            }
                            await on_tool_call(tool_info)

                        elif item.type == "tool_call_output_item" and on_tool_result:
                            result_info = {
                                "output": item.output,
                                "tool_name": item.tool_name,
                            }
                            await on_tool_result(result_info)

                    elif event.type == "handoff_stream_event" and on_handoff:
                        # Handle handoffs between agents
                        handoff_info = {
                            "from_agent": (
                                event.source_agent.name
                                if event.source_agent
                                else "Unknown"
                            ),
                            "to_agent": (
                                event.target_agent.name
                                if event.target_agent
                                else "Unknown"
                            ),
                            "reason": "Specialized knowledge required",  # This could be extracted from the context
                        }
                        await on_handoff(handoff_info)

                # Return the complete response
                return full_response or streaming_result.final_output

        except Exception as e:
            logger.error(f"Error generating streaming response: {e}")
            return f"I encountered an error while processing your request: {str(e)}"


# Provide a singleton instance
_default_streaming_agent = None


def get_streaming_agent() -> StreamingAgent:
    """Get or create the default streaming agent instance."""
    global _default_streaming_agent
    if _default_streaming_agent is None:
        _default_streaming_agent = StreamingAgent()
    return _default_streaming_agent
