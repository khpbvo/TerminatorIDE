"""Editor panel for TerminatorIDE with advanced code editing capabilities."""

import importlib.util
import os
import re
import time
from pathlib import Path

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Input, Label, Static, TextArea
from textual.widgets.text_area import Selection, TextAreaTheme

# Try to import rich syntax highlighting components
try:
    from pygments.lexers import get_all_lexers
    from rich.syntax import Syntax

    HAS_PYGMENTS = True
except ImportError:
    HAS_PYGMENTS = False

# Try to import pylint for Python linting
# try:
#    import pylint
#    from pylint.lint import Run as PylintRun
#    from pylint.reporters.text import TextReporter

#    HAS_PYLINT = True
# except ImportError:
#    HAS_PYLINT = False


class EditorPanel(Container):
    """The middle panel of the IDE containing a fully-featured code editor."""

    # Adding bracket pairs for auto-closing
    BRACKET_PAIRS = {
        "(": ")",
        "[": "]",
        "{": "}",
        '"': '"',
        "'": "'",
        "`": "`",
    }

    # Keywords for various languages for basic auto-completion
    LANGUAGE_KEYWORDS = {
        "python": [
            "and",
            "as",
            "assert",
            "async",
            "await",
            "break",
            "class",
            "continue",
            "def",
            "del",
            "elif",
            "else",
            "except",
            "False",
            "finally",
            "for",
            "from",
            "global",
            "if",
            "import",
            "in",
            "is",
            "lambda",
            "None",
            "nonlocal",
            "not",
            "or",
            "pass",
            "raise",
            "return",
            "True",
            "try",
            "while",
            "with",
            "yield",
        ],
        "javascript": [
            "await",
            "break",
            "case",
            "catch",
            "class",
            "const",
            "continue",
            "debugger",
            "default",
            "delete",
            "do",
            "else",
            "export",
            "extends",
            "false",
            "finally",
            "for",
            "function",
            "if",
            "import",
            "in",
            "instanceof",
            "new",
            "null",
            "return",
            "super",
            "switch",
            "this",
            "throw",
            "true",
            "try",
            "typeof",
            "var",
            "void",
            "while",
            "with",
            "yield",
        ],
    }

    # Python snippets for auto-completion
    SNIPPETS = {
        "python": {
            "def": "def function_name(args):\n    pass",
            "class": "class ClassName:\n    def __init__(self):\n        pass",
            "if": "if condition:\n    pass",
            "for": "for item in iterable:\n    pass",
            "while": "while condition:\n    pass",
            "try": "try:\n    pass\nexcept Exception as e:\n    pass",
            "with": "with expression as variable:\n    pass",
            "import": "import module",
            "from": "from module import name",
            "print": 'print(f"{}")',
        },
        "javascript": {
            "func": "function name() {\n    \n}",
            "arrow": "const name = () => {\n    \n}",
            "if": "if (condition) {\n    \n}",
            "for": "for (let i = 0; i < array.length; i++) {\n    \n}",
            "forin": "for (const item in object) {\n    \n}",
            "forof": "for (const item of array) {\n    \n}",
            "while": "while (condition) {\n    \n}",
            "class": "class Name {\n    constructor() {\n        \n    }\n}",
            "try": "try {\n    \n} catch (error) {\n    \n}",
            "log": "console.log();",
        },
    }

    # Define custom themes
    CUSTOM_THEMES = {
        "terminator_dark": {
            "background": "#1a1a1a",
            "foreground": "#f8f8f2",
            "cursor": "#f8f8f0",
            "cursor-line": "#2a2a2a",
            "gutter": "#1a1a1a",
            "gutter-foreground": "#75715e",
            "gutter-foreground-highlight": "#f8f8f2",
            "gutter-background": "#272822",
            "selection-foreground": "#f8f8f2",
            "selection-background": "#44475a",
            "selection-foreground-active": "#f8f8f2",
            "selection-background-active": "#6272a4",
            "bracket-foreground": "#f8f8f2",
            "bracket-background": "#44475a",
        },
        "terminator_light": {
            "background": "#f8f8f2",
            "foreground": "#272822",
            "cursor": "#272822",
            "cursor-line": "#f5f5f5",
            "gutter": "#f8f8f2",
            "gutter-foreground": "#75715e",
            "gutter-foreground-highlight": "#272822",
            "gutter-background": "#f0f0f0",
            "selection-foreground": "#272822",
            "selection-background": "#c2c2c2",
            "selection-foreground-active": "#272822",
            "selection-background-active": "#a6a6a6",
            "bracket-foreground": "#272822",
            "bracket-background": "#c2c2c2",
        },
    }

    # Keyboard shortcuts help
    KEYBOARD_SHORTCUTS = [
        ("Ctrl+S", "Save File"),
        ("Ctrl+Z", "Undo"),
        ("Ctrl+Y", "Redo"),
        ("Ctrl+F", "Find"),
        ("Ctrl+H", "Replace"),
        ("F3", "Find Next"),
        ("Shift+F3", "Find Previous"),
        ("Ctrl+G", "Go to Line"),
        ("Ctrl+/", "Toggle Comment"),
        ("Ctrl+D", "Duplicate Line"),
        ("Ctrl+A", "Select All"),
        ("Ctrl+Shift+K", "Delete Line"),
        ("Ctrl+Home", "Go to Start"),
        ("Ctrl+End", "Go to End"),
        ("Alt+Z", "Toggle Word Wrap"),
        ("Alt+L", "Toggle Line Numbers"),
        ("Ctrl+Space", "Show Completions"),
        ("F1", "Show Keyboard Shortcuts"),
    ]

    # Code folding markers
    FOLD_MARKERS = {
        "python": [
            (r"^\s*class\s+\w+.*:", "class"),
            (r"^\s*def\s+\w+.*:", "function"),
            (r"^\s*if\s+.*:", "if"),
            (r"^\s*elif\s+.*:", "elif"),
            (r"^\s*else\s*:", "else"),
            (r"^\s*for\s+.*:", "for"),
            (r"^\s*while\s+.*:", "while"),
            (r"^\s*try\s*:", "try"),
            (r"^\s*except.*:", "except"),
            (r"^\s*finally\s*:", "finally"),
            (r"^\s*with\s+.*:", "with"),
        ],
        "javascript": [
            (r"^\s*function\s+\w+.*{", "function"),
            (r"^\s*class\s+\w+.*{", "class"),
            (r"^\s*if\s*\(.*\)\s*{", "if"),
            (r"^\s*else\s+if\s*\(.*\)\s*{", "else if"),
            (r"^\s*else\s*{", "else"),
            (r"^\s*for\s*\(.*\)\s*{", "for"),
            (r"^\s*while\s*\(.*\)\s*{", "while"),
            (r"^\s*try\s*{", "try"),
            (r"^\s*catch\s*\(.*\)\s*{", "catch"),
            (r"^\s*finally\s*{", "finally"),
            (r"{\s*$", "block"),
        ],
    }

    # Linting error markers
    LINT_ERROR_MARKER = "🔴"
    LINT_WARNING_MARKER = "🟠"
    LINT_INFO_MARKER = "🔵"

    DEFAULT_CSS = """
    EditorPanel {
        width: 100%;
        height: 100%;
        layout: grid;
        grid-rows: auto 1fr auto;
        grid-gutter: 0;
        background: #1e1e1e;
    }

    #editor-header {
        height: auto;
        background: #252526;
        color: #cccccc;
        padding: 0 1;
        border-bottom: solid #3f3f3f;
    }

    #editor-container {
        width: 100%;
        height: 100%;
    }

    #editor-footer {
        height: auto;
        background: #007acc;
        color: #ffffff;
        padding: 0 1;
    }

    #file-path {
        color: #cccccc;
    }

    #status-info {
        background: #007acc;
        color: #ffffff;
        text-align: right;
    }

    #language-display {
        background: #0d6efd;
        color: #ffffff;
        padding: 0 1;
        min-width: 10;
        text-align: center;
    }

    #position-display {
        background: #252526;
        color: #cccccc;
        padding: 0 1;
        min-width: 12;
        text-align: center;
    }

    TextArea {
        border: none;
        background: #1e1e1e;
        height: 100%;
    }

    Button {
        margin: 0 1 0 0;
    }

    /* Style for tooltip */
    .completion-tooltip {
        background: #252526;
        color: #cccccc;
        padding: 0 1;
        border: solid #3f3f3f;
    }

    .tooltip-item {
        padding: 0 1;
    }

    .tooltip-item.selected {
        background: #0d6efd;
        color: #ffffff;
    }

    #search-container {
        display: none;
        background: #252526;
        height: auto;
        padding: 1 1;
        border-bottom: solid #3f3f3f;
    }

    #search-container.visible {
        display: block;
    }

    #search-input, #replace-input {
        width: 30;
        margin-right: 1;
    }

    #search-info {
        color: #cccccc;
        margin-left: 1;
    }

    /* Theme selector */
    #theme-container {
        background: #252526;
        height: auto;
        padding: 0 1;
        border-top: solid #3f3f3f;
        display: none;
    }

    #theme-container.visible {
        display: block;
    }

    .theme-button {
        margin: 0 1 0 0;
    }

    /* Keyboard shortcuts dialog */
    #shortcuts-dialog {
        width: 60;
        height: 30;
        border: solid #3f3f3f;
        background: #252526;
        display: none;
    }

    #shortcuts-dialog.visible {
        display: block;
    }

    #shortcuts-title {
        background: #007acc;
        color: #ffffff;
        text-align: center;
        padding: 1 0;
    }

    .shortcut-row {
        height: 1;
        padding: 0 1;
    }

    .shortcut-key {
        background: #3f3f3f;
        color: #ffffff;
        min-width: 12;
        text-align: center;
        margin-right: 1;
    }

    .shortcut-description {
        color: #cccccc;
    }

    /* File operation buttons */
    #file-operations {
        display: block;
        background: #252526;
        height: auto;
        padding: 0 1;
        border-top: solid #3f3f3f;
    }

    /* Code folding */
    .fold-marker {
        background: #3f3f3f;
        color: #ffffff;
        text-style: bold;
        margin-right: 1;
    }

    /* Linting */
    .lint-error {
        text-style: bold;
        color: #ff0000;
        background: #330000;
        border-bottom: solid #ff0000;
    }

    .lint-warning {
        text-style: italic;
        color: #ffaa00;
        background: #332200;
        border-bottom: solid #ffaa00;
    }

    /* Code minimap */
    #minimap-container {
        width: 15;
        height: 100%;
        background: #1e1e1e;
        display: none;
    }

    #minimap-container.visible {
        display: block;
    }

    #minimap {
        width: 15;
        height: 100%;
        color: #8a8a8a;
        background: #1e1e1e;
        text-style: dim;
    }

    #viewport-indicator {
        width: 15;
        height: 5;
        background: #3f3f3f;
        opacity: 0.5;
        position: absolute;
    }
    """

    # Sample Python content for testing
    DEFAULT_CONTENT = '''# Welcome to Terminator IDE
# A powerful code editor in the terminal

def hello_world():
    """This is a sample Python function."""
    print("Hello, World!")
    return True

class Example:
    def __init__(self, name):
        self.name = name

    def greet(self):
        """Greet the user."""
        message = f"Hello, {self.name}!"
        print(message)
        return message

if __name__ == "__main__":
    # Create an example instance
    example = Example("Developer")
    example.greet()

    # Call the hello_world function
    result = hello_world()
    assert result == True, "The function should return True"
'''

    class FileChanged(Message):
        """Message sent when the file content is changed."""

        def __init__(self, path: str, content: str) -> None:
            self.path = path
            self.content = content
            super().__init__()

    class CursorMoved(Message):
        """Message sent when the cursor position changes."""

        def __init__(self, location: tuple[int, int]) -> None:
            self.row = location[0]
            self.column = location[1]
            super().__init__()

    # Reactive attributes for tracking state
    current_path = reactive("")
    current_language = reactive("python")
    current_line = reactive(1)
    current_column = reactive(1)
    is_modified = reactive(False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_file = None
        # Track if file has been modified since last save
        self._last_saved_content = ""
        # Auto-completion state
        self._completion_active = False
        self._completion_items = []
        self._completion_selected = 0
        self._completion_prefix = ""
        # Indentation tracking
        self._last_indent_level = 0
        # Search state
        self._search_results = []
        self._current_search_index = -1
        self._search_text = ""
        # Code folding state
        self._folded_regions = set()
        # Linting state
        self._lint_markers = {}
        self._last_lint_time = 0
        self._lint_delay = 1.0  # Seconds to wait before linting again
        # Minimap state
        self._minimap_visible = False
        self._register_custom_themes()

    def _register_custom_themes(self) -> None:
        """Register custom themes with the TextArea."""
        for theme_name, theme_values in self.CUSTOM_THEMES.items():
            try:
                theme = TextAreaTheme(**theme_values)
                TextArea.register_theme(theme_name, theme)
            except Exception as e:
                print(f"Error registering theme {theme_name}: {e}")

    def compose(self) -> ComposeResult:
        """Compose the editor panel widget."""
        # Header with file info
        with Container(id="editor-header"):
            yield Label("", id="file-path")

        # Search container (hidden by default)
        with Container(id="search-container"):
            with Horizontal():
                yield Input(placeholder="Search...", id="search-input")
                yield Input(placeholder="Replace with...", id="replace-input")
                yield Label("", id="search-info")

        # Main content area with editor and minimap
        with Horizontal(id="editor-main"):
            # Main editor
            with Container(id="editor-container"):
                yield TextArea.code_editor(
                    self.DEFAULT_CONTENT,
                    language="python",
                    theme="vscode_dark",
                    show_line_numbers=True,
                    tab_behavior="indent",
                    soft_wrap=False,
                    id="editor",
                )

            # Minimap (hidden by default)
            with Container(id="minimap-container"):
                yield Static("", id="minimap")
                yield Static("", id="viewport-indicator")

        # Footer with status info
        with Horizontal(id="editor-footer"):
            yield Label("Python", id="language-display")
            yield Label("Ln 1, Col 1", id="position-display")
            yield Label("UTF-8", id="status-info")

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        editor = self.query_one("#editor", TextArea)

        # Ensure all syntax highlighting is available
        self._initialize_syntax_highlighting()

        # Set initial selections and focus
        self._select_welcome_line(editor)
        editor.focus()

        # Initialize file path display
        self._update_file_path_display("Untitled")

        # Log available features
        self._log_available_features(editor)

        # Set up initial advanced features
        self._setup_minimap()

        # Schedule initial code quality check
        self.set_timer(1.0, self._schedule_lint_check)

    def _initialize_syntax_highlighting(self) -> None:
        """Initialize and ensure all syntax highlighting capabilities are available."""
        editor = self.query_one("#editor", TextArea)

        if not HAS_PYGMENTS:
            self.app.notify(
                "Pygments not installed. Some syntax highlighting features may be limited.",
                severity="warning",
                timeout=5,
            )
            return

        # Try to install additional language support if not available
        try:
            available_languages = getattr(editor, "available_languages", [])
            if callable(available_languages):
                available_languages = available_languages()

            # Log available languages and themes for debugging
            languages_str = ", ".join(sorted(available_languages))

            # Also fix available_themes access
            available_themes = getattr(editor, "available_themes", [])
            if callable(available_themes):
                available_themes = available_themes()
            themes_str = ", ".join(sorted(available_themes))

            # Print info to console for debugging
            print(f"Available languages: {languages_str}")
            print(f"Available themes: {themes_str}")

            # Check for specific languages we want to ensure are available
            desired_languages = {
                "python",
                "javascript",
                "typescript",
                "html",
                "css",
                "java",
                "c",
                "cpp",
                "rust",
                "go",
                "php",
                "ruby",
                "markdown",
                "yaml",
                "json",
                "xml",
                "sql",
                "bash",
            }

            missing = desired_languages - set(available_languages)
            if missing:
                missing_str = ", ".join(sorted(missing))
                print(f"Missing desired languages: {missing_str}")

                # Attempt to register custom lexers for missing languages
                self._register_custom_lexers(missing)
        except Exception as e:
            print(f"Error initializing syntax highlighting: {e}")

    def _register_custom_lexers(self, missing_languages):
        """Register custom lexers for any missing languages."""
        if not HAS_PYGMENTS:
            return

        # Get all available pygments lexers
        lexer_info = list(get_all_lexers())
        lexer_map = {name.lower(): aliases for name, aliases, _, _ in lexer_info}

        for lang in missing_languages:
            # Try to find a matching lexer
            for lexer_name, aliases in lexer_map.items():
                if lang in aliases or lang == lexer_name:
                    # Found a matching lexer, try to register it
                    try:
                        # Create a syntax test to force pygments to load the lexer
                        Syntax("test", lang)
                        print(f"Successfully registered lexer for {lang}")
                    except Exception as e:
                        print(f"Failed to register lexer for {lang}: {e}")
                    break

    def _log_available_features(self, editor: TextArea) -> None:
        """Log available features for debugging."""
        try:
            print(f"TextArea version: {importlib.import_module('textual').__version__}")
            # Fix property access for available_languages and available_themes
            try:
                langs = getattr(editor, "available_languages", [])
                if callable(langs):
                    langs = langs()
                print(f"Available languages: {', '.join(sorted(langs))}")

                themes = getattr(editor, "available_themes", [])
                if callable(themes):
                    themes = themes()
                print(f"Available themes: {', '.join(sorted(themes))}")
            except Exception as e:
                print(f"Error getting languages/themes: {e}")

            print(f"Current language: {editor.language}")
            print(f"Current theme: {editor.theme}")
            print(f"Line numbers: {editor.show_line_numbers}")
            print(f"Tab behavior: {editor.tab_behavior}")
        except Exception as e:
            print(f"Error logging features: {e}")

    def _setup_minimap(self) -> None:
        """Set up the code minimap."""
        if self._minimap_visible:
            minimap = self.query_one("#minimap", Static)
            editor = self.query_one("#editor", TextArea)

            # Create minimap content (simplified version of editor content)
            lines = editor.text.split("\n")
            minimap_lines = []

            for line in lines[:100]:  # Limit for performance
                # Simplify line for minimap
                minimap_line = line[:20].replace("\t", " ")
                minimap_lines.append(minimap_line)

            minimap.update("\n".join(minimap_lines))

    def _select_welcome_line(self, editor: TextArea) -> None:
        """Select the welcome line for initial focus."""
        try:
            # Set cursor position at start of first line
            editor.selection = Selection((0, 0), (0, 0))
        except Exception:
            pass

    def _update_file_path_display(self, path: str) -> None:
        """Update the file path display in the header."""
        file_path_label = self.query_one("#file-path", Label)
        file_path_label.update(f"📄 {path}")

    def _update_status_info(self, row: int, column: int, language: str) -> None:
        """Update the status information in the footer."""
        position_label = self.query_one("#position-display", Label)
        language_label = self.query_one("#language-display", Label)

        position_label.update(f"Ln {row + 1}, Col {column + 1}")
        language_label.update(language.capitalize())

    def _detect_language(self, path: str) -> str:
        """Detect the language based on file extension."""
        ext = Path(path).suffix.lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".md": "markdown",
            ".txt": "text",
            ".sh": "bash",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "cpp",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".php": "php",
            ".sql": "sql",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".xml": "xml",
            ".toml": "toml",
        }
        return language_map.get(ext, "text")

    @on(TextArea.Changed)
    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Handle text area content changes."""
        self.is_modified = True

        if self.current_path:
            self.post_message(self.FileChanged(self.current_path, event.text_area.text))

    @on(TextArea.SelectionChanged)
    def on_selection_changed(self, event: TextArea.SelectionChanged) -> None:
        """Handle selection changes in the text area."""
        selection = event.selection
        cursor_pos = selection.end
        self.current_line = cursor_pos[0]
        self.current_column = cursor_pos[1]

        # Update the status bar with cursor position
        self._update_status_info(
            self.current_line, self.current_column, self.current_language
        )

        # Post message about cursor movement
        self.post_message(self.CursorMoved(cursor_pos))

    def on_key(self, event: events.Key) -> None:
        """Handle keyboard events for the editor."""
        # Don't handle keys if we're not focused on the editor
        editor = self.query_one("#editor", TextArea)
        if self.screen.focused is not editor and not isinstance(
            self.screen.focused, Input
        ):
            editor.focus()
            return

        # Handle key combinations using Key name which contains the modifiers
        key_combo = []
        # Extract modifiers from the key name string
        key_name = getattr(event, "name", "")
        if "ctrl" in key_name:
            key_combo.append("ctrl")
        if "shift" in key_name:
            key_combo.append("shift")
        if "alt" in key_name:
            key_combo.append("alt")

        key_combo.append(event.key)
        key = "+".join(key_combo)

        # Map key combinations to actions
        key_actions = {
            "ctrl+s": self.action_save,
            "ctrl+g": self.action_goto_line,
            "ctrl+home": self.action_goto_file_start,
            "ctrl+end": self.action_goto_file_end,
            "ctrl+a": editor.select_all,
            "ctrl+d": self.action_duplicate_line,
            "ctrl+/": self.action_toggle_comment,
            "ctrl+shift+k": self.action_delete_line,
            "ctrl+f": self.action_show_search,
            "f3": self.action_find_next,
            "shift+f3": self.action_find_previous,
            "ctrl+h": self.action_show_replace,
            "ctrl+[": self.action_fold_current,
            "ctrl+]": self.action_unfold_current,
            "ctrl+space": self.action_show_completion,
            "alt+z": self.action_toggle_word_wrap,
            "alt+l": self.action_toggle_line_numbers,
            "f1": self.action_show_shortcuts,
            "ctrl+m": self.action_toggle_minimap,
            "ctrl+l": self.action_select_current_line,
            "ctrl+shift+l": self.action_select_all_occurrences,
            "ctrl+shift+c": self.action_check_code_quality,
            "ctrl+n": self.action_new_file,
            "ctrl+o": self.action_open_file,
            "ctrl+shift+s": self.action_save_as,
        }

        # Execute the action if it exists
        if key in key_actions:
            action = key_actions[key]
            action()
            event.prevent_default()
            event.stop()
            return

        # Handle bracket pairs - fix modifier check
        if (
            event.key in self.BRACKET_PAIRS
            and "ctrl" not in key_name
            and "alt" not in key_name
        ):
            self._handle_opening_bracket(event)

    def _handle_opening_bracket(self, event: events.Key) -> None:
        """Handle opening bracket by automatically inserting closing bracket."""
        editor = self.query_one("#editor", TextArea)
        opening_bracket = event.key
        closing_bracket = self.BRACKET_PAIRS[opening_bracket]

        # Get selection to check if text is selected
        selection = editor.selection
        has_selection = selection.start != selection.end

        if has_selection:
            # Wrap selection in brackets
            selected_text = editor.selected_text
            start = selection.start
            end = selection.end

            # Replace selection with bracketed text
            editor.delete(selection.start, selection.end)
            editor.insert(f"{opening_bracket}{selected_text}{closing_bracket}")

            # Set selection to include the new brackets
            new_end = (end[0], end[1] + 2) if start[0] == end[0] else end
            editor.selection = Selection(start, new_end)

            # Prevent default to avoid double bracket
            event.prevent_default()
        else:
            # Insert closing bracket and place cursor between brackets
            cursor_pos = editor.cursor_location
            editor.insert(f"{opening_bracket}{closing_bracket}")
            editor.selection = Selection(
                (cursor_pos[0], cursor_pos[1] + 1), (cursor_pos[0], cursor_pos[1] + 1)
            )

            # Prevent default to avoid double bracket
            event.prevent_default()

    def _insert_completion(self) -> None:
        """Insert the selected completion item."""
        if not self._completion_active or not self._completion_items:
            return

        editor = self.query_one("#editor", TextArea)
        selected_item = self._completion_items[self._completion_selected]

        # Calculate cursor position and text to replace
        cursor_pos = editor.cursor_location
        prefix_len = len(self._completion_prefix)
        col = cursor_pos[1]

        # Delete prefix and insert completion
        editor.delete((cursor_pos[0], col - prefix_len), cursor_pos)

        # Check if it's a snippet
        language = self.current_language
        if language in self.SNIPPETS and selected_item in self.SNIPPETS[language]:
            # Insert snippet content
            snippet_content = self.SNIPPETS[language][selected_item]
            editor.insert(snippet_content)

            # Move cursor to a sensible position in the snippet (first indented line)
            lines = snippet_content.split("\n")
            if len(lines) > 1:
                # Find first indented line
                for i, line in enumerate(lines[1:], 1):
                    if line.startswith((" ", "\t")):
                        # Calculate new position
                        indent_pos = len(line) - len(line.lstrip())
                        new_pos = (cursor_pos[0] + i, indent_pos)
                        editor.selection = Selection(new_pos, new_pos)
                        break
        else:
            # Just insert the completion text
            editor.insert(selected_item)

        # Reset completion state
        self._completion_active = False

    def _toggle_theme_selector(self) -> None:
        """Toggle the visibility of the theme selector."""
        theme_container = self.query_one("#theme-container", Container)
        if "visible" in theme_container.classes:
            theme_container.remove_class("visible")
        else:
            theme_container.add_class("visible")

    def _hide_theme_selector(self) -> None:
        """Hide the theme selector."""
        theme_container = self.query_one("#theme-container", Container)
        theme_container.remove_class("visible")

    def _set_theme(self, theme_name: str) -> None:
        """Set the editor theme."""
        editor = self.query_one("#editor", TextArea)

        # Convert from button ID to theme name
        if theme_name == "vscode-dark":
            theme = "vscode_dark"
        elif theme_name == "terminator-dark":
            theme = "terminator_dark"
        elif theme_name == "terminator-light":
            theme = "terminator_light"
        elif theme_name == "monokai":
            theme = "monokai"
        else:
            theme = "default"

        try:
            editor.theme = theme
            self.app.notify(f"Theme set to: {theme}", severity="information")
        except Exception as e:
            self.app.notify(f"Error setting theme: {str(e)}", severity="error")

        self._hide_theme_selector()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.input.id == "search-input":
            self._search()
        elif event.input.id == "replace-input":
            self._replace_current()

    def _search(self) -> None:
        """Perform a search in the editor content."""
        search_input = self.query_one("#search-input", Input)
        search_text = search_input.value

        if not search_text:
            return

        self._search_text = search_text
        editor = self.query_one("#editor", TextArea)

        # Get all matches
        text = editor.text
        matches = list(re.finditer(re.escape(search_text), text, re.IGNORECASE))
        self._search_results = []

        for match in matches:
            start_pos = match.start()
            end_pos = match.end()

            # Convert character positions to row, column
            start_row, start_col = self._pos_to_rowcol(text, start_pos)
            end_row, end_col = self._pos_to_rowcol(text, end_pos)

            self._search_results.append(((start_row, start_col), (end_row, end_col)))

        # Update search info
        search_info = self.query_one("#search-info", Label)
        result_count = len(self._search_results)

        if result_count > 0:
            search_info.update(f"{result_count} matches")
            self._current_search_index = 0
            self._highlight_current_match()
        else:
            search_info.update("No matches")
            self._current_search_index = -1

    def _pos_to_rowcol(self, text: str, pos: int) -> tuple[int, int]:
        """Convert a character position to row, column coordinates."""
        lines = text[:pos].split("\n")
        row = len(lines) - 1
        col = len(lines[-1])
        return row, col

    def _highlight_current_match(self) -> None:
        """Highlight the current search match."""
        if not self._search_results or self._current_search_index < 0:
            return

        editor = self.query_one("#editor", TextArea)
        match = self._search_results[self._current_search_index]

        # Set selection to the match
        editor.selection = Selection(match[0], match[1])

        # Make sure the match is visible by scrolling to it
        editor.scroll_to_selection()

        # Update search info with current match index
        search_info = self.query_one("#search-info", Label)
        search_info.update(
            f"Match {self._current_search_index + 1} of {len(self._search_results)}"
        )

    def _find_next(self) -> None:
        """Find the next match."""
        if not self._search_results:
            self._search()
            return

        if self._current_search_index < len(self._search_results) - 1:
            self._current_search_index += 1
        else:
            self._current_search_index = 0

        self._highlight_current_match()

    def _find_previous(self) -> None:
        """Find the previous match."""
        if not self._search_results:
            self._search()
            return

        if self._current_search_index > 0:
            self._current_search_index -= 1
        else:
            self._current_search_index = len(self._search_results) - 1

        self._highlight_current_match()

    def _replace_current(self) -> None:
        """Replace the current match with the replacement text."""
        if not self._search_results or self._current_search_index < 0:
            return

        editor = self.query_one("#editor", TextArea)
        replace_input = self.query_one("#replace-input", Input)
        replacement = replace_input.value

        match = self._search_results[self._current_search_index]

        # Delete the matched text and insert the replacement
        editor.delete(match[0], match[1])
        editor.insert(replacement)

        # Recalculate search results since the text has changed
        self._search()

    def _replace_all(self) -> None:
        """Replace all matches with the replacement text."""
        if not self._search_results:
            return

        editor = self.query_one("#editor", TextArea)
        replace_input = self.query_one("#replace-input", Input)
        replacement = replace_input.value

        # We need to replace from the end to ensure positions remain valid
        for match in reversed(self._search_results):
            # Set selection, delete, and insert for each match
            editor.selection = Selection(match[0], match[1])
            editor.delete(match[0], match[1])
            editor.insert(replacement)

        # Notify user
        self.app.notify(
            f"Replaced {len(self._search_results)} occurrences", severity="information"
        )

        # Clear search results
        self._search_results = []
        self._current_search_index = -1
        search_info = self.query_one("#search-info", Label)
        search_info.update("All replaced")

    def _hide_search(self) -> None:
        """Hide the search container."""
        search_container = self.query_one("#search-container", Container)
        search_container.remove_class("visible")

        # Focus back to editor
        editor = self.query_one("#editor", TextArea)
        editor.focus()

    def action_show_shortcuts(self) -> None:
        """Show keyboard shortcuts dialog."""
        self.app.notify(
            "Keyboard Shortcuts:\n"
            + "\n".join(
                [f"{key}: {desc}" for key, desc in self.KEYBOARD_SHORTCUTS[:10]]
            )
            + "\n(and more...)",
            severity="information",
            timeout=10,
        )

    def _hide_shortcuts(self) -> None:
        """Hide the keyboard shortcuts dialog."""
        shortcuts_dialog = self.query_one("#shortcuts-dialog", Container)
        shortcuts_dialog.remove_class("visible")

    def _new_file(self) -> None:
        """Create a new empty file."""
        # Check if current file needs saving
        if self.is_modified:
            self.app.notify(
                "Current file has unsaved changes. Save before creating a new file?",
                severity="warning",
                timeout=5,
            )

        # Clear the editor
        editor = self.query_one("#editor", TextArea)
        editor.text = ""
        self.current_path = ""
        self._last_saved_content = ""
        self.is_modified = False
        self._update_file_path_display("Untitled")

        # Reset language to a default
        self.current_language = "python"
        editor.language = "python"
        self._update_status_info(0, 0, "python")

        # Focus back to editor
        editor.focus()

    def _prompt_open_file(self) -> None:
        """Prompt the user to select a file to open."""
        # In a real implementation, we would show a file browser dialog
        # For now, we'll just notify the user
        self.app.notify(
            "File open dialog would appear here. This would let you browse and select a file.",
            severity="information",
            timeout=5,
        )

        # Simulate opening a file for demonstration
        sample_content = """# This is a simulated file open operation

