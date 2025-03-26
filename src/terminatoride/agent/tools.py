"""
Tool implementations for TerminatorIDE agents.
These tools allow agents to interact with the IDE environment.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, TypedDict
import subprocess

from agents import function_tool, RunContextWrapper
from pydantic import BaseModel

class FileInfo(TypedDict):
    path: str
    content: str
    size: int
    is_directory: bool

class SearchResult(TypedDict):
    path: str
    line_number: int
    content: str
    context: str

@function_tool
async def read_file(ctx: RunContextWrapper[Any], path: str) -> str:
    """
    Read the contents of a file.
    
    Args:
        path: Path to the file to read
    
    Returns:
        The contents of the file as a string
    """
    try:
        file_path = Path(path).expanduser().resolve()
        return file_path.read_text(encoding='utf-8')
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
    try:
        file_path = Path(path).expanduser().resolve()
        
        # Make parent directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_path.write_text(content, encoding='utf-8')
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing to file: {str(e)}"

@function_tool
async def list_directory(ctx: RunContextWrapper[Any], path: str = ".", 
                        show_hidden: bool = False) -> List[FileInfo]:
    """
    List files and directories in the given path.
    
    Args:
        path: Directory path to list
        show_hidden: Whether to include hidden files
        
    Returns:
        List of file and directory information
    """
    try:
        dir_path = Path(path).expanduser().resolve()
        result = []
        
        for item in dir_path.iterdir():
            if not show_hidden and item.name.startswith('.'):
                continue
                
            try:
                info = {
                    "path": str(item),
                    "is_directory": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else 0,
                    "content": "" if item.is_dir() else (item.read_text(encoding='utf-8', errors='replace') if item.suffix in ['.txt', '.py', '.md', '.json'] and item.stat().st_size < 100000 else "File too large to display")
                }
                result.append(info)
            except Exception as e:
                # Skip files that can't be accessed
                continue
                
        return result
    except Exception as e:
        return [{"path": str(path), "content": f"Error listing directory: {str(e)}", "size": 0, "is_directory": False}]

@function_tool
async def execute_python(ctx: RunContextWrapper[Any], code: str) -> str:
    """
    Execute Python code and return the result.
    
    Args:
        code: Python code to execute
        
    Returns:
        Output from running the code
    """
    try:
        # Create a temporary file for the code
        tmp_file = Path("./tmp_execution.py")
        tmp_file.write_text(code, encoding='utf-8')
        
        # Execute the code in a separate process with a timeout
        result = subprocess.run(
            [sys.executable, str(tmp_file)],
            capture_output=True,
            text=True,
            timeout=5
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
async def get_current_file(ctx: RunContextWrapper[Any]) -> FileInfo:
    """
    Get information about the currently open file in the editor.
    
    Returns:
        Information about the current file
    """
    # This will be updated to get the actual current file in the editor
    # For now, return a placeholder
    context = ctx.context
    current_file = getattr(context, "current_file", None)
    
    if current_file:
        return {
            "path": current_file.path,
            "content": current_file.content,
            "size": len(current_file.content),
            "is_directory": False
        }
    return {
        "path": "",
        "content": "",
        "size": 0,
        "is_directory": False
    }

@function_tool
async def search_in_files(ctx: RunContextWrapper[Any], pattern: str, 
                         file_pattern: str = "*.py", 
                         search_dir: str = ".") -> List[SearchResult]:
    """
    Search for a pattern in files matching the given pattern.
    
    Args:
        pattern: Text or regex pattern to search for
        file_pattern: File pattern to match (e.g. "*.py")
        search_dir: Directory to search in
        
    Returns:
        List of search results with matching lines and context
    """
    try:
        import re
        search_path = Path(search_dir).expanduser().resolve()
        results = []
        
        for path in search_path.rglob(file_pattern):
            if not path.is_file():
                continue
                
            try:
                content = path.read_text(encoding='utf-8', errors='replace')
                lines = content.splitlines()
                
                for i, line in enumerate(lines):
                    if re.search(pattern, line):
                        # Get context (a few lines before and after)
                        start = max(0, i-2)
                        end = min(len(lines), i+3)
                        context_lines = lines[start:end]
                        
                        results.append({
                            "path": str(path),
                            "line_number": i + 1,
                            "content": line,
                            "context": "\n".join(f"{j+start+1}: {l}" for j, l in enumerate(context_lines))
                        })
            except Exception as e:
                # Skip files that can't be read
                continue
                
        return results
    except Exception as e:
        return [{"path": "", "line_number": 0, "content": f"Error searching files: {str(e)}", "context": ""}]

@function_tool
async def git_status(ctx: RunContextWrapper[Any], repo_path: str = ".") -> str:
    """
    Get the git status of a repository.
    
    Args:
        repo_path: Path to the git repository
        
    Returns:
        Git status output
    """
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "status"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return f"Error getting git status: {result.stderr}"
            
        return result.stdout
    except Exception as e:
        return f"Error: {str(e)}"

@function_tool
async def update_editor_content(ctx: RunContextWrapper[Any], content: str) -> str:
    """
    Update the content of the current editor.
    
    Args:
        content: New content to put in the editor
        
    Returns:
        Success message or error
    """
    try:
        # This will be connected to the UI in the future
        # For now, store in context
        context = ctx.context
        current_file = getattr(context, "current_file", None)
        
        if current_file and hasattr(current_file, "update_content"):
            current_file.update_content(content)
            return "Editor content updated successfully"
        
        return "Editor content will be updated when implemented"
    except Exception as e:
        return f"Error updating editor content: {str(e)}"

@function_tool
async def run_terminal_command(ctx: RunContextWrapper[Any], command: str, 
                              working_dir: str = ".") -> Dict[str, str]:
    """
    Run a command in the terminal.
    
    Args:
        command: Command to run
        working_dir: Working directory for the command
        
    Returns:
        Dictionary with stdout and stderr
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=working_dir,
            timeout=30  # Timeout after 30 seconds
        )
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": "Command timed out after 30 seconds",
            "return_code": -1,
            "success": False
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"Error: {str(e)}",
            "return_code": -1,
            "success": False
        }

def register_tools():
    """Register and return all available tools."""
    return [
        read_file,
        write_file,
        list_directory,
        execute_python,
        get_current_file,
        search_in_files,
        git_status,
        update_editor_content,
        run_terminal_command
    ]
