"""
Enhanced Agent Panel with streaming capabilities for TerminatorIDE.
This panel displays real-time responses from the AI assistant.
"""

import asyncio
from pathlib import Path  # Add this import for Path handling
from typing import Tuple

from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Input, Label, LoadingIndicator, Static

from terminatoride.agent.context import (  # Ensure FileContext is imported
    AgentContext,
    FileContext,
)
from terminatoride.agent_streaming import get_streaming_agent
from terminatoride.utils.logging_utils import log_exception, setup_logger

# Initialize logger
logger = setup_logger("terminatoride.agent_panel")

# Command handler registry
CODE_COMMANDS = {
    "/improve": "Improve the entire file with general best practices",
    "/refactor": "Restructure the code without changing its behavior",
    "/optimize": "Optimize the code for better performance",
    "/debug": "Find and fix bugs in the code",
    "/clean": "Clean up the code (formatting, naming conventions, etc.)",
    "/explain": "Explain what the current code does (no modifications)",
    "/security": "Improve security aspects of the code",
    "/open": "Find and open a file in the project",
    "/help": "Show available code commands",
}


class StreamingAgentPanel(Container):
    """Enhanced Agent Panel with streaming capabilities."""

    class AgentResponse(Message):
        """Message containing the agent's response."""

        def __init__(self, response: str):
            self.response = response
            super().__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info("Initializing StreamingAgentPanel")
        self.streaming_agent = get_streaming_agent()
        logger.debug(f"Agent attributes: {dir(self.streaming_agent)}")
        if hasattr(self.streaming_agent, "specialized_agents"):
            logger.info(
                f"Agent has specialized_agents: {self.streaming_agent.specialized_agents}"
            )
        else:
            logger.warning("Agent does not have specialized_agents attribute")

        self.context = AgentContext()
        self.current_response_widget = None
        self._last_file_search_results = []

    def compose(self) -> ComposeResult:
        """Compose the streaming agent panel widget."""
        yield Label("AI Assistant", id="agent-title")

        # Conversation container should take up all available space
        with ScrollableContainer(id="conversation-container"):
            yield VerticalScroll(id="conversation")

        # Input container with horizontal layout - DO NOT add the horizontal-input class here
        # Instead, rely solely on the CSS for styling
        with Container(id="input-container"):
            yield Input(placeholder="Ask the AI assistant...", id="agent-input")
            yield Button("Send", id="send-button", variant="primary")

    def on_mount(self) -> None:
        print("Available attributes on streaming_agent:", dir(self.streaming_agent))
        """Called when the widget is mounted."""
        # Add welcome message
        conversation = self.query_one("#conversation")
        conversation.mount(
            Static(
                "👋 Hello! I'm your AI assistant with streaming capabilities. How can I help you today?",
                classes="agent-message",
            )
        )

        # Show available commands
        self.show_available_commands()

        # Connect event handlers
        input_field = self.query_one("#agent-input")
        input_field.focus()

        send_button = self.query_one("#send-button")
        send_button.on_click = self._on_send_click

    async def _on_send_click(self) -> None:
        """Handle send button click."""
        input_field = self.query_one("#agent-input")
        user_message = input_field.value

        if not user_message.strip():
            return

        # Check if this is a response to a file search (just a number)
        if (
            hasattr(self, "_last_file_search_results")
            and self._last_file_search_results
            and user_message.strip().isdigit()
        ):
            file_num = int(user_message.strip())
            if 1 <= file_num <= len(self._last_file_search_results):
                # Found a valid file number
                file_path = self._last_file_search_results[file_num - 1]

                # Add user message to conversation
                conversation = self.query_one("#conversation")
                conversation.mount(
                    Static(f"You: {user_message}", classes="user-message")
                )

                # Clear input and keep focus
                input_field.value = ""
                input_field.focus()

                # Show opening message
                opening_message = Static(
                    f"Opening file: {file_path}",
                    classes="agent-message",
                )
                conversation.mount(opening_message)

                # Open the file
                success = await self.focus_file(str(file_path))

                if not success:
                    opening_message.update(f"Failed to open file: {file_path}")

                # Auto-scroll to bottom
                await self._scroll_to_bottom()
                return

        # Check if message is a code command
        is_command, command, args = self.parse_command(user_message)

        if is_command:
            # Add user message to conversation
            conversation = self.query_one("#conversation")
            conversation.mount(Static(f"You: {user_message}", classes="user-message"))

            # Clear input and keep focus
            input_field.value = ""
            input_field.focus()

            # Get current file context if available
            self._update_context()

            # Process the command
            await self.handle_code_command(command, args)

            # Auto-scroll to bottom
            await self._scroll_to_bottom()
            return

        # Regular message flow continues here

        # Add user message to conversation
        conversation = self.query_one("#conversation")
        conversation.mount(Static(f"You: {user_message}", classes="user-message"))

        # Clear input and keep focus
        input_field.value = ""
        input_field.focus()

        # Get current file context if available
        self._update_context()

        # Always use streaming (removed toggle check)
        streaming_enabled = True

        # Processing indicator
        if streaming_enabled:
            # For streaming, create a response container that will be updated
            self.current_response_widget = Static(
                "Assistant: ", classes="agent-message", markup=False
            )
            conversation.mount(self.current_response_widget)
        else:
            # This code path is no longer used but kept for potential future use
            loading = LoadingIndicator(classes="agent-thinking")
            conversation.mount(loading)
            self.current_response_widget = None

        # Process in background to keep UI responsive
        if streaming_enabled:
            # Ensure we're properly running the coroutine
            async def run_streaming():
                try:
                    await self._process_streaming_response(user_message)
                except Exception as e:
                    print(f"Error in streaming worker: {e}")
                    conversation = self.query_one("#conversation")
                    conversation.mount(
                        Static(f"Error: {str(e)}", classes="agent-error")
                    )
                    await self._scroll_to_bottom()

            self.app.run_worker(run_streaming())
        else:
            # Ensure we're properly running the coroutine
            async def run_standard():
                try:
                    await self._process_standard_response(user_message, loading)
                except Exception as e:
                    print(f"Error in standard worker: {e}")
                    conversation = self.query_one("#conversation")
                    conversation.mount(
                        Static(f"Error: {str(e)}", classes="agent-error")
                    )
                    await self._scroll_to_bottom()

            self.app.run_worker(run_standard())

        # Auto-scroll to bottom
        await self._scroll_to_bottom()

    async def _process_streaming_response(self, user_message: str) -> None:
        """Process the streaming response from agent."""
        logger.info(f"Starting streaming response for message: {user_message[:50]}...")

        try:
            # Create wrapper callbacks with logging
            async def debug_text_delta(delta: str):
                logger.debug(f"Text delta received: '{delta[:30]}...'")
                # Just log to console, not to UI
                print(f"DEBUG: Received delta: '{delta[:50]}...'")

                # Process delta as normal
                if delta is None:
                    delta = ""

                if not isinstance(delta, str):
                    try:
                        delta = str(delta)
                    except Exception as err:
                        print(f"ERROR converting delta to string: {err}")
                        delta = "[Non-text content]"

                if not delta:
                    return

                if self.current_response_widget:
                    current_text = self.current_response_widget.renderable
                    new_text = current_text + delta
                    self.current_response_widget.update(new_text)

            async def debug_tool_call(tool_info: dict):
                logger.info(f"Tool call: {tool_info}")
                await self._handle_tool_call(tool_info)

            async def debug_tool_result(result_info: dict):
                logger.info(f"Tool result: {result_info}")
                await self._handle_tool_result(result_info)

            async def debug_handoff(handoff_info: dict):
                logger.info(f"Handoff event: {handoff_info}")
                try:
                    await self._handle_handoff(handoff_info)
                except Exception:
                    log_exception(logger, "Error in handoff handler")
                    raise

            # Try using the streaming approach first
            try:
                logger.info("Starting streaming response generation")
                result = await self.streaming_agent.generate_streaming_response(
                    user_message,
                    self.context,
                    on_text_delta=debug_text_delta,
                    on_tool_call=debug_tool_call,
                    on_tool_result=debug_tool_result,
                    on_handoff=debug_handoff,
                )
                print(
                    f"Streaming completed with result: {result[:50]}..."
                    if result
                    else "No result"
                )
            except Exception as stream_err:
                # If streaming fails, try the direct approach
                print(
                    f"Streaming failed: {stream_err}, falling back to direct approach"
                )

                try:
                    # Use the direct OpenAI API as a last resort fallback
                    import os

                    from openai import OpenAI

                    # Initialize client with API key
                    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
                    if not openai_api_key:
                        # Try to get from config directly
                        print("No API key in environment, checking config")
                        try:
                            from terminatoride.config import get_config

                            config = get_config()
                            openai_api_key = config.openai.api_key
                        except Exception as config_err:
                            print(f"Config error: {config_err}")

                    if openai_api_key:
                        print("Using direct OpenAI API call")
                        client = OpenAI(api_key=openai_api_key)

                        # Make direct completion request
                        completion = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {
                                    "role": "system",
                                    "content": "You are a helpful AI assistant for TerminatorIDE.",
                                },
                                {"role": "user", "content": user_message},
                            ],
                            stream=True,
                        )

                        # Stream the response directly
                        total_content = ""
                        for chunk in completion:
                            if chunk.choices and chunk.choices[0].delta.content:
                                content = chunk.choices[0].delta.content
                                total_content += content
                                await debug_text_delta(content)

                        result = total_content
                    else:
                        raise Exception("No OpenAI API key available for fallback")
                except Exception as direct_err:
                    print(f"Direct API failed: {direct_err}")
                    # If all else fails, use a static response
                    result = "I'm sorry, I encountered an error while processing your request. Please try again."
                    if self.current_response_widget:
                        self.current_response_widget.update(f"Assistant: {result}")
                    else:
                        conversation = self.query_one("#conversation")
                        self.current_response_widget = Static(
                            f"Assistant: {result}", classes="agent-message"
                        )
                        conversation.mount(self.current_response_widget)

            # Create a separate log message for completion
            print(f"Streaming completed successfully with result: {result}")

            # If we have a current response widget that's empty, add the result text
            if (
                self.current_response_widget
                and self.current_response_widget.renderable == "Assistant: "
            ):
                # DISABLE MARKUP HERE
                self.current_response_widget.update(f"Assistant: {result}")

            # Post event for potential use by other components
            if self.current_response_widget:
                self.post_message(
                    self.AgentResponse(self.current_response_widget.renderable)
                )

            # One final scroll to bottom after all streaming
            await self._scroll_to_bottom()

        except Exception as e:
            log_exception(logger, "Error in streaming response")
            # Handle errors with more detailed diagnostic info
            import traceback

            conversation = self.query_one("#conversation")
            error_text = f"Error: {str(e)}\n\n{traceback.format_exc()}"
            conversation.mount(Static(error_text, classes="agent-error"))
            await self._scroll_to_bottom()

    async def _process_standard_response(
        self, user_message: str, loading_indicator: LoadingIndicator
    ) -> None:
        """Process the agent response without streaming."""
        try:
            # Add debug message
            conversation = self.query_one("#conversation")
            debug_widget = Static(
                "Processing request (non-streaming mode)...", classes="debug-message"
            )
            conversation.mount(debug_widget)

            # Try using streaming agent directly without callbacks
            print("Starting non-streaming request using streaming agent")
            try:
                # Use the same generate_streaming_response but without callbacks
                response = await self.streaming_agent.generate_streaming_response(
                    user_message, self.context
                )
                print(
                    f"Received response via streaming agent: {response[:50] if response else 'No response'}"
                )
            except Exception as direct_err:
                print(
                    f"Direct streaming request failed: {direct_err}, falling back to base agent"
                )
                # Fall back to traditional generate_response
                response = await self.streaming_agent.base_agent.generate_response(
                    user_message, self.context
                )
                print(
                    f"Received fallback response: {response[:50] if response else 'No response'}"
                )

            # Remove loading indicator
            if loading_indicator in conversation.children:
                loading_indicator.remove()

            # Add response to conversation
            if response:
                conversation.mount(
                    Static(f"Assistant: {response}", classes="agent-message")
                )
            else:
                conversation.mount(
                    Static(
                        "Assistant: Sorry, I couldn't generate a response.",
                        classes="agent-message",
                    )
                )

            # Remove debug widget
            if debug_widget in conversation.children:
                debug_widget.remove()

            # Auto-scroll to bottom
            await self._scroll_to_bottom()

            # Post message for potential use by other components
            self.post_message(self.AgentResponse(response or ""))

        except Exception as e:
            import traceback

            error_text = (
                f"Error in standard response: {str(e)}\n\n{traceback.format_exc()}"
            )
            print(error_text)

            # Handle errors
            if loading_indicator in conversation.children:
                loading_indicator.remove()

            conversation = self.query_one("#conversation")
            conversation.mount(Static(f"Error: {str(e)}", classes="agent-error"))
            await self._scroll_to_bottom()

    async def _handle_text_delta(self, delta: str) -> None:
        """Handle text delta events from streaming."""
        try:
            # Debug log to see what we're getting
            print(f"Delta type: {type(delta)}, content: {str(delta)[:30]}...")

            if delta is None:  # Skip None deltas
                return

            # Convert to string if needed
            if not isinstance(delta, str):
                try:
                    delta = str(delta)
                except Exception as conv_err:
                    print(f"Error converting delta to string: {conv_err}")
                    delta = "[Non-text content]"

            if not delta:  # Skip empty deltas after conversion
                return

            if self.current_response_widget:
                # Get the current text
                current_text = self.current_response_widget.renderable

                # Add the new text
                new_text = current_text + delta

                # Update the widget with the new text - DISABLE MARKUP HERE
                self.current_response_widget.update(new_text)

                # Auto-scroll
                await self._scroll_to_bottom()
        except Exception as e:
            print(f"Error in _handle_text_delta: {e}")
            # Create a new widget if there was a problem
            try:
                conversation = self.query_one("#conversation")
                # DISABLE MARKUP HERE TOO
                self.current_response_widget = Static(
                    f"Assistant: {delta}", classes="agent-message", markup=False
                )
                conversation.mount(self.current_response_widget)
                await self._scroll_to_bottom()
            except Exception as mount_err:
                print(f"Failed to create recovery widget: {mount_err}")

    async def _handle_tool_call(self, tool_info: dict) -> None:
        """Handle tool call events."""
        conversation = self.query_one("#conversation")
        conversation.mount(
            Static(
                f"🛠️ Using tool: {tool_info['name']}",
                classes="agent-tool-call",
            )
        )
        # Scroll to bottom
        await self._scroll_to_bottom()

    async def _handle_tool_result(self, result_info: dict) -> None:
        """Handle tool result events."""
        conversation = self.query_one("#conversation")
        conversation.mount(
            Static(
                f"📊 Tool result: {result_info['output'][:50]}...",
                classes="agent-tool-result",
            )
        )
        # Scroll to bottom
        await self._scroll_to_bottom()

    async def _handle_handoff(self, handoff_info: dict) -> None:
        """Handle handoff events."""
        logger.info(f"Handling handoff: {handoff_info}")
        conversation = self.query_one("#conversation")

        # Get the agent information directly from the handoff_info
        from_agent = handoff_info.get("from_agent", "unknown")
        to_agent = handoff_info.get("to_agent", "unknown")

        # Just use the agent names directly from the handoff_info
        conversation.mount(
            Static(
                f"🔄 Handing off from {from_agent} to {to_agent}",
                classes="agent-handoff",
            )
        )
        # Scroll to bottom
        await self._scroll_to_bottom()

    async def _scroll_to_bottom(self) -> None:
        """Scroll the conversation to the bottom."""
        try:
            # First try to get the ScrollableContainer
            container = self.query_one("#conversation-container")
            await container.scroll_end(animate=False)

            # Also scroll the conversation itself as a backup
            conversation = self.query_one("#conversation")
            if hasattr(conversation, "scroll_end"):
                await conversation.scroll_end(animate=False)

            # Force a refresh to ensure scrolling takes effect
            self.refresh()
        except Exception as e:
            print(f"Error scrolling to bottom: {e}")

    def _update_context(self) -> None:
        """Update the agent context with current IDE state."""
        try:
            # Get the editor panel
            editor_panel = self.app.query_one("#editor-panel")

            # Get the current file from the editor panel
            if hasattr(editor_panel, "current_file") and editor_panel.current_file:
                current_file = editor_panel.current_file

                # Update context with current file info
                self.context.update_current_file(
                    path=current_file.path,
                    content=current_file.content,
                    language=current_file.language,
                    cursor_position=current_file.cursor_position,
                )

                # Also update project context if available
                if hasattr(self.context, "project") and hasattr(
                    editor_panel, "current_path"
                ):
                    # Set project root to the parent directory of the current file
                    project_root = str(Path(current_file.path).parent)
                    self.context.project.root_path = project_root

                print(f"Updated agent context with file: {current_file.path}")
            else:
                print("No current file available for agent context")
        except Exception as e:
            print(f"Error updating agent context: {e}")

    async def focus_file(self, file_path: str) -> bool:
        """
        Focus (open) a specific file in the editor panel.
        This can be called by the agent to open files of interest.

        Args:
            file_path: Path to the file to open

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the editor panel
            editor_panel = self.app.query_one("#editor-panel")

            # Check if the file exists
            path = Path(file_path)
            if not path.exists() or not path.is_file():
                self.app.notify(f"File not found: {file_path}", severity="error")
                return False

            # Read the file content
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Open the file in the editor
            editor_panel.open_file(str(path), content)

            # Update the current_file property
            editor_panel.current_file = FileContext(
                path=str(path),
                content=content,
                language=editor_panel._detect_language(str(path)),
                cursor_position=0,
            )

            # Update agent context with this file
            self._update_context()

            # Notify success
            self.app.notify(f"Opened file: {path.name}", severity="information")
            return True
        except Exception as e:
            self.app.notify(f"Error opening file: {str(e)}", severity="error")
            return False

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in the input field."""
        if event.input.id == "agent-input":
            asyncio.create_task(self._on_send_click())

    def show_available_commands(self) -> None:
        """Show available code commands at startup."""
        # Get the conversation container
        conversation = self.query_one("#conversation")

        # Create a message with available commands
        commands_message = "💡 **Available Code Commands:**\n\n"
        for cmd, desc in CODE_COMMANDS.items():
            commands_message += f"* `{cmd}` - {desc}\n"

        # Add a note about normal queries
        commands_message += (
            "\nYou can also ask me normal questions about your code or anything else!"
        )

        # Add the message to the conversation
        conversation.mount(Static(commands_message, classes="agent-message"))

    def parse_command(self, message: str) -> Tuple[bool, str, str]:
        """
        Parse a message for code commands.

        Args:
            message: The user message

        Returns:
            Tuple of (is_command, command, arguments)
        """
        # Check if the message starts with a slash command
        for command in CODE_COMMANDS:
            if message.startswith(command):
                # Extract arguments after the command
                args = message[len(command) :].strip()
                return True, command, args

        return False, "", ""

    async def handle_code_command(self, command: str, args: str):
        """
        Handle a code command.

        Args:
            command: The command (e.g., /improve)
            args: Additional arguments after the command
        """
        # Get the current file content from the editor
        if (
            not hasattr(self.app, "query_one")
            or not self.context
            or not self.context.current_file
        ):
            self.app.notify("No file is currently open to improve", severity="warning")
            return False

        original_code = self.context.current_file.content
        language = self.context.current_file.language or "python"

        # Show thinking message
        conversation = self.query_one("#conversation")
        thinking = Static(f"Processing {command} command...", classes="agent-thinking")
        conversation.mount(thinking)

        # Add a code improvement response to conversation
        command_message = Static(
            f"🔍 Processing {command} command on current file...",
            classes="agent-message",
        )
        conversation.mount(command_message)

        # Generate improved code
        try:
            # Create a prompt based on the command
            if command == "/help":
                # Show available commands
                help_text = "💡 **Available Code Commands:**\n\n"
                for cmd, desc in CODE_COMMANDS.items():
                    help_text += f"* `{cmd}` - {desc}\n"

                thinking.remove()
                command_message.update(help_text)
                return True

            elif command == "/explain":
                # Use the streaming agent to explain code
                explanation = await self.streaming_agent.generate_response(
                    f"Explain the following {language} code in detail:\n\n```{language}\n{original_code}\n```",
                    self.context,
                )

                thinking.remove()
                command_message.update(f"📝 **Code Explanation:**\n\n{explanation}")
                return True

            elif command == "/open":
                # Search for files
                thinking.remove()
                command_message.update(
                    f"🔍 Searching for files matching '{args}'...\n"
                    "Please enter the number of the file you want to open."
                )

                # TODO: Implement file search and listing
                return True

            else:
                # For improvement commands
                prompt = ""
                if command == "/improve":
                    prompt = f"Improve this {language} code with best practices:\n\n```{language}\n{original_code}\n```\nProvide both the improved code and an explanation of the changes."
                elif command == "/refactor":
                    prompt = f"Refactor this {language} code for better structure:\n\n```{language}\n{original_code}\n```\nProvide both the refactored code and an explanation of the changes."
                elif command == "/optimize":
                    prompt = f"Optimize this {language} code for better performance:\n\n```{language}\n{original_code}\n```\nProvide both the optimized code and an explanation of the improvements."
                elif command == "/debug":
                    prompt = f"Find and fix any bugs in this {language} code:\n\n```{language}\n{original_code}\n```\nProvide both the fixed code and an explanation of the bugs."
                elif command == "/clean":
                    prompt = f"Clean up this {language} code (formatting, naming, etc.):\n\n```{language}\n{original_code}\n```\nProvide both the cleaned code and an explanation of the changes."
                elif command == "/security":
                    prompt = f"Improve security aspects of this {language} code:\n\n```{language}\n{original_code}\n```\nProvide both the improved code and an explanation of the security issues fixed."

                # Get response from the agent
                response = await self.streaming_agent.generate_response(
                    prompt, self.context
                )

                # Try to extract code block from response
                import re

                code_pattern = r"```(?:\w+)?\n([\s\S]*?)```"
                code_matches = re.findall(code_pattern, response)

                if code_matches:
                    improved_code = code_matches[0].strip()

                    # Create a diff using DiffManager
                    from terminatoride.utils.diff_manager import DiffManager

                    diff_text = DiffManager.generate_diff(original_code, improved_code)

                    # Extract explanation (text before or after code block)
                    explanation = response.replace(
                        f"```{language}\n{improved_code}\n```", ""
                    )
                    explanation = explanation.replace(f"```\n{improved_code}\n```", "")

                    # Remove the thinking indicator and update message
                    thinking.remove()
                    command_message.update("Code improvements ready for review")

                    # Show the diff dialog
                    await self.show_diff_dialog(
                        diff_text, original_code, improved_code, explanation
                    )
                    return True
                else:
                    thinking.remove()
                    command_message.update(
                        f"Could not extract improved code from response. Here's the full response:\n\n{response}"
                    )
                    return False

        except Exception as e:
            # Handle errors
            thinking.remove()
            command_message.update(f"Error processing {command} command: {str(e)}")

            import traceback

            print(f"Error in code command: {traceback.format_exc()}")
            return False

    async def show_diff_dialog(
        self,
        diff_text: str,
        original_code: str,
        improved_code: str,
        explanation: str = "",
    ):
        """
        Show a dialog with the diff between original and improved code.

        Args:
            diff_text: The diff text
            original_code: The original code
            improved_code: The improved code
            explanation: Optional explanation of changes
        """
        from terminatoride.screens.diff_view_screen import DiffViewScreen

        # Create a callback to apply the changes
        def apply_changes():
            if (
                hasattr(self.app, "query_one")
                and self.context
                and self.context.current_file
            ):
                # Get the editor panel
                editor_panel = self.app.query_one("#editor-panel")

                # Update the editor content with the improved code
                if hasattr(editor_panel, "set_content"):
                    editor_panel.set_content(improved_code)

                # Update the file context to reflect changes
                file_path = self.context.current_file.path
                self.context.update_current_file(file_path, improved_code)

                # Notify the user
                self.app.notify(
                    "Code changes applied successfully", severity="information"
                )

        # Create and show the diff view screen
        diff_screen = DiffViewScreen(
            diff_text=diff_text,
            apply_callback=apply_changes,
            title="Code Improvements",
            explanation=explanation,
        )

        await self.app.push_screen(diff_screen)
