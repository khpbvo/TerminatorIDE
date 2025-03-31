"""
Tool implementations for TerminatorIDE agents.
These tools allow agents to interact with the IDE environment.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, List, TypedDict

from agents import FunctionTool, RunContextWrapper, function_tool

from terminatoride.agent.tracing import trace
from terminatoride.ide.tools_extension import IDE_TOOLS_AVAILABLE, extend_tools


class FileInfo(TypedDict):
    path: str
    content: str
    size: int
    is_directory: bool


@function_tool
async def read_file(ctx: RunContextWrapper[Any], path: str) -> str:
    """
    Read the contents of a file.

    Args:
        path: Path to the file to read

    Returns:
        The contents of the file as a string
    """
    with trace(workflow_name="Tool: read_file", metadata={"path": path}):
        try:
            file_path = Path(path).expanduser().resolve()
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading file: {str(e)}"


@function_tool
async def write_file(ctx: RunContextWrapper[Any], path: str, content: str) -> str:
    """
    Write content to a file.

    Args:
        path: Path to the file to write
        content: Content to write to the file

    Returns:
        A message indicating success or failure
    """
    with trace(workflow_name="Tool: write_file", metadata={"path": path}):
        try:
            file_path = Path(path).expanduser().resolve()

            # Make parent directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            file_path.write_text(content, encoding="utf-8")
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing to file: {str(e)}"


@function_tool
async def list_directory(
    ctx: RunContextWrapper[Any], path: str = ".", show_hidden: bool = False
) -> List[FileInfo]:
    """
    List files and directories in the given path.

    Args:
        path: Directory path to list
        show_hidden: Whether to include hidden files

    Returns:
        List of file and directory information
    """
    with trace(
        workflow_name="Tool: list_directory",
        metadata={"path": path, "show_hidden": show_hidden},
    ):
        try:
            dir_path = Path(path).expanduser().resolve()
            result = []

            for item in dir_path.iterdir():
                if not show_hidden and item.name.startswith("."):
                    continue

                try:
                    info = {
                        "path": str(item),
                        "is_directory": item.is_dir(),
                        "size": item.stat().st_size if item.is_file() else 0,
                        "content": (
                            ""
                            if item.is_dir()
                            else (
                                item.read_text(encoding="utf-8", errors="replace")
                                if item.suffix in [".txt", ".py", ".md", ".json"]
                                and item.stat().st_size < 100000
                                else "File too large to display"
                            )
                        ),
                    }
                    result.append(info)
                except Exception:
                    # Skip files that can't be accessed
                    continue

            return result
        except Exception as e:
            return [
                {
                    "path": str(path),
                    "content": f"Error listing directory: {str(e)}",
                    "size": 0,
                    "is_directory": False,
                }
            ]


@function_tool
async def execute_python(ctx: RunContextWrapper[Any], code: str) -> str:
    """
    Execute Python code and return the result.

    Args:
        code: Python code to execute

    Returns:
        Output from running the code
    """
    with trace(
        workflow_name="Tool: execute_python",
        metadata={"temp_file": "./tmp_execution.py"},
    ):
        try:
            # Create a temporary file for the code
            tmp_file = Path("./tmp_execution.py")
            tmp_file.write_text(code, encoding="utf-8")

            # Execute the code in a separate process with a timeout
            result = subprocess.run(
                [sys.executable, str(tmp_file)],
                capture_output=True,
                text=True,
                timeout=5,
            )

            # Clean up the temporary file
            tmp_file.unlink(missing_ok=True)

            if result.returncode != 0:
                return f"Error executing code: {result.stderr}"

            return result.stdout or "Code executed successfully (no output)"
        except subprocess.TimeoutExpired:
            tmp_file.unlink(missing_ok=True)
            return "Execution timed out after 5 seconds"
        except Exception as e:
            return f"Error: {str(e)}"


@function_tool
async def lint_python(ctx: RunContextWrapper[Any], code: str) -> str:
    """
    Lint Python code using pylint and return the output.

    Args:
        code: Python code to lint

    Returns:
        Linting output as a string
    """
    with trace(workflow_name="Tool: lint_python", metadata={"length": len(code)}):
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(code)
                temp_path = f.name

            result = subprocess.run(
                ["pylint", temp_path, "--output-format=json"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            issues = json.loads(result.stdout or "[]")

            return json.dumps(issues, indent=2) if issues else "No issues found ✅"
        except Exception as e:
            return f"Error running pylint: {str(e)}"


@function_tool
async def get_current_file(ctx: RunContextWrapper[Any]) -> FileInfo:
    """
    Get information about the currently open file in the editor.

    Returns:
        Information about the current file
    """
    with trace(workflow_name="Tool: get_current_file", metadata={}):
        # This will be updated to get the actual current file in the editor
        # For now, return a placeholder
        context = ctx.context
        current_file = getattr(context, "current_file", None)

        if current_file:
            return {
                "path": current_file.path,
                "content": current_file.content,
                "size": len(current_file.content),
                "is_directory": False,
            }
        return {"path": "", "content": "", "size": 0, "is_directory": False}


@function_tool
async def navigate_to_found_file(ctx: RunContextWrapper[Any], file_path: None) -> str:
    """
    Navigate to (open) a specific file in the editor.
    Use this after finding files with find_in_project to open them.

    Args:
        file_path: Path to the file to navigate to

    Returns:
        Success or error message
    """
    with trace(
        workflow_name="Tool: navigate_to_found_file", metadata={"path": file_path}
    ):
        try:
            # Get the agent panel (which has our focus_file method)
            agent_panel = ctx.app.query_one("#agent-panel")

            # Use the async method to focus the file
            await agent_panel.focus_file(file_path)

            return f"Successfully opened file: {file_path}"
        except Exception as e:
            return f"Error navigating to file: {str(e)}"


@function_tool
async def find_in_project(
    ctx: RunContextWrapper[Any],
    search_pattern: str,
    file_pattern: str = None,
    max_results: int = None,
) -> List[FileInfo]:
    """
    Search for files matching a pattern in the project directory.

    Args:
        search_pattern: Text to search for in files
        file_pattern: File pattern to match (e.g., "*.py", "*.md")
        max_results: Maximum number of results to return

    Returns:
        List of matching files with content snippets
    """
    with trace(
        workflow_name="Tool: find_in_project", metadata={"pattern": search_pattern}
    ):
        try:
            # Determine the project directory
            project_root = "."
            if hasattr(ctx.context, "project") and hasattr(
                ctx.context.project, "root_path"
            ):
                if ctx.context.project.root_path:
                    project_root = ctx.context.project.root_path

            # Use grep or similar to search files
            cmd = ["grep", "-r", "-l", search_pattern]

            # Add file pattern filtering
            if file_pattern != "*":
                cmd.extend(["--include", file_pattern])

            # Set the directory to search
            cmd.append(project_root)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            matching_files = []
            count = 0

            for file_path in result.stdout.strip().split("\n"):
                if not file_path or count >= max_results:
                    break

                path = Path(file_path.strip())
                if path.exists() and path.is_file():
                    try:
                        # Read file content
                        content = path.read_text(encoding="utf-8", errors="replace")

                        # Extract a snippet containing the matched text
                        lines = content.splitlines()
                        snippet_lines = []
                        found = False

                        for i, line in enumerate(lines):
                            if search_pattern.lower() in line.lower():
                                # Add context before and after the matching line
                                start = max(0, i - 2)
                                end = min(len(lines), i + 3)

                                if start > 0:
                                    snippet_lines.append("...")

                                snippet_lines.extend(lines[start:end])

                                if end < len(lines):
                                    snippet_lines.append("...")

                                found = True
                                break

                        # If pattern not found in line-by-line search, just include first few lines
                        if not found:
                            snippet_lines = lines[:5] + (
                                ["..."] if len(lines) > 5 else []
                            )

                        matching_files.append(
                            {
                                "path": str(path),
                                "content": "\n".join(snippet_lines),
                                "size": path.stat().st_size,
                                "is_directory": False,
                            }
                        )

                        count += 1

                    except Exception:
                        # Skip files that can't be read
                        continue

            return (
                matching_files
                if matching_files
                else [
                    {
                        "path": "",
                        "content": f"No files matching '{search_pattern}' were found.",
                        "size": 0,
                        "is_directory": False,
                    }
                ]
            )

        except Exception as e:
            return [
                {
                    "path": "",
                    "content": f"Error searching files: {str(e)}",
                    "size": 0,
                    "is_directory": False,
                }
            ]


def register_tools():
    """Register and return all available tools."""
    # Create proper tool objects from the function tools

    # Convert function tools to proper tool objects with name attributes
    def create_proper_tool(func):
        try:
            if hasattr(func, "name") and callable(
                getattr(func, "on_invoke_tool", None)
            ):
                # Already a proper FunctionTool
                return func

            # If it's a raw function, create a proper FunctionTool with explicit name
            if hasattr(func, "__name__"):
                # For function_tool decorated functions that need proper wrapping
                name = func.__name__
                description = func.__doc__ or f"Tool: {name}"

                # Import necessary tools from the Agents SDK
                from agents.tools import extract_params_schema_from_function

                # Try to get the proper schema if possible
                try:
                    params_schema = extract_params_schema_from_function(func)

                    # Clean up the schema to remove any default values that cause errors
                    if (
                        isinstance(params_schema, dict)
                        and "properties" in params_schema
                    ):
                        for prop_name, prop_schema in params_schema[
                            "properties"
                        ].items():
                            # Remove any 'default' keys that might cause issues
                            if "default" in prop_schema:
                                del prop_schema["default"]
                except Exception as schema_err:
                    print(f"Error extracting schema for {name}: {schema_err}")
                    params_schema = {
                        "type": "object",
                        "properties": {
                            "args": {
                                "type": "string",
                                "description": "Arguments for the tool",
                            }
                        },
                        "required": ["args"],
                    }

                # Create a proper FunctionTool wrapper
                return FunctionTool(
                    name=name,
                    description=description,
                    params_json_schema=params_schema,
                    on_invoke_tool=func,
                )

            # Return as is if we can't wrap it
            return func
        except Exception as e:
            print(f"Error creating tool wrapper: {e}")
            # Return the original function as fallback
            return func

    # Get the base tools
    base_tools = [
        read_file,
        write_file,
        list_directory,
        execute_python,
        get_current_file,
        navigate_to_found_file,
        find_in_project,  # Add our new search tool
    ]

    # Convert them to proper tools
    tools = [create_proper_tool(tool) for tool in base_tools]

    # Add IDE tools if available
    if IDE_TOOLS_AVAILABLE:
        ide_tools = extend_tools([])
        tools.extend([create_proper_tool(tool) for tool in ide_tools])

    return tools
