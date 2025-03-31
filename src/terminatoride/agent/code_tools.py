"""
Code manipulation tools for TerminatorIDE agents.
Allows agents to analyze, modify, and improve code using difflib.
"""

from typing import Any, Optional

from agents import RunContextWrapper, function_tool

from terminatoride.agent.context import AgentContext
from terminatoride.agent.tracing import trace
from terminatoride.utils.diff_manager import DiffManager


@function_tool
async def apply_code_changes(
    ctx: RunContextWrapper[Any],
    content: str,
    line_start: Optional[int] = None,
    line_end: Optional[int] = None,
    show_diff: Optional[bool] = None,
) -> str:
    """
    Apply code changes to the current file.

    Args:
        content: The new content for the specified lines or full file
        line_start: Optional starting line number (0-indexed)
        line_end: Optional ending line number (0-indexed)
        show_diff: Whether to show a diff before applying (default: True)

    Returns:
        Result message
    """
    with trace(
        workflow_name="Tool: apply_code_changes", metadata={"length": len(content)}
    ):
        try:
            if (
                not isinstance(ctx.context, AgentContext)
                or not ctx.context.current_file
            ):
                return "Error: No file is currently open"

            original_content = ctx.context.current_file.content

            # If line range is specified, only replace that part
            if line_start is not None and line_end is not None:
                lines = original_content.splitlines()

                # Validate line range
                if line_start < 0 or line_end >= len(lines) or line_start > line_end:
                    return f"Error: Invalid line range ({line_start}, {line_end})"

                # Replace the specified lines
                new_lines = (
                    lines[:line_start] + content.splitlines() + lines[line_end + 1 :]
                )
                modified_content = "\n".join(new_lines)
            else:
                # Replace the entire file
                modified_content = content

            # Generate diff
            diff = DiffManager.generate_diff(original_content, modified_content)

            # Apply changes via context
            show = show_diff if show_diff is not None else True
            success = ctx.context.apply_code_changes(modified_content, show)

            if success:
                return f"Code changes prepared. Diff preview:\n{diff[:500]}..."
            else:
                return "Error: Failed to apply code changes"
        except Exception as e:
            return f"Error applying changes: {str(e)}"


@function_tool
async def suggest_code_changes(
    ctx: RunContextWrapper[Any],
    original_code: str,
    suggested_code: str,
    description: str,
) -> str:
    """
    Suggest code changes without applying them.

    Args:
        original_code: The original code snippet
        suggested_code: The suggested improved code
        description: Description of the changes

    Returns:
        Diff between original and suggested code
    """
    with trace(
        workflow_name="Tool: suggest_code_changes",
        metadata={"description": description},
    ):
        try:
            # Generate diff
            diff = DiffManager.generate_diff(original_code, suggested_code)

            # Return the suggestion
            return f"Suggested Changes: {description}\n\n{diff}"
        except Exception as e:
            return f"Error generating suggestion: {str(e)}"


@function_tool
async def improve_code(
    ctx: RunContextWrapper[Any],
    instructions: str,
    line_start: Optional[int] = None,
    line_end: Optional[int] = None,
) -> str:
    """
    Analyze and improve code based on instructions.

    Args:
        instructions: What improvements to make
        line_start: Optional starting line (0-indexed) to limit scope
        line_end: Optional ending line (0-indexed) to limit scope

    Returns:
        Improved code with explanation
    """
    with trace(
        workflow_name="Tool: improve_code", metadata={"instructions": instructions}
    ):
        try:
            if (
                not isinstance(ctx.context, AgentContext)
                or not ctx.context.current_file
            ):
                return "Error: No file is currently open"

            original_content = ctx.context.current_file.content

            # Extract relevant portion if line range is specified
            if line_start is not None and line_end is not None:
                lines = original_content.splitlines()

                # Validate line range
                if line_start < 0 or line_end >= len(lines) or line_start > line_end:
                    return f"Error: Invalid line range ({line_start}, {line_end})"

                # Get the code to improve
                code_to_improve = "\n".join(lines[line_start : line_end + 1])
            else:
                code_to_improve = original_content

            # Here you would normally call another LLM to improve the code
            # For now, we'll return a placeholder that would typically be
            # replaced with actual LLM-improved code
            return f"""
ORIGINAL CODE:
{code_to_improve}

INSTRUCTIONS:
{instructions}

To improve this code according to these instructions, use the `apply_code_changes` tool
with your improved version of the code and set `show_diff=True` to let the user
review the changes before applying them.
"""
        except Exception as e:
            return f"Error improving code: {str(e)}"


@function_tool
async def analyze_code(ctx: RunContextWrapper[Any], focus: Optional[str] = None) -> str:
    """
    Analyze the current file's code for issues or improvement opportunities.

    Args:
        focus: Optional focus area (e.g., "performance", "security", "readability")

    Returns:
        Analysis results
    """
    with trace(
        workflow_name="Tool: analyze_code", metadata={"focus": focus or "general"}
    ):
        try:
            if (
                not isinstance(ctx.context, AgentContext)
                or not ctx.context.current_file
            ):
                return "Error: No file is currently open"

            code = ctx.context.current_file.content
            language = ctx.context.current_file.language or "unknown"

            # Here you would normally do an actual code analysis, potentially
            # using various tools depending on the language
            return f"""
CODE ANALYSIS:

Language: {language}
File size: {len(code)} characters
Line count: {len(code.splitlines())} lines

This is where a detailed code analysis would appear based on the focus area: {focus or "general"}

You can use the `improve_code` tool to suggest improvements to this code.
"""
        except Exception as e:
            return f"Error analyzing code: {str(e)}"
