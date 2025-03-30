"""
IDE Tools Integration Module for TerminatorIDE.
"""

from terminatoride.agent.agent_manager import AgentManager


def setup_ide_tools(agent_manager: AgentManager) -> None:
    """
    Set up and register IDE tools with the Agent Manager.

    Args:
        agent_manager: The AgentManager instance
    """
    from terminatoride.ide.function_tools import register_ide_tools

    # Get all IDE operation tools
    ide_tools = register_ide_tools()

    # Add IDE tools to the default tools
    all_tools = agent_manager.tools + ide_tools

    # Update the tools on the agent manager
    agent_manager.tools = all_tools

    # Update tools on existing agents
    for name, agent in agent_manager._agents.items():
        # Don't override specialized tools if the agent already has them
        if not getattr(agent, "tools", None):
            agent.tools = all_tools
