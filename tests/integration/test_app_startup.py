import pytest
from textual.driver import Driver
from terminatoride.app import TerminatorIDE

class TestAppStartup:
    @pytest.mark.asyncio  # Make sure to keep this decorator
    async def test_app_startup(self):
        """Test that the app can start up without errors."""
        app = TerminatorIDE()
        
        # Use Textual's testing driver
        async with app.run_test() as pilot:
            # Check that our main UI components are present
            # Remove await as query_one is synchronous in your version
            assert pilot.app.query_one("#left-panel")
            assert pilot.app.query_one("#editor-panel")
            assert pilot.app.query_one("#agent-panel")
            
            # Check the title is correct
            assert app.title == "TerminatorIDE"
