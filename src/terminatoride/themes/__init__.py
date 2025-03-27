"""Themes for TerminatorIDE."""

from typing import Dict, Any

# Base theme colors
DEFAULT_THEME = {
    "dark": {
        "background": "#1e1e2e",
        "foreground": "#cdd6f4",
        "primary": "#89b4fa",
        "secondary": "#f5c2e7",
        "accent": "#f38ba8",
        "surface": "#313244",
        "surface-darken-1": "#181825",
        "text": "#cdd6f4",
        "success": "#a6e3a1",
        "warning": "#f9e2af",
        "error": "#f38ba8",
        "info": "#89b4fa",
    },
    "light": {
        "background": "#eff1f5",
        "foreground": "#4c4f69",
        "primary": "#1e66f5",
        "secondary": "#ea76cb",
        "accent": "#d20f39",
        "surface": "#dce0e8",
        "surface-darken-1": "#ccd0da",
        "text": "#4c4f69",
        "success": "#40a02b",
        "warning": "#df8e1d",
        "error": "#d20f39",
        "info": "#1e66f5",
    }
}

def get_theme_colors(theme_name: str = "dark") -> Dict[str, Any]:
    """Get the colors for a theme.
    
    Args:
        theme_name: The name of the theme ("dark" or "light").
        
    Returns:
        A dictionary of theme colors.
    """
    if theme_name in DEFAULT_THEME:
        return DEFAULT_THEME[theme_name]
    return DEFAULT_THEME["dark"]  # Default to dark theme 