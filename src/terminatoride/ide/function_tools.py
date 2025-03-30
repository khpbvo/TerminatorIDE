"""
IDE Function Tools for TerminatorIDE.
These tools allow the AI agent to interact with the IDE environment.
"""

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from agents import RunContextWrapper, function_tool

from terminatoride.agent.context import AgentContext
from terminatoride.agent.tracing import trace
from terminatoride.utils.git_helpers import git_add, git_commit, git_init, is_git_repo

# File and Project Navigation Tools


@function_tool
async def navigate_to_file(ctx: RunContextWrapper[AgentContext], path: str) -> str:
    """
    Navigate to a specific file in the IDE.

    Args:
        path: Path to the file to navigate to

    Returns:
        Success or error message
    """
    with trace(workflow_name="Tool: navigate_to_file", metadata={"path": path}):
        try:
            file_path = Path(path).expanduser().resolve()

            if not file_path.exists():
                return f"Error: File {path} does not exist"

            if not file_path.is_file():
                return f"Error: {path} is not a file"

            # Update the context with the new file
            if isinstance(ctx.context, AgentContext) and hasattr(
                ctx.context, "update_current_file"
            ):
                content = file_path.read_text(encoding="utf-8", errors="replace")
                ctx.context.update_current_file(str(file_path), content)
                return f"Successfully navigated to {path}"
            else:
                return f"Navigated to {path}, but context update failed"
        except Exception as e:
            return f"Error navigating to file: {str(e)}"


@function_tool
async def create_new_file(
    ctx: RunContextWrapper[AgentContext], path: str, content: str = ""
) -> str:
    """
    Create a new file with optional initial content.

    Args:
        path: Path where the new file should be created
        content: Optional initial content for the file

    Returns:
        Success or error message
    """
    with trace(workflow_name="Tool: create_new_file", metadata={"path": path}):
        try:
            file_path = Path(path).expanduser().resolve()

            if file_path.exists():
                return f"Error: File {path} already exists"

            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the initial content
            file_path.write_text(content, encoding="utf-8")

            # Update the context with the new file
            if isinstance(ctx.context, AgentContext) and hasattr(
                ctx.context, "update_current_file"
            ):
                ctx.context.update_current_file(str(file_path), content)

            return f"Successfully created file {path}"
        except Exception as e:
            return f"Error creating file: {str(e)}"


@function_tool
async def change_directory(ctx: RunContextWrapper[AgentContext], path: str) -> str:
    """
    Change the current working directory.

    Args:
        path: Path to the directory to change to

    Returns:
        Success or error message
    """
    with trace(workflow_name="Tool: change_directory", metadata={"path": path}):
        try:
            dir_path = Path(path).expanduser().resolve()

            if not dir_path.exists():
                return f"Error: Directory {path} does not exist"

            if not dir_path.is_dir():
                return f"Error: {path} is not a directory"

            # Change the working directory
            os.chdir(str(dir_path))

            # Update the terminal context if available
            if isinstance(ctx.context, AgentContext) and hasattr(
                ctx.context, "terminal"
            ):
                ctx.context.terminal.current_directory = str(dir_path)

            return f"Successfully changed directory to {path}"
        except Exception as e:
            return f"Error changing directory: {str(e)}"


# Code Editing Operations


@function_tool
async def insert_at_cursor(ctx: RunContextWrapper[AgentContext], text: str) -> str:
    """
    Insert text at the current cursor position in the editor.

    Args:
        text: Text to insert at current cursor position

    Returns:
        Success or error message
    """
    with trace(
        workflow_name="Tool: insert_at_cursor", metadata={"text_length": len(text)}
    ):
        try:
            if (
                not isinstance(ctx.context, AgentContext)
                or not ctx.context.current_file
            ):
                return "Error: No file is currently open"

            content = ctx.context.current_file.content
            cursor_pos = ctx.context.current_file.cursor_position

            # Insert the text at the cursor position
            new_content = content[:cursor_pos] + text + content[cursor_pos:]
            new_cursor_pos = cursor_pos + len(text)

            # Update the file content and cursor position
            ctx.context.update_current_file(
                ctx.context.current_file.path, new_content, new_cursor_pos
            )

            return f"Successfully inserted {len(text)} characters at cursor position"
        except Exception as e:
            return f"Error inserting text: {str(e)}"


