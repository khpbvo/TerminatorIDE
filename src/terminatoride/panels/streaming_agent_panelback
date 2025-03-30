"""
Enhanced Agent Panel with streaming capabilities for TerminatorIDE.
This panel displays real-time responses from the AI assistant.
"""

import asyncio

from rich.syntax import Syntax
from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer, Vertical
from textual.message import Message
from textual.widgets import Button, Checkbox, Input, Label, LoadingIndicator, Static

from terminatoride.agent.context import AgentContext
from terminatoride.agent_streaming import get_streaming_agent


class StreamingAgentPanel(Container):
    """Enhanced Agent Panel with streaming capabilities."""

    class AgentResponse(Message):
        """Message containing the agent's response."""

        def __init__(self, response: str):
            self.response = response
            super().__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.streaming_agent = get_streaming_agent()
        self.context = AgentContext()
        self.current_response_widget = None

    def compose(self) -> ComposeResult:
        """Compose the streaming agent panel widget."""
        yield Label("AI Assistant", id="agent-title")

        with ScrollableContainer(id="conversation-container"):
            yield Vertical(id="conversation")

        with Container(id="input-container"):
            with Container(id="streaming-options"):
                yield Checkbox("Enable Streaming", id="streaming-toggle", value=True)

            yield Input(placeholder="Ask the AI assistant...", id="agent-input")
            yield Button("Send", id="send-button", variant="primary")

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        # Add welcome message
        conversation = self.query_one("#conversation")
        conversation.mount(
            Static(
                "👋 Hello! I'm your AI assistant with streaming capabilities. How can I help you today?",
                classes="agent-message",
            )
        )

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

        # Add user message to conversation
        conversation = self.query_one("#conversation")
        conversation.mount(Static(f"You: {user_message}", classes="user-message"))

        # Clear input and keep focus
        input_field.value = ""
        input_field.focus()

        # Get current file context if available
        self._update_context()

        # Check if streaming is enabled
        streaming_enabled = self.query_one("#streaming-toggle").value

        # Processing indicator
        if streaming_enabled:
            # For streaming, create a response container that will be updated
            self.current_response_widget = Static(
                "Assistant: ", classes="agent-message"
            )
            conversation.mount(self.current_response_widget)
        else:
            # For non-streaming, show a loading indicator
            loading = LoadingIndicator(classes="agent-thinking")
            conversation.mount(loading)
            self.current_response_widget = None

        # Process in background to keep UI responsive
        if streaming_enabled:
            self.app.run_worker(self._process_streaming_response(user_message))
        else:
            self.app.run_worker(self._process_standard_response(user_message, loading))

        # Auto-scroll to bottom
        await self._scroll_to_bottom()

    class CodeUpdate(Message):
        """Message containing code from the AI."""

        def __init__(self, code: str, language: str):
            self.code = code
            self.language = language
            super().__init__()

    async def _handle_code_block(self, code: str, language: str) -> None:
        """Handle code blocks from the AI response."""
        # Add the code to the conversation with syntax highlighting
        conversation = self.query_one("#conversation")

        # Create a syntax highlighted version for the conversation
        syntax_widget = Syntax(code, language, theme="monokai", line_numbers=True)
        conversation.mount(Static(syntax_widget, classes="agent-code"))

        # Send an update message for the editor
        self.post_message(self.CodeUpdate(code, language))

        # Auto-scroll to bottom
        await self._scroll_to_bottom()

    async def _process_streaming_response(self, user_message: str) -> None:
        """Process the streaming agent response."""
        try:
            # Add debug message to conversation
            conversation = self.query_one("#conversation")
            debug_widget = Static(
                "Starting streaming request...", classes="debug-message"
            )
            conversation.mount(debug_widget)

            # Get streaming response from agent
            _ = await self.streaming_agent.generate_streaming_response(
                user_message,
                self.context,
                on_text_delta=self._handle_text_delta,
                on_tool_call=self._handle_tool_call,
                on_tool_result=self._handle_tool_result,
                on_handoff=self._handle_handoff,
            )

            # Update debug message with success status
            debug_widget.update("Streaming completed successfully")

            # Remove debug widget after short delay
            async def remove_debug():
                import asyncio

                await asyncio.sleep(2)
                debug_widget.remove()

            # Start the removal task
            self.app.run_worker(remove_debug())

            # Post event for potential use by other components
            if self.current_response_widget:
                self.post_message(
                    self.AgentResponse(self.current_response_widget.renderable)
                )

            # One final scroll to bottom after all streaming
            await self._scroll_to_bottom()

        except Exception as e:
            # Handle errors with more details
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
            debug_widget = Static("Processing request...", classes="debug-message")
            conversation.mount(debug_widget)

            # Try using the streaming agent but in non-streaming mode
            print("Starting non-streaming request using streaming agent")
            try:
                # Use the same generate_streaming_response but without callbacks
                response = await self.streaming_agent.generate_streaming_response(
                    user_message, self.context
                )
                print(f"Received response via streaming agent: {response[:50]}...")
            except Exception as direct_err:
                print(
                    f"Direct streaming request failed: {direct_err}, falling back to base agent"
                )
                # Fall back to traditional generate_response
                response = await self.streaming_agent.base_agent.generate_response(
                    user_message, self.context
                )
                print(f"Received fallback response: {response[:50]}...")

            # Remove loading indicator
            if loading_indicator in conversation.children:
                loading_indicator.remove()

            # Add response to conversation
            conversation.mount(
                Static(f"Assistant: {response}", classes="agent-message")
            )

            # Remove debug widget
            if debug_widget in conversation.children:
                debug_widget.remove()

            # Auto-scroll to bottom
            await self._scroll_to_bottom()

            # Post message for potential use by other components
            self.post_message(self.AgentResponse(response))

        except Exception as e:
            import traceback

            error_text = f"Error: {str(e)}\n\n{traceback.format_exc()}"
            print(f"Error in standard response: {error_text}")

            # Remove loading indicator
            if loading_indicator in conversation.children:
                loading_indicator.remove()

            conversation = self.query_one("#conversation")
            conversation.mount(Static(f"Error: {str(e)}", classes="agent-error"))
            await self._scroll_to_bottom()

    async def _handle_text_delta(self, delta: str) -> None:
        """Handle text delta events from streaming."""
        if self.current_response_widget:
            # Get the current text
            current_text = self.current_response_widget.renderable

            # If this is the first token, add the "Assistant: " prefix
            if current_text == "Assistant: ":
                new_text = current_text + delta
            else:
                new_text = current_text + delta

            # Update the widget with the new text
            self.current_response_widget.update(new_text)
            # Scroll to bottom
            await self._scroll_to_bottom()

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
        conversation = self.query_one("#conversation")
        conversation.mount(
            Static(
                f"🔄 Handing off from {handoff_info['from_agent']} to {handoff_info['to_agent']}",
                classes="agent-handoff",
            )
        )
        # Scroll to bottom
        await self._scroll_to_bottom()

    async def _scroll_to_bottom(self) -> None:
        """Scroll the conversation to the bottom."""
        try:
            container = self.query_one("#conversation-container", ScrollableContainer)
            if container is not None:
                await container.scroll_end(animate=False)
        except Exception as e:
            # Safely handle any errors during scrolling without crashing
            print(f"Error scrolling to bottom: {e}")

    def _update_context(self) -> None:
        """Update the agent context with current IDE state."""
        # This would be connected to the actual editor state in the real app
        # For now, we'll use a placeholder implementation

        # Example: Get the current file from the editor panel if it exists
        current_file = (
            self.app.query_one("#editor-panel").current_file
            if hasattr(self.app.query_one("#editor-panel"), "current_file")
            else None
        )

        if current_file:
            # Update context with current file info
            self.context.update_current_file(
                path=current_file.path,
                content=current_file.content,
                cursor_position=(
                    current_file.cursor_position
                    if hasattr(current_file, "cursor_position")
                    else 0
                ),
            )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in the input field."""
        if event.input.id == "agent-input":
            asyncio.create_task(self._on_send_click())
