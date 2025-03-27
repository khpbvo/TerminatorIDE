"""
Handoff system for TerminatorIDE agents.
Provides functionality for specialized agent handoffs and delegation.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from agents import Agent, Handoff, InputFilter, RunContextWrapper, handoff
from agents.extensions import handoff_filters
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from pydantic import BaseModel, create_model

logger = logging.getLogger(__name__)

T = TypeVar("T")


class HandoffManager:
    """
    Manages agent handoffs for specialized tasks.
    Provides utilities for creating and configuring handoffs.
    """

    @staticmethod
    def create_handoff(
        agent: Agent,
        on_handoff: Optional[Callable] = None,
        tool_name_override: Optional[str] = None,
        tool_description_override: Optional[str] = None,
        input_type: Optional[Type[BaseModel]] = None,
        input_filter: Optional[InputFilter] = None,
    ) -> Handoff:
        """
        Create a customized handoff object.

        Args:
            agent: The target agent to hand off to
            on_handoff: Optional callback function when handoff occurs
            tool_name_override: Optional custom name for the handoff tool
            tool_description_override: Optional custom description for the handoff
            input_type: Optional Pydantic model for structured handoff input
            input_filter: Optional filter function to modify inputs before handoff

        Returns:
            Configured Handoff object
        """
        return handoff(
            agent=agent,
            on_handoff=on_handoff,
            tool_name_override=tool_name_override,
            tool_description_override=tool_description_override,
            input_type=input_type,
            input_filter=input_filter,
        )

    @staticmethod
    def create_escalation_handoff(
        agent: Agent, reason_required: bool = True, callback: Optional[Callable] = None
    ) -> Handoff:
        """
        Create an escalation handoff with reason tracking.

        Args:
            agent: The agent to escalate to
            reason_required: Whether to require a reason for escalation
            callback: Optional callback when escalation occurs

        Returns:
            Handoff configured for escalation
        """
        # Create a dynamic Pydantic model for the escalation input
        EscalationData = create_model(
            "EscalationData",
            reason=(str, ... if reason_required else ""),
            context=(Optional[Dict[str, Any]], None),
        )

        async def on_escalation(
            ctx: RunContextWrapper[Any], input_data: EscalationData
        ):
            logger.info(f"Escalating to {agent.name}: {input_data.reason}")
            if callback:
                await callback(ctx, input_data)

        return handoff(
            agent=agent,
            on_handoff=on_escalation,
            input_type=EscalationData,
            tool_name_override=f"escalate_to_{agent.name.lower().replace(' ', '_')}",
            tool_description_override=f"Escalate this conversation to {agent.name} when you need specialized help or cannot resolve the issue.",
        )

    @staticmethod
    def create_domain_handoff(
        agent: Agent, domain: str, preserve_tools: bool = False
    ) -> Handoff:
        """
        Create a domain-specific handoff.

        Args:
            agent: The domain expert agent
            domain: The name of the domain (e.g., "Python", "JavaScript")
            preserve_tools: Whether to preserve tools in the handoff

        Returns:
            Domain-specific handoff
        """
        input_filter = None if preserve_tools else handoff_filters.remove_all_tools

        return handoff(
            agent=agent,
            tool_name_override=f"{domain.lower()}_expert",
            tool_description_override=f"Handoff to the {domain} expert when dealing with {domain}-specific questions or tasks.",
            input_filter=input_filter,
        )

    @staticmethod
    def with_recommended_prompt(instructions: str) -> str:
        """
        Add the recommended handoff prompt prefix to instructions.

        Args:
            instructions: The original instructions

        Returns:
            Instructions with recommended prefix
        """
        return f"{RECOMMENDED_PROMPT_PREFIX}\n{instructions}"

    @staticmethod
    def create_triage_agent(
        name: str,
        base_instructions: str,
        specialized_agents: List[Agent],
        model: Optional[str] = None,
    ) -> Agent:
        """
        Create a triage agent that can handoff to specialized agents.

        Args:
            name: Name of the triage agent
            base_instructions: Base instructions for the agent
            specialized_agents: List of specialized agents to handoff to
            model: Optional model override

        Returns:
            Configured triage agent
        """
        agent_descriptions = "\n".join(
            f"- {agent.name}: {agent.get_tool_description() if hasattr(agent, 'get_tool_description') else 'No description provided'}"
            for agent in specialized_agents
        )

        instructions = f"""{base_instructions}

You are a triage agent that helps determine the best specialized agent to handle a request.
You have access to the following specialized agents:

{agent_descriptions}

When a user request clearly falls into one of these domains, use the appropriate handoff tool.
Only hand off when you're confident the specialized agent can better handle the request.
"""

        return Agent(
            name=name,
            instructions=instructions,
            handoffs=specialized_agents,
            model=model,
        )
