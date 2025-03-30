"""
Agent Manager module for TerminatorIDE.
Handles agent initialization, configuration, and execution.
"""

import logging
from typing import Any, Dict, List, Optional, Type, Union

from agents import (
    Agent,
    RunConfig,
    Runner,
    enable_verbose_stdout_logging,
    set_default_openai_client,
    set_default_openai_key,
)
from openai import AsyncOpenAI
from pydantic import BaseModel

from terminatoride.agent.agent_sdk_trace_bridge import trace_agent_run
from terminatoride.agent.tools import register_tools
from terminatoride.config import get_config

logger = logging.getLogger(__name__)


class AgentManager:
    """Manages Agent SDK integration for TerminatorIDE."""

    def __init__(self, enable_tracing: bool = True, verbose_logging: bool = False):
        """Initialize the agent manager."""
        self.config = get_config()
        self._init_client()
        self._agents = {}

        # Set up logging if requested
        if verbose_logging:
            enable_verbose_stdout_logging()

        # Register built-in tools
        self.tools = register_tools()

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
                api_key=api_key, organization=self.config.openai.organization
            )
            set_default_openai_client(client)

    def create_agent(
        self,
        name: str,
        instructions: str,
        model: Optional[str] = None,
        tools: Optional[List] = None,
        handoffs: Optional[List] = None,
        output_type: Optional[Type[BaseModel]] = None,
    ) -> Agent:
        """
        Create and register a new agent.

        Args:
            name: The name of the agent
            instructions: Prompt/instructions for the agent
            model: Optional model to use, defaults to config
            tools: Optional list of tools to provide to the agent
            handoffs: Optional list of handoff agents
            output_type: Optional pydantic model for structured output

        Returns:
            The created Agent instance
        """
        if not model:
            model = self.config.openai.model

        if not tools:
            tools = self.tools

        agent = Agent(
            name=name,
            instructions=instructions,
            model=model,
            tools=tools,
            handoffs=handoffs,
            output_type=output_type,
        )

        # Register the agent for future reference
        self._agents[name] = agent
        return agent

    def create_specialized_agent(
        self,
        name: str,
        instructions: str,
        specialty: str,
        output_type: Type[BaseModel],
        model: Optional[str] = None,
        tools: Optional[List] = None,
    ) -> Agent:
        """
        Create a specialized agent with a structured output type.

        Args:
            name: The name of the agent
            instructions: Prompt/instructions for the agent
            specialty: The agent's area of expertise
            output_type: Pydantic model for structured output
            model: Optional model to use, defaults to config
            tools: Optional list of tools to provide to the agent

        Returns:
            The created specialized Agent instance
        """
        agent = self.create_agent(
            name=name,
            instructions=instructions,
            model=model,
            tools=tools,
            output_type=output_type,
        )

        # Add metadata about the specialty
        agent.metadata = {"specialty": specialty}

        logger.info(f"Created specialized agent '{name}' for {specialty}")
        return agent

    async def run_agent(
        self,
        agent: Union[Agent, str],
        user_input: str,
        context: Optional[Any] = None,
        run_config: Optional[RunConfig] = None,
    ) -> Any:
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
            agent_instance = self._agents[agent]
        else:
            agent_instance = agent

        # Use the trace_agent_run decorator for detailed tracing
        @trace_agent_run(agent_instance.name, getattr(agent_instance, "model", None))
        async def _run_agent():
            return await Runner.run(
                starting_agent=agent_instance,
                input=user_input,
                context=context,
                run_config=run_config,
            )

        return await _run_agent()

    def get_agent(self, name: str) -> Optional[Agent]:
        """Get a registered agent by name."""
        return self._agents.get(name)

    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self._agents.keys())

    def list_specialized_agents(self) -> List[Dict[str, str]]:
        """List all specialized agents with their specialties."""
        result = []
        for name, agent in self._agents.items():
            if (
                hasattr(agent, "metadata")
                and agent.metadata
                and "specialty" in agent.metadata
            ):
                result.append(
                    {
                        "name": name,
                        "specialty": agent.metadata["specialty"],
                        "output_type": (
                            agent.output_type.__name__ if agent.output_type else None
                        ),
                    }
                )
        return result
