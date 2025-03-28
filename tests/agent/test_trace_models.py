"""
Tests for the trace model classes and utility functions.
"""

import json

import pytest
from pydantic import ValidationError

from terminatoride.agent.trace_models import (AgentTraceEvent, BaseTraceEvent,
                                              CustomTraceEvent,
                                              GuardrailTraceEvent,
                                              HandoffTraceEvent,
                                              LLMGenerationTraceEvent,
                                              ToolCallTraceEvent,
                                              TraceEventType, TraceStatus,
                                              WorkflowTraceEvent,
                                              create_agent_trace,
                                              create_workflow_trace)


class TestTraceModels:
    def test_base_trace_event(self):
        """Test that base trace event can be created with minimal fields."""
        event = BaseTraceEvent(
            event_type=TraceEventType.CUSTOM,
            duration_ms=100,
            status=TraceStatus.SUCCESS,
        )
        assert event.event_type == TraceEventType.CUSTOM
        assert event.duration_ms == 100
        assert event.status == TraceStatus.SUCCESS
        assert isinstance(event.metadata, dict)
        assert isinstance(event.timestamp, str)
        # Timestamp should be in ISO format with Z suffix
        assert event.timestamp.endswith("Z")

    def test_workflow_trace_event(self):
        """Test workflow trace event creation and validation."""
        event = WorkflowTraceEvent(
            workflow="test_workflow",
            duration_ms=200,
            status=TraceStatus.SUCCESS,
            group_id="group1",
            trace_id="trace1",
        )
        assert event.event_type == TraceEventType.WORKFLOW
        assert event.workflow == "test_workflow"
        assert event.group_id == "group1"
        assert event.trace_id == "trace1"

    def test_agent_trace_event(self):
        """Test agent trace event creation and validation."""
        event = AgentTraceEvent(
            agent_name="test_agent",
            workflow="test_workflow",
            duration_ms=300,
            status=TraceStatus.SUCCESS,
            model="gpt-4",
            input_summary="test input",
            output_summary="test output",
        )
        assert event.event_type == TraceEventType.AGENT
        assert event.agent_name == "test_agent"
        assert event.workflow == "test_workflow"
        assert event.model == "gpt-4"
        assert event.input_summary == "test input"
        assert event.output_summary == "test output"

    def test_llm_generation_trace_event(self):
        """Test LLM generation trace event creation and validation."""
        event = LLMGenerationTraceEvent(
            agent_name="test_agent",
            workflow="test_workflow",
            model="gpt-4",
            duration_ms=400,
            status=TraceStatus.SUCCESS,
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )
        assert event.event_type == TraceEventType.LLM_GENERATION
        assert event.prompt_tokens == 100
        assert event.completion_tokens == 50
        assert event.total_tokens == 150

    def test_tool_call_trace_event(self):
        """Test tool call trace event creation and validation."""
        event = ToolCallTraceEvent(
            agent_name="test_agent",
            workflow="test_workflow",
            tool_name="test_tool",
            duration_ms=500,
            status=TraceStatus.SUCCESS,
            tool_input_summary='{"arg": "value"}',
            tool_output_summary="tool result",
        )
        assert event.event_type == TraceEventType.TOOL_CALL
        assert event.tool_name == "test_tool"
        assert event.tool_input_summary == '{"arg": "value"}'
        assert event.tool_output_summary == "tool result"

    def test_handoff_trace_event(self):
        """Test handoff trace event creation and validation."""
        event = HandoffTraceEvent(
            source_agent="agent1",
            target_agent="agent2",
            workflow="test_workflow",
            duration_ms=600,
            status=TraceStatus.SUCCESS,
            reason="Need specialized knowledge",
        )
        assert event.event_type == TraceEventType.HANDOFF
        assert event.source_agent == "agent1"
        assert event.target_agent == "agent2"
        assert event.reason == "Need specialized knowledge"

    def test_guardrail_trace_event(self):
        """Test guardrail trace event creation and validation."""
        event = GuardrailTraceEvent(
            agent_name="test_agent",
            workflow="test_workflow",
            guardrail_name="content_filter",
            triggered=True,
            duration_ms=700,
            status=TraceStatus.SUCCESS,
            input_summary="potentially harmful content",
        )
        assert event.event_type == TraceEventType.GUARDRAIL
        assert event.guardrail_name == "content_filter"
        assert event.triggered is True
        assert event.input_summary == "potentially harmful content"

    def test_custom_trace_event(self):
        """Test custom trace event creation and validation."""
        event = CustomTraceEvent(
            workflow="test_workflow",
            name="custom_event",
            details={"key": "value"},
            duration_ms=800,
            status=TraceStatus.SUCCESS,
        )
        assert event.event_type == TraceEventType.CUSTOM
        assert event.name == "custom_event"
        assert event.details == {"key": "value"}

    def test_json_serialization(self):
        """Test that trace events can be serialized to JSON."""
        event = AgentTraceEvent(
            agent_name="test_agent",
            workflow="test_workflow",
            duration_ms=300,
            status=TraceStatus.SUCCESS,
        )
        json_str = event.model_dump_json()
        data = json.loads(json_str)
        assert data["event_type"] == "agent"
        assert data["agent_name"] == "test_agent"
        assert data["workflow"] == "test_workflow"
        assert data["status"] == "success"

    def test_utility_functions(self):
        """Test the utility functions for creating trace events."""
        workflow_trace = create_workflow_trace(
            workflow="test_workflow",
            status=TraceStatus.SUCCESS,
            duration_ms=100,
            metadata={"test": "value"},
            group_id="group1",
            trace_id="trace1",
        )
        assert isinstance(workflow_trace, WorkflowTraceEvent)
        assert workflow_trace.workflow == "test_workflow"
        assert workflow_trace.metadata == {"test": "value"}

        agent_trace = create_agent_trace(
            agent_name="test_agent",
            workflow="test_workflow",
            status=TraceStatus.ERROR,
            duration_ms=200,
            model="gpt-4",
            input_summary="test input",
            output_summary="test output",
        )
        assert isinstance(agent_trace, AgentTraceEvent)
        assert agent_trace.agent_name == "test_agent"
        assert agent_trace.status == TraceStatus.ERROR
        assert agent_trace.model == "gpt-4"

    def test_invalid_status(self):
        """Test validation error when an invalid status is provided."""
        with pytest.raises(ValidationError):
            BaseTraceEvent(
                event_type=TraceEventType.CUSTOM,
                duration_ms=100,
                status="invalid_status",  # Not a valid TraceStatus
            )

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        with pytest.raises(ValidationError):
            # Missing required field workflow
            WorkflowTraceEvent(
                duration_ms=200,
                status=TraceStatus.SUCCESS,
            )
