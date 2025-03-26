"""
Agent Manager module for TerminatorIDE.
Handles agent initialization, configuration, and execution.
"""
import os
import logging
import asyncio
from typing import Optional, List, Dict, Any, Union, AsyncIterator, Callable, Type
from dataclasses import dataclass
from pathlib import Path

from agents import (
    Agent, Runner, RunConfig, function_tool, 
    set_default_openai_key, set_default_openai_client,
    trace, enable_verbose_stdout_logging, ItemHelpers, 
    RunResultStreaming, StreamEvent, InputGuardrailTripwireTriggered, 
    OutputGuardrailTripwireTriggered, Handoff, HandoffCallItem,
    HandoffOutput, HandoffOutputItem, ItemHelpers
)
from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent
from pydantic import BaseModel

from terminatoride.config import get_config
from terminatoride.agent.tools import register_tools
from terminatoride.agent.guardrails import get_default_guardrails
from terminatoride.agent.handoff import HandoffManager

logger = logging.getLogger(__name__)

class AgentManager:
    """Manages Agent SDK integration for TerminatorIDE."""
    
    def __init__(self, enable_tracing: bool = True, verbose_logging: bool = False,
                enable_guardrails: bool = True):
        """Initialize the agent manager."""
        self.config = get_config()
        self._init_client()
        self._agents = {}
        self._specialized_agents = {}
        self.enable_guardrails = enable_guardrails
        self.handoff_manager = HandoffManager()
        
        # Set up logging if requested
        if verbose_logging:
            enable_verbose_stdout_logging()
        
        # Register built-in tools
        self.tools = register_tools()
        
        # Set up default guardrails
        self.input_guardrails, self.output_guardrails = get_default_guardrails() if enable_guardrails else ([], [])
    
    def _init_client(self):
        """Initialize OpenAI client from configuration."""
        api_key = self.config.openai.api_key
        if not api_key:
            raise ValueError("OpenAI API key is not configured")
        
        # Set the API key for the Agent SDK
        set_default_openai_key(api_key)
        
        # Optionally configure a custom client
        if self.config.openai.organization:
            client = AsyncOpenAI(
                api_key=api_key,
                organization=self.config.openai.organization
            )
            set_default_openai_client(client)
    
    def create_agent(self, name: str, instructions: str, model: Optional[str] = None, 
                    tools: Optional[List] = None, handoffs: Optional[List] = None, 
                    output_type: Optional[Any] = None, apply_guardrails: bool = True) -> Agent:
        """
        Create and register a new agent.
        
        Args:
            name: The name of the agent
            instructions: Prompt/instructions for the agent
            model: Optional model to use, defaults to config
            tools: Optional list of tools to provide to the agent
            handoffs: Optional list of handoff agents
            output_type: Optional pydantic model for structured output
            apply_guardrails: Whether to apply default guardrails to this agent
            
        Returns:
            The created Agent instance
        """
        if not model:
            model = self.config.openai.model
        
        if not tools:
            tools = self.tools
            
        # Apply guardrails if enabled and requested
        input_guardrails = self.input_guardrails if self.enable_guardrails and apply_guardrails else []
        output_guardrails = self.output_guardrails if self.enable_guardrails and apply_guardrails else []
            
        agent = Agent(
            name=name,
            instructions=instructions,
            model=model,
            tools=tools,
            handoffs=handoffs,
            output_type=output_type,
            input_guardrails=input_guardrails,
            output_guardrails=output_guardrails
        )
        
        # Register the agent for future reference
        self._agents[name] = agent
        return agent
    
    def create_specialized_agent(self, name: str, instructions: str, 
                                specialty: str, model: Optional[str] = None,
                                tools: Optional[List] = None, 
                                output_type: Optional[Any] = None) -> Agent:
        """
        Create and register a specialized agent for a specific domain or task.
        
        Args:
            name: The name of the agent
            instructions: Prompt/instructions for the agent
            specialty: The specialty domain or task
            model: Optional model to use, defaults to config
            tools: Optional list of tools to provide to the agent
            output_type: Optional pydantic model for structured output
            
        Returns:
            The created Agent instance
        """
        # Add the specialty to the agent name for clarity
        full_name = f"{name} ({specialty} Specialist)"
        
        agent = self.create_agent(
            name=full_name,
            instructions=instructions,
            model=model,
            tools=tools,
            output_type=output_type
        )
        
        # Register as a specialized agent
        self._specialized_agents[specialty.lower()] = agent
        return agent
    
    def create_triage_agent(self, name: str, base_instructions: str, 
                            specialized_agents: Optional[List[Union[Agent, str]]] = None, 
                            model: Optional[str] = None) -> Agent:
        """
        Create a triage agent that can handoff to specialized agents.
        
        Args:
            name: Name of the triage agent
            base_instructions: Base instructions for the agent
            specialized_agents: Optional list of specialized agents or agent names
            model: Optional model override
            
        Returns:
            Configured triage agent
        """
        # Process agent list to get actual agent objects
        agents_list = []
        if specialized_agents:
            for agent in specialized_agents:
                if isinstance(agent, str):
                    if agent in self._agents:
                        agents_list.append(self._agents[agent])
                    else:
                        logger.warning(f"Agent '{agent}' not found, skipping")
                else:
                    agents_list.append(agent)
        else:
            # If no agents specified, use all registered specialized agents
            agents_list = list(self._specialized_agents.values())
        
        return HandoffManager.create_triage_agent(
            name=name,
            base_instructions=base_instructions,
            specialized_agents=agents_list,
            model=model
        )
    
    def create_handoff(self, source_agent: Union[Agent, str], 
                      target_agent: Union[Agent, str],
                      tool_name: Optional[str] = None,
                      description: Optional[str] = None,
                      on_handoff: Optional[Callable] = None) -> None:
        """
        Create a handoff relationship between two agents.
        
        Args:
            source_agent: The agent that will hand off tasks
            target_agent: The agent that will receive handoffs
            tool_name: Optional override for the handoff tool name
            description: Optional description for the handoff
            on_handoff: Optional callback when handoff occurs
        """
        # Get agent instances if names were provided
        source = source_agent if isinstance(source_agent, Agent) else self._agents.get(source_agent)
        target = target_agent if isinstance(target_agent, Agent) else self._agents.get(target_agent)
        
        if not source or not target:
            missing = []
            if not source:
                missing.append(f"source '{source_agent}'")
            if not target:
                missing.append(f"target '{target_agent}'")
            raise ValueError(f"Could not find agents: {', '.join(missing)}")
        
        # Create the handoff object
        handoff_obj = HandoffManager.create_handoff(
            agent=target,
            on_handoff=on_handoff,
            tool_name_override=tool_name,
            tool_description_override=description
        )
        
        # Update the source agent's handoffs
        if not source.handoffs:
            source.handoffs = [handoff_obj]
        else:
            source.handoffs.append(handoff_obj)
        
        logger.info(f"Created handoff from {source.name} to {target.name}")
    
    def create_escalation_path(self, from_agent: Union[Agent, str], 
                              to_agent: Union[Agent, str],
                              reason_required: bool = True,
                              callback: Optional[Callable] = None) -> None:
        """
        Create an escalation path from one agent to another.
        
        Args:
            from_agent: The agent with the issue
            to_agent: The agent to escalate to
            reason_required: Whether to require a reason for escalation
            callback: Optional callback function when escalation occurs
        """
        # Get agent instances if names were provided
        source = from_agent if isinstance(from_agent, Agent) else self._agents.get(from_agent)
        target = to_agent if isinstance(to_agent, Agent) else self._agents.get(to_agent)
        
        if not source or not target:
            missing = []
            if not source:
                missing.append(f"source '{from_agent}'")
            if not target:
                missing.append(f"target '{to_agent}'")
            raise ValueError(f"Could not find agents: {', '.join(missing)}")
        
        # Create the escalation handoff
        handoff_obj = HandoffManager.create_escalation_handoff(
            agent=target,
            reason_required=reason_required,
            callback=callback
        )
        
        # Update the source agent's handoffs
        if not source.handoffs:
            source.handoffs = [handoff_obj]
        else:
            source.handoffs.append(handoff_obj)
        
        logger.info(f"Created escalation path from {source.name} to {target.name}")
    
    async def run_agent(self, agent: Union[Agent, str], user_input: str, 
                        context: Optional[Any] = None, 
                        run_config: Optional[RunConfig] = None) -> Any:
        """
        Run an agent with the given input.
        
        Args:
            agent: The agent instance or name of a registered agent
            user_input: The user input to pass to the agent
            context: Optional context to pass to the agent
            run_config: Optional run configuration
            
        Returns:
            The output from the agent run
        """
        if isinstance(agent, str):
            if agent not in self._agents:
                raise ValueError(f"Agent '{agent}' is not registered")
            agent = self._agents[agent]
        
        try:
            with trace(workflow_name=f"{agent.name} Run"):
                result = await Runner.run(
                    starting_agent=agent,
                    input=user_input,
                    context=context,
                    run_config=run_config
                )
                
            return result
        except InputGuardrailTripwireTriggered as e:
            logger.warning(f"Input guardrail triggered: {e}")
            return {
                "error": "guardrail_triggered",
                "message": "Your input was flagged by our safety system.",
                "details": str(e)
            }
        except OutputGuardrailTripwireTriggered as e:
            logger.warning(f"Output guardrail triggered: {e}")
            return {
                "error": "guardrail_triggered",
                "message": "The agent's response was flagged by our safety system.",
                "details": str(e)
            }
        except Exception as e:
            logger.error(f"Error running agent: {e}")
            return {
                "error": "execution_error",
                "message": f"Error running agent: {str(e)}",
                "details": str(e)
            }
    
    async def run_agent_streamed(self, agent: Union[Agent, str], user_input: str,
                                context: Optional[Any] = None,
                                run_config: Optional[RunConfig] = None,
                                on_text_delta: Optional[Callable[[str], None]] = None,
                                on_tool_call: Optional[Callable[[Dict[str, Any]], None]] = None,
                                on_tool_result: Optional[Callable[[Dict[str, Any]], None]] = None,
                                on_handoff: Optional[Callable[[Dict[str, Any]], None]] = None,
                                on_error: Optional[Callable[[Dict[str, Any]], None]] = None) -> Any:
        """
        Run an agent with streaming responses.
        
        Args:
            agent: The agent instance or name of a registered agent
            user_input: The user input to pass to the agent
            context: Optional context to pass to the agent
            run_config: Optional run configuration
            on_text_delta: Callback for text generation events
            on_tool_call: Callback for tool call events
            on_tool_result: Callback for tool result events
            on_handoff: Callback for handoff events
            on_error: Callback for error events
            
        Returns:
            The final result from the agent run
        """
        if isinstance(agent, str):
            if agent not in self._agents:
                raise ValueError(f"Agent '{agent}' is not registered")
            agent = self._agents[agent]
        
        try:
            with trace(workflow_name=f"{agent.name} Streamed Run"):
                result = Runner.run_streamed(
                    starting_agent=agent,
                    input=user_input,
                    context=context,
                    run_config=run_config
                )
                
                # Process streaming events
                async for event in result.stream_events():
                    if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                        # Text being generated token by token
                        if on_text_delta and hasattr(event.data, 'delta'):
                            on_text_delta(event.data.delta)
                    
                    elif event.type == "agent_updated_stream_event" and on_handoff:
                        # Agent was updated (handoff occurred)
                        handoff_info = {
                            "from_agent": event.source_agent.name if hasattr(event, 'source_agent') else "unknown",
                            "to_agent": event.new_agent.name,
                            "reason": "Agent handoff"
                        }
                        on_handoff(handoff_info)
                            
                    elif event.type == "run_item_stream_event":
                        if event.item.type == "handoff_call_item" and on_handoff:
                            # Handoff is being initiated
                            handoff_call = event.item.raw_item
                            target_name = "unknown"
                            if hasattr(handoff_call, 'function') and hasattr(handoff_call.function, 'name'):
                                for h in agent.handoffs:
                                    if h.tool_name == handoff_call.function.name:
                                        target_name = h.agent.name
                                        break
                            
                            handoff_info = {
                                "from_agent": agent.name,
                                "to_agent": target_name,
                                "reason": "Handoff initiated"
                            }
                            on_handoff(handoff_info)
                            
                        elif event.item.type == "handoff_output_item" and on_handoff:
                            # Handoff completed
                            source_agent = event.item.source_agent.name if hasattr(event.item, 'source_agent') else "unknown"
                            target_agent = event.item.target_agent.name if hasattr(event.item, 'target_agent') else "unknown"
                            
                            handoff_info = {
                                "from_agent": source_agent,
                                "to_agent": target_agent,
                                "reason": "Handoff completed"
                            }
                            on_handoff(handoff_info)
                        
                        elif event.item.type == "tool_call_item" and on_tool_call:
                            # Tool is being called
                            tool_info = {
                                "name": event.item.raw_item.function.name,
                                "arguments": event.item.raw_item.function.arguments
                            }
                            on_tool_call(tool_info)
                            
                        elif event.item.type == "tool_call_output_item" and on_tool_result:
                            # Tool call result
                            result_info = {
                                "output": event.item.output
                            }
                            on_tool_result(result_info)
                            
                        elif event.item.type == "message_output_item" and on_text_delta:
                            # Complete message output
                            message_text = ItemHelpers.text_message_output(event.item)
                            on_text_delta(f"\n{message_text}")
            
            return result
        except InputGuardrailTripwireTriggered as e:
            logger.warning(f"Input guardrail triggered: {e}")
            error_info = {
                "error": "guardrail_triggered",
                "message": "Your input was flagged by our safety system.",
                "details": str(e)
            }
            if on_error:
                on_error(error_info)
            return error_info
        except OutputGuardrailTripwireTriggered as e:
            logger.warning(f"Output guardrail triggered: {e}")
            error_info = {
                "error": "guardrail_triggered",
                "message": "The agent's response was flagged by our safety system.",
                "details": str(e)
            }
            if on_error:
                on_error(error_info)
            return error_info
        except Exception as e:
            logger.error(f"Error in streamed run: {e}")
            error_info = {
                "error": "execution_error",
                "message": f"Error running agent: {str(e)}",
                "details": str(e)
            }
            if on_error:
                on_error(error_info)
            return error_info
    
    async def stream_tokens(self, agent: Union[Agent, str], user_input: str,
                          context: Optional[Any] = None) -> AsyncIterator[str]:
        """
        Stream tokens from an agent response.
        
        Args:
            agent: The agent instance or name of a registered agent
            user_input: The user input to pass to the agent
            context: Optional context to pass to the agent
            
        Yields:
            Individual tokens as they are generated
        """
        if isinstance(agent, str):
            if agent not in self._agents:
                raise ValueError(f"Agent '{agent}' is not registered")
            agent = self._agents[agent]
        
        try:
            result = Runner.run_streamed(
                starting_agent=agent,
                input=user_input,
                context=context
            )
            
            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    if hasattr(event.data, 'delta'):
                        yield event.data.delta
        except InputGuardrailTripwireTriggered as e:
            yield f"\n[SAFETY SYSTEM] Your input was flagged: {str(e)}"
        except OutputGuardrailTripwireTriggered as e:
            yield f"\n[SAFETY SYSTEM] The response was flagged: {str(e)}"
        except Exception as e:
            yield f"\n[ERROR] {str(e)}"
    
    def get_agent(self, name: str) -> Optional[Agent]:
        """Get a registered agent by name."""
        return self._agents.get(name)
    
    def get_specialized_agent(self, specialty: str) -> Optional[Agent]:
        """Get a specialized agent by specialty domain."""
        return self._specialized_agents.get(specialty.lower())
    
    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self._agents.keys())
    
    def list_specialized_agents(self) -> Dict[str, str]:
        """List all specialized agents with their specialties."""
        return {specialty: agent.name for specialty, agent in self._specialized_agents.items()}
