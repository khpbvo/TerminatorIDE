"""
Agent initialization module for TerminatorIDE.
"""

from terminatoride.agent.agent_manager import AgentManager
from terminatoride.agent.context import (AgentContext, FileContext,
                                         ProjectContext)
from terminatoride.agent.models import ModelSelector, ModelSettings, ModelType
from terminatoride.agent.tools import register_tools

__all__ = [
    "AgentManager",
    "AgentContext",
    "FileContext",
    "ProjectContext",
    "ModelType",
    "ModelSettings",
    "ModelSelector",
    "register_tools",
]

# Create a default agent manager instance
default_agent_manager = None


def get_agent_manager() -> AgentManager:
    """Get or create the default agent manager."""
    global default_agent_manager
    if default_agent_manager is None:
        default_agent_manager = AgentManager()
    return default_agent_manager
