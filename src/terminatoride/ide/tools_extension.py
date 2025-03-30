"""
Extension module for agent tools integration.
This module allows adding IDE function tools to the existing tools registry.
"""

import logging
from typing import List

# Import IDE-specific tools
try:
    from terminatoride.ide.function_tools import register_ide_tools as get_ide_tools

    IDE_TOOLS_AVAILABLE = True
except ImportError:
    IDE_TOOLS_AVAILABLE = False
    logging.warning("IDE tools module not found. Some functionality will be limited.")

logger = logging.getLogger(__name__)


def extend_tools(existing_tools: List) -> List:
    """
    Extend existing tools list with IDE function tools.

    Args:
        existing_tools: List of existing tools to extend

    Returns:
        Extended list of tools including IDE function tools
    """
    # Start with provided tools
    all_tools = list(existing_tools)

    # Add IDE-specific tools if available
    if IDE_TOOLS_AVAILABLE:
        try:
            ide_tools = get_ide_tools()
            all_tools.extend(ide_tools)
            logger.info(f"Added {len(ide_tools)} IDE tools to existing tools")
        except Exception as e:
            logger.error(f"Failed to add IDE tools: {str(e)}")

    return all_tools