@function_tool
async def replace_text(
    ctx: RunContextWrapper[AgentContext],
    search_text: str,
    replace_text: str,
    line_range: Optional[List[int]] = None,
) -> str:
    """
    Replace occurrences of text in the current file.

    Args:
        search_text: Text to search for
        replace_text: Text to replace with
        line_range: Optional range of lines to limit the replacement [start, end]

    Returns:
        Success message with count of replacements made
    """
    with trace(
        workflow_name="Tool: replace_text",
        metadata={"search": search_text, "replace": replace_text},
    ):
        try:
            if (
                not isinstance(ctx.context, AgentContext)
                or not ctx.context.current_file
            ):
                return "Error: No file is currently open"

            content = ctx.context.current_file.content
            lines = content.splitlines(True)  # Keep line endings

            if line_range and len(line_range) == 2:
                start_line = max(0, line_range[0] - 1)  # Convert to 0-indexed
                end_line = min(len(lines), line_range[1])

                # Apply replacement only to the specified lines
                before_lines = lines[:start_line]
                target_lines = lines[start_line:end_line]
                after_lines = lines[end_line:]

                # Do the replacement
                replaced_lines = []
                for line in target_lines:
                    replaced_lines.append(line.replace(search_text, replace_text))

                # Count replacements
                count = sum(line.count(search_text) for line in target_lines)

                # Combine the lines back
                new_content = "".join(before_lines + replaced_lines + after_lines)
            else:
                # Apply replacement to the entire file
                new_content = content.replace(search_text, replace_text)
                count = content.count(search_text)

            # Update the file content
            ctx.context.update_current_file(
                ctx.context.current_file.path,
                new_content,
                ctx.context.current_file.cursor_position,
            )

            return f"Successfully replaced {count} occurrences of '{search_text}'"
        except Exception as e:
            return f"Error replacing text: {str(e)}"


@function_tool
async def replace_regex(
    ctx: RunContextWrapper[AgentContext],
    pattern: str,
    replace_text: str,
    line_range: Optional[List[int]] = None,
) -> str:
    """
    Replace text matching a regex pattern in the current file.

    Args:
        pattern: Regular expression pattern to search for
        replace_text: Text to replace with (can include capture groups)
        line_range: Optional range of lines to limit the replacement [start, end]

    Returns:
        Success message with count of replacements made
    """
    with trace(
        workflow_name="Tool: replace_regex",
        metadata={"pattern": pattern, "replace": replace_text},
    ):
        try:
            if (
                not isinstance(ctx.context, AgentContext)
                or not ctx.context.current_file
            ):
                return "Error: No file is currently open"

            content = ctx.context.current_file.content

            # Compile the regex pattern
            regex = re.compile(pattern)

            if line_range and len(line_range) == 2:
                lines = content.splitlines(True)  # Keep line endings
                start_line = max(0, line_range[0] - 1)  # Convert to 0-indexed
                end_line = min(len(lines), line_range[1])

                # Apply replacement only to the specified lines
                before_lines = lines[:start_line]
                target_content = "".join(lines[start_line:end_line])
                after_lines = lines[end_line:]

                # Count matches
                count = len(regex.findall(target_content))

                # Do the replacement
                replaced_content = regex.sub(replace_text, target_content)

                # Combine the content back
                new_content = (
                    "".join(before_lines) + replaced_content + "".join(after_lines)
                )
            else:
                # Count matches in the entire file
                count = len(regex.findall(content))

                # Apply replacement to the entire file
                new_content = regex.sub(replace_text, content)

            # Update the file content
            ctx.context.update_current_file(
                ctx.context.current_file.path,
                new_content,
                ctx.context.current_file.cursor_position,
            )

            return f"Successfully replaced {count} matches of pattern '{pattern}'"
        except re.error as e:
            return f"Error in regex pattern: {str(e)}"
        except Exception as e:
            return f"Error replacing text: {str(e)}"


