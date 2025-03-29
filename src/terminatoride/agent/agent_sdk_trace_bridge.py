"""
Bridge between OpenAI Agent SDK tracing and TerminatorIDE tracing.
This module connects Agent SDK trace events to our custom tracing system.
"""

import functools
import time
from typing import Callable, Optional, TypeVar

# Import only what's definitely available in the SDK
from agents import (
    agent_span,
    function_span,
    generation_span,
    guardrail_span,
    handoff_span,
    tracing,
)

from terminatoride.agent.tracing import trace
from terminatoride.utils.trace_logger import write_trace_event

T = TypeVar("T")


def wrap_sdk_span(span_func: Callable) -> Callable:
    """
    Decorator to wrap Agent SDK span functions with our custom tracing.

    Args:
        span_func: The Agent SDK span function to wrap

    Returns:
        Wrapped function that integrates with our tracing system
    """

    @functools.wraps(span_func)
    def wrapper(*args, **kwargs):
        # Extract span name from kwargs or use default
        span_name = kwargs.get("name", "SDK Span")

        # Extract metadata if available
        metadata = kwargs.get("metadata", {})

        # Create our custom trace that wraps the SDK span
        with trace(f"SDK: {span_name}", metadata):
            # Execute the original SDK span
            return span_func(*args, **kwargs)

    return wrapper


# Wrap the standard Agent SDK span functions with our custom tracing
agent_span_traced = wrap_sdk_span(agent_span)
generation_span_traced = wrap_sdk_span(generation_span)
function_span_traced = wrap_sdk_span(function_span)
handoff_span_traced = wrap_sdk_span(handoff_span)
guardrail_span_traced = wrap_sdk_span(guardrail_span)


def trace_agent_run(agent_name: str, model: Optional[str] = None) -> Callable:
    """
    Decorator to trace agent runs.

    Args:
        agent_name: Name of the agent
        model: Optional model name

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            metadata = {
                "agent_name": agent_name,
                "model": model,
            }

            with trace(f"Agent Run: {agent_name}", metadata):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    # Extract useful metrics from result if available
                    if hasattr(result, "raw_responses") and result.raw_responses:
                        for resp in result.raw_responses:
                            if hasattr(resp, "usage") and resp.usage:
                                metadata.update(
                                    {
                                        "prompt_tokens": resp.usage.prompt_tokens,
                                        "completion_tokens": resp.usage.completion_tokens,
                                        "total_tokens": resp.usage.total_tokens,
                                    }
                                )
                    return result
                except Exception as e:
                    metadata["error"] = str(e)
                    raise
                finally:
                    duration_ms = int((time.time() - start_time) * 1000)
                    metadata["duration_ms"] = duration_ms

        return wrapper

    return decorator


def configure_sdk_tracing() -> None:
    """
    Configure the Agent SDK to use our custom tracing.
    This should be called during application initialization.
    """
    # Since we're not sure if we can set_default_trace_processors, we'll
    # just monkey-patch the span functions which will work regardless
    # Try to keep original references
    # Try to replace with our wrapped versions
    # Use try/except for each one in case the structure is different
    try:
        tracing.agent_span = agent_span_traced
    except AttributeError:
        pass

    try:
        tracing.generation_span = generation_span_traced
    except AttributeError:
        pass

    try:
        tracing.function_span = function_span_traced
    except AttributeError:
        pass

    try:
        tracing.handoff_span = handoff_span_traced
    except AttributeError:
        pass

    try:
        tracing.guardrail_span = guardrail_span_traced
    except AttributeError:
        pass

    # Log that we've configured tracing
    write_trace_event(
        {
            "workflow": "SDK Tracing Integration",
            "metadata": {"status": "initialized"},
            "status": "success",
            "duration_ms": 0,
        }
    )