def sample_function():
    '''Example function for demonstration.'''
    print("File open demonstration")
    return True

# The file browser would let you select a real file
# and populate the editor with its contents
"""

        self.open_file("example.py", sample_content)

    def _prompt_save_as(self) -> None:
        """Prompt the user to select a location to save the file."""
        # In a real implementation, we would show a file save dialog
        # For now, we'll just notify the user
        self.app.notify(
            "File save dialog would appear here. This would let you choose where to save the file.",
            severity="information",
            timeout=5,
        )

        # Simulate saving a file with a new name
        self.current_path = "new_file.py"
        self._update_file_path_display("new_file.py")
        self.save_file()

    # Add this utility method for getting relative file paths
    def _get_relative_path(self, path: str) -> str:
        """Convert an absolute path to a relative path if possible."""
        try:
            working_dir = os.getcwd()
            abs_path = os.path.abspath(path)
            if abs_path.startswith(working_dir):
                return os.path.relpath(abs_path, working_dir)
            return abs_path
        except Exception:
            return path

    def action_toggle_minimap(self) -> None:
        """Toggle the code minimap visibility."""
        self._minimap_visible = not self._minimap_visible
        minimap_container = self.query_one("#minimap-container", Container)

        if self._minimap_visible:
            minimap_container.add_class("visible")
            self._setup_minimap()
        else:
            minimap_container.remove_class("visible")

        self.app.notify(
            f"Minimap: {'visible' if self._minimap_visible else 'hidden'}",
            severity="information",
        )

    def action_fold_current(self) -> None:
        """Fold the current code region."""
        editor = self.query_one("#editor", TextArea)
        cursor_location = editor.cursor_location
        current_line_idx = cursor_location[0]

        # Find foldable region at current line
        language = self.current_language
        if language not in self.FOLD_MARKERS:
            return

        current_line = editor.document.get_line(current_line_idx)
        if not current_line:
            return

        # Check if line matches any fold pattern
        fold_type = None
        for pattern, fold_name in self.FOLD_MARKERS.get(language, []):
            if re.match(pattern, current_line):
                fold_type = fold_name
                break

        if not fold_type:
            return

        # Find the end of the fold region
        start_indent = len(current_line) - len(current_line.lstrip())
        end_line_idx = current_line_idx

        for i in range(current_line_idx + 1, len(editor.document.lines)):
            line = editor.document.get_line(i)
            if not line or line.isspace():
                continue

            line_indent = len(line) - len(line.lstrip())
            if line_indent <= start_indent:
                # Found the end of the block
                end_line_idx = i - 1
                break

            if i == len(editor.document.lines) - 1:
                # Last line of the document
                end_line_idx = i

        if end_line_idx > current_line_idx:
            # Add to folded regions
            fold_region = (current_line_idx, end_line_idx)
            self._folded_regions.add(fold_region)

            # Hide folded region lines
            folded_text = f"{current_line} [...] "

            # Replace the folded region with a placeholder
            lines = editor.text.split("\n")
            new_lines = (
                lines[:current_line_idx] + [folded_text] + lines[end_line_idx + 1 :]
            )
            editor.text = "\n".join(new_lines)

            # Set cursor at the fold line
            editor.selection = Selection((current_line_idx, 0), (current_line_idx, 0))

            self.app.notify(f"Folded {fold_type} region", severity="information")

    # def action_unfold_current(self) -> None:
    #     """Unfold the current folded region."""
    #     editor = self.query_one("#editor", TextArea)
    #     cursor_location = editor.cursor_location
    #     current_line_idx = cursor_location[0]

    #     # Check if cursor is on a folded region
    #     for start, end in self._folded_regions:
    #         if start == current_line_idx:
    #             # This is a folded region, unfold it
    #             self._folded_regions.remove((start, end))

    #             # For a real implementation, we would store the original text
    #             # and restore it. For this demo, we'll show a notification
    #             self.app.notify("Unfolded region", severity="information")
    #             return

    def action_select_current_line(self) -> None:
        """Select the current line."""
        editor = self.query_one("#editor", TextArea)
        cursor_location = editor.cursor_location
        current_line_idx = cursor_location[0]

        # Get the current line
        current_line = editor.document.get_line(current_line_idx)
        if current_line is None:
            return

        # Set selection to cover the entire line
        editor.selection = Selection(
            (current_line_idx, 0), (current_line_idx, len(current_line))
        )

    def action_select_all_occurrences(self) -> None:
        """Select all occurrences of the currently selected text."""
        editor = self.query_one("#editor", TextArea)
        selected_text = editor.selected_text

        if not selected_text:
            # No selection, select the word at cursor
            cursor_location = editor.cursor_location
            current_line_idx = cursor_location[0]
            current_line = editor.document.get_line(current_line_idx)

            if not current_line:
                return

            # Find word boundaries
            col = cursor_location[1]
            if col >= len(current_line) or not current_line[col].isalnum():
                if (
                    col > 0
                    and col - 1 < len(current_line)
                    and current_line[col - 1].isalnum()
                ):
                    col = col - 1
                else:
                    return

            # Find start of word
            start_col = col
            while start_col > 0 and current_line[start_col - 1].isalnum():
                start_col -= 1

            # Find end of word
            end_col = col
            while end_col < len(current_line) and current_line[end_col].isalnum():
                end_col += 1

            selected_text = current_line[start_col:end_col]

            if not selected_text:
                return

        # Find all occurrences
        self._search_text = selected_text
        text = editor.text
        matches = list(re.finditer(re.escape(selected_text), text))
        self._search_results = []

        for match in matches:
            start_pos = match.start()
            end_pos = match.end()

            # Convert character positions to row, column
            start_row, start_col = self._pos_to_rowcol(text, start_pos)
            end_row, end_col = self._pos_to_rowcol(text, end_pos)

            self._search_results.append(((start_row, start_col), (end_row, end_col)))

        if self._search_results:
            # Notify number of occurrences found
            self.app.notify(
                f"Found {len(self._search_results)} occurrences", severity="information"
            )

            # Highlight the first occurrence
            self._current_search_index = 0
            self._highlight_current_match()

    def action_check_code_quality(self) -> None:
        """Check code quality using linters."""
        self._run_lint_check()

    def _schedule_lint_check(self) -> None:
        """Schedule a lint check if enough time has passed."""
        current_time = time.time()
        if current_time - self._last_lint_time > self._lint_delay:
            self._run_lint_check()
            self._last_lint_time = current_time

    # def _run_lint_check(self) -> None:
    #     """Run linting check on the current code."""
    #     editor = self.query_one("#editor", TextArea)
    #     language = self.current_language

    #     # Clear previous lint markers
    #     self._lint_markers = {}

    #     if language == "python" and HAS_PYLINT:
    #         # Run pylint on the current Python code
    #         code = editor.text

    #         # Skip if code is too short
    #         if len(code.strip()) < 10:
    #             return

    #         try:
    #             # Create a temporary file with the code
    #             temp_file = Path("temp_lint_check.py")
    #             temp_file.write_text(code)

    #             # Use StringIO to capture pylint output
    #             from io import StringIO

    #             pylint_output = StringIO()
    #             reporter = TextReporter(pylint_output)

    #             # Run pylint
    #             try:
    #                 PylintRun(
    #                     ["--disable=all", "--enable=E", temp_file], reporter=reporter
    #                 )
    #                 lint_output = pylint_output.getvalue()

    #                 # Parse output to find errors
    #                 for line in lint_output.splitlines():
    #                     if ":" in line:
    #                         parts = line.split(":")
    #                         if len(parts) >= 3 and parts[1].strip().isdigit():
    #                             line_num = int(parts[1].strip()) - 1  # 0-based index
    #                             message = ":".join(parts[2:]).strip()
    #                             self._lint_markers[line_num] = {
    #                                 "type": "error",
    #                                 "message": message,
    #                             }
    #             except Exception as e:
    #                 print(f"Pylint error: {e}")

    #             # Clean up
    #             temp_file.unlink(missing_ok=True)

    #             # Update editor to show lint markers
    #             self._show_lint_markers()
    #         except Exception as e:
    #             print(f"Linting error: {e}")

    # def _show_lint_markers(self) -> None:
    #     """Show lint markers in the editor."""
    #     if not self._lint_markers:
    #         return

    #     # For a full implementation, we would add visual markers to the editor
    #     # For this demo, we'll just show a notification with the number of issues
    #     error_count = sum(
    #         1 for marker in self._lint_markers.values() if marker["type"] == "error"
    #     )
    #     warning_count = sum(
    #         1 for marker in self._lint_markers.values() if marker["type"] == "warning"
    #     )

    #     message = f"Found {error_count} errors"
    #     if warning_count > 0:
    #         message += f" and {warning_count} warnings"

    #     if error_count > 0 or warning_count > 0:
    #         self.app.notify(message, severity="error" if error_count > 0 else "warning")

    def action_save(self) -> None:
        """Save the current file."""
        if not self.current_path:
            self.app.notify("No file to save. Use 'Save As' first", severity="warning")
            return

        try:
            editor = self.query_one("#editor", TextArea)
            content = editor.text

            path = Path(self.current_path)
            path.write_text(content, encoding="utf-8")

            # Update state
            self._last_saved_content = content
            self.is_modified = False

            # Notify user
            self.app.notify(f"Saved {path.name}", severity="information")
        except Exception as e:
            self.app.notify(f"Error saving file: {str(e)}", severity="error")

    def action_show_search(self) -> None:
        """Show search bar."""
        search_container = self.query_one("#search-container", Container)
        search_container.add_class("visible")

        # Focus the search input
        search_input = self.query_one("#search-input", Input)
        search_input.focus()

        # Pre-fill with selected text if any
        editor = self.query_one("#editor", TextArea)
        if editor.selected_text:
            search_input.value = editor.selected_text

    def action_show_replace(self) -> None:
        """Show search and replace bar."""
        self.action_show_search()

        # Focus the replace input
        replace_input = self.query_one("#replace-input", Input)
        replace_input.focus()

    def action_goto_line(self) -> None:
        """Action to go to a specific line."""
        # This would typically open a dialog to ask for line number
        self.app.notify("Go to line functionality coming soon", severity="information")

    def action_duplicate_line(self) -> None:
        """Action to duplicate the current line."""
        editor = self.query_one("#editor", TextArea)
        # Get current selection/cursor position
        selection = editor.selection
        line_idx = selection.end[0]

        # Get the line content
        lines = editor.text.split("\n")
        if line_idx < len(lines):
            line_content = lines[line_idx]

            # Insert a duplicate line
            new_lines = lines[: line_idx + 1] + [line_content] + lines[line_idx + 1 :]
            editor.text = "\n".join(new_lines)

            # Place cursor at start of new line
            editor.selection = Selection((line_idx + 1, 0), (line_idx + 1, 0))

    def action_toggle_comment(self) -> None:
        """Action to toggle comment on current line or selection."""
        editor = self.query_one("#editor", TextArea)

        # Get current selection
        selection = editor.selection
        start_line = selection.start[0]
        end_line = selection.end[0]

        # Get text lines
        lines = editor.text.split("\n")

        # Determine comment character based on language
        comment_char = (
            "#" if self.current_language in ["python", "bash", "yaml"] else "//"
        )

        # Check if all lines are already commented
        all_commented = all(
            line.strip().startswith(comment_char)
            for line in lines[start_line : end_line + 1]
            if line.strip()
        )

        # Toggle comments
        new_lines = lines.copy()
        for i in range(start_line, min(end_line + 1, len(lines))):
            if not lines[i].strip():  # Skip empty lines
                continue

            if all_commented:
                # Remove comment
                if lines[i].strip().startswith(comment_char):
                    # Find the position of the comment character
                    pos = lines[i].find(comment_char)
                    if pos >= 0:
                        # Remove comment character and one space if present
                        if (
                            len(lines[i]) > pos + len(comment_char)
                            and lines[i][pos + len(comment_char)] == " "
                        ):
                            new_lines[i] = (
                                lines[i][:pos] + lines[i][pos + len(comment_char) + 1 :]
                            )
                        else:
                            new_lines[i] = (
                                lines[i][:pos] + lines[i][pos + len(comment_char) :]
                            )
            else:
                # Add comment
                new_lines[i] = comment_char + " " + lines[i]

        # Update text
        editor.text = "\n".join(new_lines)

        # Maintain selection
        editor.selection = selection

    def action_goto_file_start(self) -> None:
        """Action to go to the start of the file."""
        editor = self.query_one("#editor", TextArea)
        editor.selection = Selection((0, 0), (0, 0))

    def action_goto_file_end(self) -> None:
        """Action to go to the end of the file."""
        editor = self.query_one("#editor", TextArea)
        lines = editor.text.split("\n")
        last_line_idx = len(lines) - 1
        last_line_len = len(lines[last_line_idx])
        editor.selection = Selection(
            (last_line_idx, last_line_len), (last_line_idx, last_line_len)
        )

    def action_toggle_word_wrap(self) -> None:
        """Toggle word wrap in the editor."""
        editor = self.query_one("#editor", TextArea)
        editor.soft_wrap = not editor.soft_wrap
        self.app.notify(
            f"Soft wrap: {'enabled' if editor.soft_wrap else 'disabled'}",
            severity="information",
        )

    def action_toggle_line_numbers(self) -> None:
        """Toggle line numbers in the editor."""
        editor = self.query_one("#editor", TextArea)
        editor.show_line_numbers = not editor.show_line_numbers
        self.app.notify(
            f"Line numbers: {'enabled' if editor.show_line_numbers else 'disabled'}",
            severity="information",
        )

    def action_show_completion(self) -> None:
        """Show code completion suggestions."""
        editor = self.query_one("#editor", TextArea)
        cursor_location = editor.cursor_location

        # Get current word
        current_line = editor.document.get_line(cursor_location[0])
        if not current_line:
            return

        # Find word prefix at cursor
        col = cursor_location[1]
        prefix_start = col

        # Find the start of the current word
        while (
            prefix_start > 0
            and current_line[prefix_start - 1].isalnum()
            or current_line[prefix_start - 1] == "_"
        ):
            prefix_start -= 1

        current_prefix = current_line[prefix_start:col]
        if not current_prefix:
            return

        # Get language-specific completions
        self._show_completions(editor, current_prefix, cursor_location)

    def action_delete_line(self) -> None:
        """Delete the current line."""
        editor = self.query_one("#editor", TextArea)
        cursor_location = editor.cursor_location
        current_line_idx = cursor_location[0]

        # Get all lines
        lines = editor.text.split("\n")

        # Remove the current line
        if 0 <= current_line_idx < len(lines):
            new_lines = lines[:current_line_idx] + lines[current_line_idx + 1 :]
            editor.text = "\n".join(new_lines)

            # Set cursor to the start of the next line or the end of the file
            if current_line_idx < len(new_lines):
                editor.selection = Selection(
                    (current_line_idx, 0), (current_line_idx, 0)
                )
            else:
                last_line = len(new_lines) - 1
                last_col = len(new_lines[last_line]) if last_line >= 0 else 0
                editor.selection = Selection(
                    (last_line, last_col), (last_line, last_col)
                )

    def open_file(self, path: str, content: str) -> None:
        """Open a file in the editor."""
        self.current_path = path
        file_name = Path(path).name

        try:
            editor = self.query_one("#editor", TextArea)

            # Detect language for syntax highlighting
            self.current_language = self._detect_language(path)
            editor.language = self.current_language

            # Update content
            editor.text = content
            self._last_saved_content = content
            self.is_modified = False

            # Update UI elements
            self._update_file_path_display(file_name)
            self._update_status_info(0, 0, self.current_language)

            # Focus editor
            editor.focus()
        except Exception as e:
            self.app.notify(f"Error opening file: {str(e)}", severity="error")

    def action_new_file(self) -> None:
        """Create a new file."""
        self._new_file()

    def action_open_file(self) -> None:
        """Open a file dialog."""
        self._prompt_open_file()

    def action_save_as(self) -> None:
        """Save as dialog."""
        self._prompt_save_as()

    def action_find_next(self) -> None:
        """Find the next search match."""
        self._find_next()

    def action_find_previous(self) -> None:
        """Find the previous search match."""
        self._find_previous()

    # def action_fold_current(self) -> None:
    #     """Fold the current code region."""
    #     editor = self.query_one("#editor", TextArea)
    #     cursor_location = editor.cursor_location
    #     current_line_idx = cursor_location[0]

    #     # Find foldable region at current line
    #     language = self.current_language
    #     if language not in self.FOLD_MARKERS:
    #         return

    #     current_line = editor.document.get_line(current_line_idx)
    #     if not current_line:
    #         return

    #     # Check if line matches any fold pattern
    #     fold_type = None
    #     for pattern, fold_name in self.FOLD_MARKERS.get(language, []):
    #         if re.match(pattern, current_line):
    #             fold_type = fold_name
    #             break

    #     if not fold_type:
    #         return

    #     # Find the end of the fold region
    #     start_indent = len(current_line) - len(current_line.lstrip())
    #     end_line_idx = current_line_idx

    #     for i in range(current_line_idx + 1, len(editor.document.lines)):
    #         line = editor.document.get_line(i)
    #         if not line or line.isspace():
    #             continue

    #         line_indent = len(line) - len(line.lstrip())
    #         if line_indent <= start_indent:
    #             # Found the end of the block
    #             end_line_idx = i - 1
    #             break

    #         if i == len(editor.document.lines) - 1:
    #             # Last line of the document
    #             end_line_idx = i

    #     if end_line_idx > current_line_idx:
    #         # Add to folded regions
    #         fold_region = (current_line_idx, end_line_idx)
    #         self._folded_regions.add(fold_region)

    #         # Hide folded region lines
    #         folded_text = f"{current_line} [...] "

    #         # Replace the folded region with a placeholder
    #         lines = editor.text.split("\n")
    #         new_lines = (
    #             lines[:current_line_idx] + [folded_text] + lines[end_line_idx + 1 :]
    #         )
    #         editor.text = "\n".join(new_lines)

    #         # Set cursor at the fold line
    #         editor.selection = Selection((current_line_idx, 0), (current_line_idx, 0))

    #         self.app.notify(f"Folded {fold_type} region", severity="information")

    # def action_unfold_current(self) -> None:
    #     """Unfold the current folded region."""
    #     editor = self.query_one("#editor", TextArea)
    #     cursor_location = editor.cursor_location
    #     current_line_idx = cursor_location[0]

    #     # Check if cursor is on a folded region
    #     for start, end in self._folded_regions:
    #         if start == current_line_idx:
    #             # This is a folded region, unfold it
    #             self._folded_regions.remove((start, end))

    #             # For a real implementation, we would store the original text
    #             # and restore it. For this demo, we'll show a notification
    #             self.app.notify("Unfolded region", severity="information")
    #             return
