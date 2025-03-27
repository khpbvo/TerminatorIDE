"""File operations utility for TerminatorIDE."""

import os
import shutil
from pathlib import Path
from typing import Union, Optional, Tuple

class FileOperations:
    """Utility class for file operations."""
    
    @staticmethod
    def create_file(path: Union[str, Path], content: str = "") -> Tuple[bool, str]:
        """Create a new file.
        
        Args:
            path: The path to the file to create.
            content: Optional initial content for the file.
            
        Returns:
            A tuple of (success, message).
        """
        try:
            path = Path(path)
            
            # Check if file already exists
            if path.exists():
                return False, f"File {path} already exists."
            
            # Create parent directories if they don't exist
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create the file with the specified content
            with open(path, "w") as f:
                f.write(content)
            
            return True, f"File {path.name} created successfully."
        except Exception as e:
            return False, f"Error creating file: {str(e)}"
    
    @staticmethod
    def create_directory(path: Union[str, Path]) -> Tuple[bool, str]:
        """Create a new directory.
        
        Args:
            path: The path to the directory to create.
            
        Returns:
            A tuple of (success, message).
        """
        try:
            path = Path(path)
            
            # Check if directory already exists
            if path.exists():
                return False, f"Directory {path} already exists."
            
            # Create the directory and parents if they don't exist
            path.mkdir(parents=True, exist_ok=True)
            
            return True, f"Directory {path.name} created successfully."
        except Exception as e:
            return False, f"Error creating directory: {str(e)}"
    
    @staticmethod
    def rename(src: Union[str, Path], dst: Union[str, Path]) -> Tuple[bool, str]:
        """Rename a file or directory.
        
        Args:
            src: The source path to rename.
            dst: The destination path.
            
        Returns:
            A tuple of (success, message).
        """
        try:
            src = Path(src)
            dst = Path(dst)
            
            # Check if source exists
            if not src.exists():
                return False, f"{src} does not exist."
            
            # Check if destination already exists
            if dst.exists():
                return False, f"{dst} already exists."
            
            # Rename (move) the file or directory
            src.rename(dst)
            
            return True, f"Renamed {src.name} to {dst.name} successfully."
        except Exception as e:
            return False, f"Error renaming: {str(e)}"
    
    @staticmethod
    def delete(path: Union[str, Path], recursive: bool = True) -> Tuple[bool, str]:
        """Delete a file or directory.
        
        Args:
            path: The path to delete.
            recursive: Whether to delete directories recursively.
            
        Returns:
            A tuple of (success, message).
        """
        try:
            path = Path(path)
            
            # Check if path exists
            if not path.exists():
                return False, f"{path} does not exist."
            
            # Delete file or directory
            if path.is_file():
                path.unlink()
                return True, f"File {path.name} deleted successfully."
            elif path.is_dir():
                if recursive:
                    shutil.rmtree(path)
                    return True, f"Directory {path.name} deleted successfully."
                else:
                    path.rmdir()  # Will only work if directory is empty
                    return True, f"Empty directory {path.name} deleted successfully."
            
            return False, f"Unknown path type: {path}."
        except Exception as e:
            return False, f"Error deleting: {str(e)}"
    
    @staticmethod
    def copy(src: Union[str, Path], dst: Union[str, Path]) -> Tuple[bool, str]:
        """Copy a file or directory.
        
        Args:
            src: The source path to copy.
            dst: The destination path.
            
        Returns:
            A tuple of (success, message).
        """
        try:
            src = Path(src)
            dst = Path(dst)
            
            # Check if source exists
            if not src.exists():
                return False, f"{src} does not exist."
            
            # Check if destination already exists
            if dst.exists():
                return False, f"{dst} already exists."
            
            # Copy file or directory
            if src.is_file():
                shutil.copy2(src, dst)
                return True, f"File {src.name} copied to {dst} successfully."
            elif src.is_dir():
                shutil.copytree(src, dst)
                return True, f"Directory {src.name} copied to {dst} successfully."
            
            return False, f"Unknown path type: {src}."
        except Exception as e:
            return False, f"Error copying: {str(e)}" 