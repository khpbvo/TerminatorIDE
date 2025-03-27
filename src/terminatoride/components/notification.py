"""Notification component for TerminatorIDE."""

from textual.containers import Container
from textual.widget import Widget
from textual.widgets import Static
from textual.app import ComposeResult
from textual.message import Message


class Notification(Widget):
    """A notification widget that shows a message and then disappears."""
    
    DEFAULT_CSS = """
    Notification {
        width: 40%;
        height: auto;
        dock: bottom;
        layer: notification;
        background: $accent;
        color: $text;
        padding: 1;
        margin: 2;
        border: solid $primary;
        text-align: center;
    }
    
    Notification.info {
        background: $primary;
    }
    
    Notification.success {
        background: $success;
    }
    
    Notification.warning {
        background: $warning;
    }
    
    Notification.error {
        background: $error;
    }
    """
    
    class Dismissed(Message):
        """Message sent when notification is dismissed."""
        
        def __init__(self, notification: "Notification") -> None:
            self.notification = notification
            super().__init__()
    
    def __init__(
        self, 
        message: str, 
        level: str = "info", 
        timeout: float = 3.0, 
        *args, 
        **kwargs
    ):
        """Initialize the notification.
        
        Args:
            message: The message to display.
            level: The notification level (info, success, warning, error).
            timeout: The time in seconds before the notification disappears.
        """
        super().__init__(*args, **kwargs)
        self.message = message
        self.level = level
        self.timeout = timeout
    
    def compose(self) -> ComposeResult:
        """Compose the notification widget."""
        yield Static(self.message)
    
    def on_mount(self) -> None:
        """Handle mount event and set auto-dismiss timer."""
        self.add_class(self.level)
        if self.timeout > 0:
            self.set_timer(self.timeout, self.dismiss)
    
    def dismiss(self) -> None:
        """Dismiss the notification."""
        self.post_message(self.Dismissed(self))
        self.remove()


class NotificationManager(Widget):
    """Manages notifications in the application."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the notification manager."""
        super().__init__(*args, **kwargs)
        self.notifications = []
    
    def show_notification(
        self, 
        message: str, 
        level: str = "info", 
        timeout: float = 3.0
    ) -> Notification:
        """Show a notification.
        
        Args:
            message: The notification message.
            level: The notification level (info, success, warning, error).
            timeout: The time in seconds before the notification disappears.
        
        Returns:
            The created notification widget.
        """
        notification = Notification(message, level, timeout)
        self.notifications.append(notification)
        self.mount(notification)
        return notification
    
    def on_notification_dismissed(self, event: Notification.Dismissed) -> None:
        """Handle notification dismissed events."""
        if event.notification in self.notifications:
            self.notifications.remove(event.notification) 