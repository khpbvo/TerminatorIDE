"""
OpenAI Agent implementation for TerminatorIDE.
This module integrates the OpenAI Agent SDK for AI assistant capabilities.
"""

import logging
from typing import Any, List, Optional

from agents import Agent, Runner, set_default_openai_key

from terminatoride.agent.agent_sdk_trace_bridge import trace_agent_run
from terminatoride.agent.context import AgentContext
from terminatoride.agent.models import ModelSelector, ModelType
from terminatoride.agent.tools import register_tools
from terminatoride.agent.tracing import trace
from terminatoride.config import get_config
from terminatoride.utils.error_handling import RateLimitHandler

logger = logging.getLogger(__name__)


class OpenAIAgent:
    """Main OpenAI Agent implementation using the Agent SDK."""

    def __init__(self):
        """Initialize the OpenAI agent with configuration, tools, and rate limiting."""
        self.config = get_config()
        self._setup_api_key()

        self.tools = register_tools()
        # Remove any tool with the name 'list_directory' to avoid schema errors.
        self.tools = [
            tool
            for tool in self.tools
            if getattr(tool, "name", None) != "list_directory"
        ]

        # Set up rate limiting
        self.rate_limiter = RateLimitHandler(max_requests=50, time_window=60)

        # Create the default agent
        self.default_agent = self._create_default_agent()

        # Store specialized agents
        self.specialized_agents = {}

        logger.info("OpenAI Agent initialized successfully")

    def _setup_api_key(self):
        """Set up the OpenAI API key from configuration."""
        api_key = self.config.openai.api_key
        if not api_key:
            raise ValueError("OpenAI API key is not configured")

        # Set the API key for the Agent SDK
        set_default_openai_key(api_key)
        logger.debug("API key configured")

    def _create_default_agent(self) -> Agent:
        """Create the default assistant agent."""
        with trace("Creating default agent"):
            model_type = ModelType.from_string(self.config.openai.model)
            # model_settings = ModelSelector.get_recommended_settings(model_type)

            agent = Agent(
                name="TerminatorIDE Assistant",
                instructions="""
                You are an AI assistant for TerminatorIDE, a terminal-based integrated development environment.
                Help users with coding tasks, explain code, suggest improvements, and assist with using the IDE.
                Use the available tools to interact with the IDE and provide helpful responses.
                Be concise, clear, and focus on providing practical solutions.
                """,
                model=ModelSelector.get_model_string(model_type),
                tools=self.tools,
            )

            return agent

    def create_specialized_agent(
        self,
        name: str,
        instructions: str,
        model_type: Optional[ModelType] = None,
        output_type: Optional[type] = None,
    ) -> Agent:
        """
        Create a specialized agent for a specific task.

        Args:
            name: Name of the specialized agent
            instructions: Specific instructions for this agent
            model_type: Optional specific model to use
            output_type: Optional Pydantic model for structured output

        Returns:
            The created specialized agent
        """
        if not model_type:
            model_type = ModelType.from_string(self.config.openai.model)

        # Get appropriate settings for this model
        # model_settings = ModelSelector.get_recommended_settings(model_type)

        # Create the agent
        agent = Agent(
            name=name,
            instructions=instructions,
            model=ModelSelector.get_model_string(model_type),
            tools=self.tools,
            output_type=output_type,
        )

        # Store for future reference
        self.specialized_agents[name] = agent

        return agent

    @trace_agent_run("Default Agent")
    async def generate_response(
        self, user_message: str, context: Optional[AgentContext] = None
    ) -> str:
        """
        Generate a response to the user's message.

        Args:
            user_message: The user's input message
            context: Optional agent context with IDE state

        Returns:
            The generated response from the agent
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

            # Execute the agent
            result = await Runner.run(
                starting_agent=self.default_agent,
                input=user_message,
                context=run_context,
            )

            return result.final_output

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"I encountered an error while processing your request. {str(e)}"

    @trace_agent_run("Specialized Agent")
    async def run_specialized_agent(
        self, agent_name: str, user_message: str, context: Optional[AgentContext] = None
    ) -> Any:
        """
        Run a specialized agent by name.

        Args:
            agent_name: Name of the specialized agent to run
            user_message: The user's input message
            context: Optional agent context

        Returns:
            The agent's response, which may be structured data if the agent has an output_type
        """
        # Check rate limits before proceeding
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.time_until_next_request()
            if wait_time > 0:
                logger.warning(
                    f"Rate limit reached. Need to wait {wait_time:.2f} seconds"
                )
                return (
                    f"Rate limit reached. Please try again in {wait_time:.1f} seconds."
                )

        if agent_name not in self.specialized_agents:
            raise ValueError(f"Specialized agent '{agent_name}' not found")

        agent = self.specialized_agents[agent_name]
        run_context = context if context is not None else AgentContext()

        result = await Runner.run(
            starting_agent=agent, input=user_message, context=run_context
        )

        return result.final_output

    def get_available_agents(self) -> List[str]:
        """Get a list of available specialized agent names."""
        return list(self.specialized_agents.keys())


# Provide a singleton instance
_default_agent = None


def get_openai_agent() -> OpenAIAgent:
    """Get or create the default OpenAI agent instance."""
    global _default_agent
    if _default_agent is None:
        _default_agent = OpenAIAgent()
    return _default_agent