@function_tool
async def move_cursor(ctx: RunContextWrapper[AgentContext], position: int) -> str:
    """
    Move the cursor to a specific position in the current file.

    Args:
        position: Character position to move the cursor to (0-indexed)

    Returns:
        Success or error message
    """
    with trace(workflow_name="Tool: move_cursor", metadata={"position": position}):
        try:
            if (
                not isinstance(ctx.context, AgentContext)
                or not ctx.context.current_file
            ):
                return "Error: No file is currently open"

            content = ctx.context.current_file.content

            # Validate position
            if position < 0:
                position = 0
            if position > len(content):
                position = len(content)

            # Update cursor position
            ctx.context.update_current_file(
                ctx.context.current_file.path, content, position
            )

            # Calculate line and column for better user feedback
            lines = content[:position].splitlines()
            if not lines:
                line, col = 1, 0
            else:
                line = len(lines)
                col = len(lines[-1])

            return f"Cursor moved to position {position} (line {line}, column {col})"
        except Exception as e:
            return f"Error moving cursor: {str(e)}"


# Search Operations


@function_tool
async def find_in_file(
    ctx: RunContextWrapper[AgentContext],
    search_text: str,
    case_sensitive: bool = False,
    whole_word: bool = False,
) -> str:
    """
    Find occurrences of text in the current file.

    Args:
        search_text: Text to search for
        case_sensitive: Whether the search should be case-sensitive
        whole_word: Whether to match whole words only

    Returns:
        Results with line numbers and matched lines
    """
    with trace(workflow_name="Tool: find_in_file", metadata={"search": search_text}):
        try:
            if (
                not isinstance(ctx.context, AgentContext)
                or not ctx.context.current_file
            ):
                return "Error: No file is currently open"

            content = ctx.context.current_file.content
            lines = content.splitlines()

            # Prepare regex pattern based on options
            if whole_word:
                pattern = r"\b" + re.escape(search_text) + r"\b"
            else:
                pattern = re.escape(search_text)

            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)

            # Find matches
            matches = []
            for i, line in enumerate(lines):
                if regex.search(line):
                    matches.append((i + 1, line.strip()))

            # Generate results
            if not matches:
                return f"No occurrences of '{search_text}' found"

            result = f"Found {len(matches)} occurrences of '{search_text}':\n\n"
            for line_num, line_text in matches:
                result += f"Line {line_num}: {line_text}\n"

            return result
        except re.error as e:
            return f"Error in search pattern: {str(e)}"
        except Exception as e:
            return f"Error searching file: {str(e)}"


