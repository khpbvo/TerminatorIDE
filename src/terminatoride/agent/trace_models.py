"""
Pydantic models for trace events in TerminatorIDE.
These models define the structure of different types of trace events that can be logged.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field


class TraceEventType(str, Enum):
    """Types of trace events that can be logged."""

    WORKFLOW = "workflow"
    AGENT = "agent"
    LLM_GENERATION = "llm_generation"
    TOOL_CALL = "tool_call"
    HANDOFF = "handoff"
    GUARDRAIL = "guardrail"
    CUSTOM = "custom"


class TraceStatus(str, Enum):
    """Status values for trace events."""

    SUCCESS = "success"
    ERROR = "error"
    PENDING = "pending"
    CANCELLED = "cancelled"


class BaseTraceEvent(BaseModel):
    """Base model for all trace events."""

    event_type: TraceEventType
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    duration_ms: int
    status: TraceStatus
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowTraceEvent(BaseTraceEvent):
    """Trace event for high-level workflows."""

    event_type: TraceEventType = TraceEventType.WORKFLOW
    workflow: str
    group_id: Optional[str] = None
    trace_id: Optional[str] = None


class AgentTraceEvent(BaseTraceEvent):
    """Trace event for agent execution."""

    event_type: TraceEventType = TraceEventType.AGENT
    agent_name: str
    workflow: str
    model: Optional[str] = None
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None


class LLMGenerationTraceEvent(BaseTraceEvent):
    """Trace event for LLM generation."""

    event_type: TraceEventType = TraceEventType.LLM_GENERATION
    agent_name: str
    workflow: str
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class ToolCallTraceEvent(BaseTraceEvent):
    """Trace event for tool calls."""

    event_type: TraceEventType = TraceEventType.TOOL_CALL
    agent_name: str
    workflow: str
    tool_name: str
    tool_input_summary: Optional[str] = None
    tool_output_summary: Optional[str] = None


class HandoffTraceEvent(BaseTraceEvent):
    """Trace event for handoffs between agents."""

    event_type: TraceEventType = TraceEventType.HANDOFF
    source_agent: str
    target_agent: str
    workflow: str
    reason: Optional[str] = None


class GuardrailTraceEvent(BaseTraceEvent):
    """Trace event for guardrail evaluations."""

    event_type: TraceEventType = TraceEventType.GUARDRAIL
    agent_name: str
    workflow: str
    guardrail_name: str
    triggered: bool
    input_summary: Optional[str] = None


class CustomTraceEvent(BaseTraceEvent):
    """Trace event for custom events."""

    event_type: TraceEventType = TraceEventType.CUSTOM
    workflow: str
    name: str
    details: Optional[Dict[str, Any]] = None


# Union type for all possible trace events
TraceEvent = Union[
    WorkflowTraceEvent,
    AgentTraceEvent,
    LLMGenerationTraceEvent,
    ToolCallTraceEvent,
    HandoffTraceEvent,
    GuardrailTraceEvent,
    CustomTraceEvent,
]


# Utility functions
def create_workflow_trace(
    workflow: str,
    status: TraceStatus,
    duration_ms: int,
    metadata: Dict[str, Any] = None,
    group_id: str = None,
    trace_id: str = None,
) -> WorkflowTraceEvent:
    """Create a workflow trace event."""
    return WorkflowTraceEvent(
        workflow=workflow,
        status=status,
        duration_ms=duration_ms,
        metadata=metadata or {},
        group_id=group_id,
        trace_id=trace_id,
    )


def create_agent_trace(
    agent_name: str,
    workflow: str,
    status: TraceStatus,
    duration_ms: int,
    model: str = None,
    input_summary: str = None,
    output_summary: str = None,
    metadata: Dict[str, Any] = None,
) -> AgentTraceEvent:
    """Create an agent trace event."""
    return AgentTraceEvent(
        agent_name=agent_name,
        workflow=workflow,
        status=status,
        duration_ms=duration_ms,
        model=model,
        input_summary=input_summary,
        output_summary=output_summary,
        metadata=metadata or {},
    )
