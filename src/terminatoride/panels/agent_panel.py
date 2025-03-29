"""
Example of integrating the OpenAI Agent with the agent panel.
This shows how to connect the UI with the agent functionality.
"""

import asyncio

from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer, Vertical
from textual.message import Message
from textual.widgets import Button, Input, Label, Static

from terminatoride.agent.context import AgentContext, FileContext
from terminatoride.agents.openai_agent import get_openai_agent


class AgentPanel(Container):
    """The right panel of the IDE for AI agent interactions."""

    class AgentResponse(Message):
        """Message containing the agent's response."""

        def __init__(self, response: str):
            self.response = response
            super().__init__()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent = get_openai_agent()
        self.context = AgentContext()

    def compose(self) -> ComposeResult:
        """Compose the agent panel widget."""
        yield Label("AI Assistant", id="agent-title")

        with ScrollableContainer(id="conversation-container"):
            yield Vertical(id="conversation")

        with Container(id="input-container"):
            yield Input(placeholder="Ask the AI assistant...", id="agent-input")
            yield Button("Send", id="send-button", variant="primary")

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        # Add welcome message
        conversation = self.query_one("#conversation")
        conversation.mount(
            Static(
                "👋 Hello! I'm your AI assistant. How can I help you today?",
                classes="agent-message",
            )
        )

        # Connect event handlers
        input_widget = self.query_one("#agent-input")
        input_widget.focus()

        send_button = self.query_one("#send-button")
        send_button.on_click = self._on_send_click

    async def _on_send_click(self) -> None:
        """Handle send button click."""
        input_widget = self.query_one("#agent-input")
        user_message = input_widget.value

        if not user_message.strip():
            return

        # Add user message to conversation
        conversation = self.query_one("#conversation")
        conversation.mount(Static(f"You: {user_message}", classes="user-message"))

        # Clear input
        input_widget.value = ""
        input_widget.focus()

        # Get current file context if available
        self._update_context()

        # Show "thinking" indicator
        thinking = Static("Assistant is thinking...", classes="agent-thinking")
        conversation.mount(thinking)

        # Process in background to keep UI responsive
        self.app.run_worker(self._process_agent_response(user_message, thinking))

    async def _process_agent_response(
        self, user_message: str, thinking_indicator: Static
    ) -> None:
        """Process the agent response in a background worker."""
        try:
            # Get response from agent
            response = await self.agent.generate_response(user_message, self.context)

            # Remove thinking indicator
            thinking_indicator.remove()

            # Add response to conversation
            conversation = self.query_one("#conversation")
            conversation.mount(
                Static(f"Assistant: {response}", classes="agent-message")
            )

            # Auto-scroll to bottom
            container = self.query_one("#conversation-container")
            await container.scroll_end()

            # Post message for potential use by other components
            self.post_message(self.AgentResponse(response))

        except Exception as e:
            # Handle errors
            thinking_indicator.remove()
            conversation = self.query_one("#conversation")
            conversation.mount(Static(f"Error: {str(e)}", classes="agent-error"))

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


# Example usage in a test environment
async def test_agent_interaction():
    """Test the agent interaction in a standalone context."""
    agent = get_openai_agent()
    context = AgentContext()

    # Add a sample file context
    sample_file = FileContext(
        path="/path/to/sample.py",
        content="def hello_world():\n    print('Hello, World!')\n\nhello_world()",
        language="python",
    )
    context.update_current_file(sample_file.path, sample_file.content)

    # Test a simple query
    response = await agent.generate_response("Can you explain this code?", context)
    print(f"Agent response: {response}")


if __name__ == "__main__":
    # Run a standalone test
    asyncio.run(test_agent_interaction())