@function_tool
async def find_in_project(
    ctx: RunContextWrapper[AgentContext],
    search_text: str,
    file_pattern: str = "*.*",
    case_sensitive: bool = False,
    exclude_patterns: Optional[List[str]] = None,
) -> str:
    """
    Find occurrences of text across files in the project.

    Args:
        search_text: Text to search for
        file_pattern: Pattern to filter files (e.g., "*.py")
        case_sensitive: Whether the search should be case-sensitive
        exclude_patterns: Patterns to exclude (e.g., ["venv/*", "*.pyc"])

    Returns:
        Results with file paths, line numbers, and matched lines
    """
    with trace(
        workflow_name="Tool: find_in_project",
        metadata={"search": search_text, "pattern": file_pattern},
    ):
        try:
            if not isinstance(ctx.context, AgentContext) or not hasattr(
                ctx.context, "project"
            ):
                return "Error: No project context available"

            project_root = ctx.context.project.root_path
            if not project_root:
                return "Error: Project root path is not set"

            root_path = Path(project_root)
            if not root_path.exists() or not root_path.is_dir():
                return f"Error: Project root '{project_root}' is not a valid directory"

            # Prepare regex for search text
            flags = 0 if case_sensitive else re.IGNORECASE
            search_regex = re.compile(re.escape(search_text), flags)

            # Convert file pattern to regex
            file_pattern_regex = re.compile(fnmatch_to_regex(file_pattern))

            # Prepare exclude patterns
            exclude_regexes = []
            if exclude_patterns:
                for pattern in exclude_patterns:
                    exclude_regexes.append(re.compile(fnmatch_to_regex(pattern)))

            # Add default exclusions for common files to ignore
            default_excludes = [
                r"\.git/",
                r"\.venv/",
                r"venv/",
                r"__pycache__/",
                r"\.pyc$",
                r"\.pyo$",
                r"\.pyd$",
                r"\.so$",
                r"\.dll$",
                r"\.exe$",
            ]
            for pattern in default_excludes:
                exclude_regexes.append(re.compile(pattern))

            # Find files matching the pattern
            matches = []
            files_searched = 0

            for file_path in root_path.rglob("*"):
                # Skip directories
                if file_path.is_dir():
                    continue

                # Check if file matches the pattern
                rel_path = str(file_path.relative_to(root_path))
                if not file_pattern_regex.match(file_path.name):
                    continue

                # Check if file should be excluded
                should_exclude = False
                for exclude_regex in exclude_regexes:
                    if exclude_regex.search(rel_path):
                        should_exclude = True
                        break

                if should_exclude:
                    continue

                # Search within the file
                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                    files_searched += 1

                    lines = content.splitlines()
                    for i, line in enumerate(lines):
                        if search_regex.search(line):
                            matches.append((rel_path, i + 1, line.strip()))
                except Exception:
                    # Skip files that can't be read
                    continue

            # Generate results
            if not matches:
                return (
                    f"No occurrences of '{search_text}' found in {files_searched} files"
                )

            result = f"Found {len(matches)} occurrences of '{search_text}' in {files_searched} files:\n\n"
            for file_path, line_num, line_text in matches:
                result += f"{file_path}:{line_num}: {line_text}\n"

            return result
        except Exception as e:
            return f"Error searching project: {str(e)}"


# Git Operations


