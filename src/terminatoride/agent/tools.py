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

def register_tools():
    """Register and return all available tools."""
    return [
        read_file,
        write_file,
        list_directory,
        execute_python,
        get_current_file
    ]
