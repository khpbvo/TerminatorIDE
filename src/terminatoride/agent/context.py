"""
Context management for TerminatorIDE agents.
Provides shared context between the IDE and agents.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path

@dataclass
class FileContext:
    """Context for a file being edited."""
    path: str
    content: str = ""
    language: str = ""
    cursor_position: int = 0
    
    @property
    def filename(self) -> str:
        """Get the file name without path."""
        return Path(self.path).name
    
    @property
    def extension(self) -> str:
        """Get the file extension."""
        return Path(self.path).suffix.lstrip('.')

@dataclass
class ProjectContext:
    """Context for the current project."""
    root_path: str = ""
    git_enabled: bool = False
    current_branch: Optional[str] = None
    
    def is_initialized(self) -> bool:
        """Check if the project context is initialized."""
        return bool(self.root_path)

@dataclass
class TerminalContext:
    """Context for the terminal."""
    last_command: str = ""
    last_output: str = ""
    current_directory: str = ""

@dataclass
class EditorContext:
    """Context for the editor."""
    last_search: str = ""
    selection: str = ""

@dataclass
class AgentContext:
    """
    Comprehensive context for agents in TerminatorIDE.
    This context is passed to agents during execution.
    """
    current_file: Optional[FileContext] = None
    project: ProjectContext = field(default_factory=ProjectContext)
    terminal: TerminalContext = field(default_factory=TerminalContext)
    editor: EditorContext = field(default_factory=EditorContext)
    
    # Keep track of recent files
    recent_files: List[FileContext] = field(default_factory=list)
    
    # Custom metadata for agent usage
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_current_file(self, path: str, content: str, cursor_position: int = 0):
        """Update the current file context."""
        if not self.current_file or self.current_file.path != path:
            # Create a new file context
            self.current_file = FileContext(
                path=path,
                content=content,
                cursor_position=cursor_position,
                language=Path(path).suffix.lstrip('.')
            )
            
            # Add to recent files, removing if already exists
            self.recent_files = [f for f in self.recent_files if f.path != path]
            self.recent_files.insert(0, self.current_file)
            
            # Limit recent files to 10
            if len(self.recent_files) > 10:
                self.recent_files.pop()
        else:
            # Update existing file context
            self.current_file.content = content
            self.current_file.cursor_position = cursor_position
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata for agent context."""
        self.metadata[key] = value
        
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from agent context."""
        return self.metadata.get(key, default)