@function_tool
async def git_status(ctx: RunContextWrapper[AgentContext]) -> str:
    """
    Get the status of the git repository.

    Returns:
        Git status information
    """
    with trace(workflow_name="Tool: git_status"):
        try:
            if not isinstance(ctx.context, AgentContext) or not hasattr(
                ctx.context, "project"
            ):
                return "Error: No project context available"

            project_root = ctx.context.project.root_path
            if not project_root:
                return "Error: Project root path is not set"

            if not is_git_repo(Path(project_root)):
                return f"The project at '{project_root}' is not a git repository"

            result = subprocess.run(
                ["git", "status"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                return f"Git status error: {result.stderr}"

            return result.stdout
        except Exception as e:
            return f"Error getting git status: {str(e)}"


@function_tool
async def git_stage_file(ctx: RunContextWrapper[AgentContext], file_path: str) -> str:
    """
    Stage a file for commit in git.

    Args:
        file_path: Path to the file to stage

    Returns:
        Success or error message
    """
    with trace(workflow_name="Tool: git_stage_file", metadata={"path": file_path}):
        try:
            if not isinstance(ctx.context, AgentContext) or not hasattr(
                ctx.context, "project"
            ):
                return "Error: No project context available"

            project_root = ctx.context.project.root_path
            if not project_root:
                return "Error: Project root path is not set"

            path = Path(project_root) / file_path

            if not is_git_repo(Path(project_root)):
                return f"The project at '{project_root}' is not a git repository"

            if not path.exists():
                return f"Error: File '{file_path}' does not exist"

            # Use the git_add helper function
            success = git_add(Path(project_root), [file_path])

            if success:
                return f"Successfully staged '{file_path}'"
            else:
                return f"Failed to stage '{file_path}'"
        except Exception as e:
            return f"Error staging file: {str(e)}"


# @function_tool
# async def git_commit(ctx: RunContextWrapper[AgentContext], message: str) -> str:
#     """
#     Commit staged changes to git.

#     Args:
#         message: Commit message

#     Returns:
#         Success or error message
#     """
#     with trace(workflow_name="Tool: git_commit", metadata={"message": message}):
#         try:
#             if not isinstance(ctx.context, AgentContext) or not hasattr(
#                 ctx.context, "project"
#             ):
#                 return "Error: No project context available"

#             project_root = ctx.context.project.root_path
#             if not project_root:
#                 return "Error: Project root path is not set"

#             if not is_git_repo(Path(project_root)):
#                 return f"The project at '{project_root}' is not a git repository"

#             # Use the git_commit helper function
#             success = git_commit(Path(project_root), message)

#             if success:
#                 return f"Successfully committed changes with message: '{message}'"
#             else:
#                 return "Failed to commit changes. Make sure there are staged changes."
#         except Exception as e:
#             return f"Error committing changes: {str(e)}"


@function_tool
async def git_initialize(ctx: RunContextWrapper[AgentContext]) -> str:
    """
    Initialize a new git repository in the current project.

    Returns:
        Success or error message
    """
    with trace(workflow_name="Tool: git_initialize"):
        try:
            if not isinstance(ctx.context, AgentContext) or not hasattr(
                ctx.context, "project"
            ):
                return "Error: No project context available"

            project_root = ctx.context.project.root_path
            if not project_root:
                return "Error: Project root path is not set"

            if is_git_repo(Path(project_root)):
                return f"The project at '{project_root}' is already a git repository"

            # Use the git_init helper function
            success = git_init(Path(project_root))

            if success:
                return f"Successfully initialized git repository at '{project_root}'"
            else:
                return f"Failed to initialize git repository at '{project_root}'"
        except Exception as e:
            return f"Error initializing git repository: {str(e)}"


# Project Management Tools


@function_tool
async def create_directory(ctx: RunContextWrapper[AgentContext], path: str) -> str:
    """
    Create a new directory.

    Args:
        path: Path to the directory to create

    Returns:
        Success or error message
    """
    with trace(workflow_name="Tool: create_directory", metadata={"path": path}):
        try:
            dir_path = Path(path).expanduser().resolve()

            if dir_path.exists():
                return f"Error: Path '{path}' already exists"

            # Create the directory
            dir_path.mkdir(parents=True, exist_ok=True)

            return f"Successfully created directory at '{path}'"
        except Exception as e:
            return f"Error creating directory: {str(e)}"


@function_tool
async def run_command(
    ctx: RunContextWrapper[AgentContext],
    command: str,
    working_dir: Optional[str] = None,
) -> str:
    """
    Run a shell command and return the output.

    Args:
        command: The command to run
        working_dir: Optional working directory for the command

    Returns:
        Command output or error message
    """
    with trace(workflow_name="Tool: run_command", metadata={"command": command}):
        try:
            # Set working directory
            if working_dir:
                cwd = Path(working_dir).expanduser().resolve()
                if not cwd.exists() or not cwd.is_dir():
                    return f"Error: Working directory '{working_dir}' is not valid"
            elif isinstance(ctx.context, AgentContext) and hasattr(
                ctx.context, "project"
            ):
                cwd = ctx.context.project.root_path
            else:
                cwd = None

            # Run the command
            result = subprocess.run(
                command,
                shell=True,  # Use shell for convenience
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30,  # Set a reasonable timeout
            )

            # Capture command output
            output = ""
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"

            # Update terminal context if available
            if isinstance(ctx.context, AgentContext) and hasattr(
                ctx.context, "terminal"
            ):
                ctx.context.terminal.last_command = command
                ctx.context.terminal.last_output = output

            return f"Command completed with exit code {result.returncode}\n\n{output}"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 30 seconds"
        except Exception as e:
            return f"Error running command: {str(e)}"


@function_tool
async def rename_file(
    ctx: RunContextWrapper[AgentContext], source: str, destination: str
) -> str:
    """
    Rename or move a file or directory.

    Args:
        source: Path to the source file or directory
        destination: Path to the destination

    Returns:
        Success or error message
    """
    with trace(
        workflow_name="Tool: rename_file",
        metadata={"source": source, "destination": destination},
    ):
        try:
            src_path = Path(source).expanduser().resolve()
            dst_path = Path(destination).expanduser().resolve()

            if not src_path.exists():
                return f"Error: Source path '{source}' does not exist"

            if dst_path.exists():
                return f"Error: Destination path '{destination}' already exists"

            # Create parent directories if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)

            # Rename/move the file or directory
            shutil.move(str(src_path), str(dst_path))

            # If this was the current file, update the context
            if (
                isinstance(ctx.context, AgentContext)
                and ctx.context.current_file
                and ctx.context.current_file.path == str(src_path)
            ):
                content = ctx.context.current_file.content
                ctx.context.update_current_file(str(dst_path), content)

            return f"Successfully moved '{source}' to '{destination}'"
        except Exception as e:
            return f"Error renaming/moving file: {str(e)}"


@function_tool
async def delete_file(
    ctx: RunContextWrapper[AgentContext], path: str, recursive: bool = False
) -> str:
    """
    Delete a file or directory.

    Args:
        path: Path to the file or directory to delete
        recursive: Whether to recursively delete directories

    Returns:
        Success or error message
    """
    with trace(
        workflow_name="Tool: delete_file",
        metadata={"path": path, "recursive": recursive},
    ):
        try:
            file_path = Path(path).expanduser().resolve()

            if not file_path.exists():
                return f"Error: Path '{path}' does not exist"

            if file_path.is_file():
                file_path.unlink()
                return f"Successfully deleted file '{path}'"
            elif file_path.is_dir():
                if recursive:
                    shutil.rmtree(file_path)
                    return (
                        f"Successfully deleted directory '{path}' and all its contents"
                    )
                else:
                    try:
                        file_path.rmdir()  # Will only succeed if directory is empty
                        return f"Successfully deleted empty directory '{path}'"
                    except OSError:
                        return f"Error: Directory '{path}' is not empty. Use recursive=True to delete non-empty directories."

            return f"Unknown path type for '{path}'"
        except Exception as e:
            return f"Error deleting path: {str(e)}"


# Helpers


def fnmatch_to_regex(pattern: str) -> str:
    """
    Convert a glob pattern like "*.py" to a regex pattern.

    Args:
        pattern: Glob pattern (e.g., "*.py", "src/**/*.js")

    Returns:
        Equivalent regex pattern
    """
    # Escape all regex special chars except * and ?
    pattern = re.escape(pattern).replace(r"\*", ".*").replace(r"\?", ".")

    # Handle ** (for recursive directory matching)
    pattern = pattern.replace(r".*.*", r".*")

    # Ensure it matches the entire string
    return f"^{pattern}$"


# Register all tools
def register_ide_tools() -> List:
    """Register and return all IDE operation tools."""
    return [
        # File and Project Navigation
        navigate_to_file,
        create_new_file,
        change_directory,
        # Code Editing
        insert_at_cursor,
        replace_text,
        replace_regex,
        move_cursor,
        # Search
        find_in_file,
        find_in_project,
        # Git
        git_status,
        git_stage_file,
        git_commit,
        git_initialize,
        # Project Management
        create_directory,
        run_command,
        rename_file,
        delete_file,
    ]
