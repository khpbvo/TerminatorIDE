"""
Enhanced Agent Panel with streaming capabilities for TerminatorIDE.
This panel displays real-time responses from the AI assistant.
"""

import asyncio

from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Input, Label, LoadingIndicator, Static

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

        # Conversation container should take up all available space
        with ScrollableContainer(id="conversation-container"):
            yield VerticalScroll(id="conversation")

        # Input container with horizontal layout - DO NOT add the horizontal-input class here
        # Instead, rely solely on the CSS for styling
        with Container(id="input-container"):
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

        # Always use streaming (removed toggle check)
        streaming_enabled = True

        # Processing indicator
        if streaming_enabled:
            # For streaming, create a response container that will be updated
            self.current_response_widget = Static(
                "Assistant: ", classes="agent-message"
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
        try:
            # Create wrapper callbacks without debug widget updates
            async def debug_text_delta(delta: str):
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
                print(f"Tool call: {tool_info}")
                await self._handle_tool_call(tool_info)

            async def debug_tool_result(result_info: dict):
                print(f"Tool result: {result_info}")
                await self._handle_tool_result(result_info)

            async def debug_handoff(handoff_info: dict):
                print(f"Handoff: {handoff_info}")
                await self._handle_handoff(handoff_info)

            # Try using the streaming approach first
            try:
                print("Starting streaming response generation")
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
                self.current_response_widget.update(f"Assistant: {result}")

            # Post event for potential use by other components
            if self.current_response_widget:
                self.post_message(
                    self.AgentResponse(self.current_response_widget.renderable)
                )

            # One final scroll to bottom after all streaming
            await self._scroll_to_bottom()

        except Exception as e:
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

                # Update the widget with the new text
                self.current_response_widget.update(new_text)

                # Auto-scroll
                await self._scroll_to_bottom()
        except Exception as e:
            print(f"Error in _handle_text_delta: {e}")
            # Create a new widget if there was a problem
            try:
                conversation = self.query_one("#conversation")
                self.current_response_widget = Static(
                    f"Assistant: {delta}", classes="agent-message"
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
