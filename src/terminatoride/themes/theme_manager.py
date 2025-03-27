"""Theme manager for TerminatorIDE."""

from typing import Any, Callable, Dict

from textual.app import App

from . import DEFAULT_THEME


class ThemeManager:
    """Manages application themes."""

    def __init__(self, app: App):
        """Initialize the theme manager.

        Args:
            app: The Textual app instance.
        """
        self.app = app
        self.current_theme = "dark"
        self.themes = DEFAULT_THEME.copy()
        self.on_theme_change_callbacks = []

    def set_theme(self, theme_name: str) -> bool:
        """Set the current theme.

        Args:
            theme_name: The name of the theme to set.

        Returns:
            True if the theme was set successfully, False otherwise.
        """
        if theme_name not in self.themes:
            return False

        self.current_theme = theme_name
        self.app.dark = theme_name == "dark"

        # We don't update CSS variables directly as this is not supported
        # in the current Textual version. Instead, we rely on Textual's
        # built-in dark mode support and our CSS classes.

        # Call theme change callbacks
        for callback in self.on_theme_change_callbacks:
            callback(theme_name, self.themes[theme_name])

        return True

    def toggle_theme(self) -> str:
        """Toggle between light and dark themes.

        Returns:
            The name of the new theme.
        """
        new_theme = "light" if self.current_theme == "dark" else "dark"
        self.set_theme(new_theme)
        return new_theme

    def get_current_theme(self) -> Dict[str, Any]:
        """Get the current theme colors.

        Returns:
            A dictionary of theme colors.
        """
        return self.themes[self.current_theme]

    def register_theme(self, name: str, colors: Dict[str, str]) -> bool:
        """Register a new theme.

        Args:
            name: The name of the theme.
            colors: The colors for the theme.

        Returns:
            True if the theme was registered successfully, False otherwise.
        """
        if name in self.themes:
            return False

        self.themes[name] = colors
        return True

    def on_theme_change(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Register a callback for theme changes.

        Args:
            callback: The callback function to call when the theme changes.
        """
        self.on_theme_change_callbacks.append(callback)
