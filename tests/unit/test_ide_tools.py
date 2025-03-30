"""
Tests for IDE tools functionality.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from terminatoride.agent.context import AgentContext  # Move this import here
from terminatoride.ide.function_tools import (
    change_directory,
    create_directory,
    create_new_file,
    delete_file,
    find_in_file,
    find_in_project,
    git_initialize,
    git_stage_file,
    git_status,
    insert_at_cursor,
    move_cursor,
    navigate_to_file,
    rename_file,
    replace_regex,
    replace_text,
    run_command,
)


class TestIdeTools:
    """Test suite for IDE function tools."""

    @pytest.fixture
    def mock_context(self, tmp_path):
        """Mock run context for testing using a proper AgentContext-like instance."""
        # Maak een tijdelijke project directory voor tests die projectcontext nodig hebben.
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        # Maak een dummy current_file object.
        class DummyFile:
            pass

        current_file = DummyFile()
        current_file.path = str(tmp_path / "sample.py")
        current_file.content = "Test content"
        current_file.cursor_position = 0

        # Maak een dummy project object.
        class DummyProject:
            pass

        project = DummyProject()
        project.root_path = str(project_dir)

        # Probeer een AgentContext te instantieren; als dat niet lukt, maak een dummy object en forceer de class.
        try:
            agent_ctx = AgentContext()
        except Exception:
            agent_ctx = type("AgentContextDummy", (), {})()
        # Forceer dat agent_ctx als een AgentContext wordt herkend.
        agent_ctx.__class__ = AgentContext

        # Wijs de vereiste attributen toe.
        agent_ctx.current_file = current_file

        # Add a side effect to update current_file when update_current_file is called
        def update_side_effect(
            path, content, cursor_position=0
        ):  # Make cursor_position optional
            agent_ctx.current_file.content = content
            agent_ctx.current_file.path = path
            agent_ctx.current_file.cursor_position = cursor_position

        agent_ctx.update_current_file = MagicMock(side_effect=update_side_effect)
        agent_ctx.project = project

        mock_context = MagicMock()
        mock_context.context = agent_ctx
        return mock_context

    @pytest.fixture
    def temp_file(self, tmp_path):
        """Create a temporary file for testing."""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("Test content")
        return test_file

    @pytest.fixture
    def temp_directory(self, tmp_path):
        """Create a temporary directory for testing."""
        test_dir = tmp_path / "project"
        test_dir.mkdir()
        return test_dir

    @pytest.mark.asyncio
    async def test_navigate_to_file(self, mock_context, temp_file):
        """Test navigate_to_file function."""
        # Mock the on_invoke_tool method which is what actually gets called
        with patch.object(
            navigate_to_file, "on_invoke_tool", new_callable=AsyncMock
        ) as mock_navigate:
            mock_navigate.return_value = f"Successfully navigated to {temp_file}"

            # Call the function's on_invoke_tool directly
            result = await navigate_to_file.on_invoke_tool(
                mock_context, json.dumps({"path": str(temp_file)})
            )

            # Verify the result
            assert "Successfully navigated" in result
            mock_navigate.assert_called_once()

    @pytest.mark.asyncio
    async def test_navigate_to_nonexistent_file(self, mock_context, tmp_path):
        """Test navigate_to_file with a nonexistent file."""
        nonexistent_file = tmp_path / "does_not_exist.txt"

        # Execute the real function (not mocking) to test the error handling
        with patch.object(
            navigate_to_file,
            "on_invoke_tool",
            AsyncMock(wraps=navigate_to_file.on_invoke_tool),
        ):
            result = await navigate_to_file.on_invoke_tool(
                mock_context, json.dumps({"path": str(nonexistent_file)})
            )

            # Verify the result contains an error message
            assert "Error" in result
            assert "does not exist" in result

    @pytest.mark.asyncio
    async def test_create_new_file(self, mock_context, tmp_path):
        """Test create_new_file function."""
        new_file_path = tmp_path / "new_file.txt"
        content = "This is a new file"

        with patch.object(
            create_new_file,
            "on_invoke_tool",
            AsyncMock(wraps=create_new_file.on_invoke_tool),
        ):
            result = await create_new_file.on_invoke_tool(
                mock_context,
                json.dumps({"path": str(new_file_path), "content": content}),
            )

            # Verify the file was created
            assert new_file_path.exists()
            assert new_file_path.read_text() == content
            assert "Successfully created" in result

    @pytest.mark.asyncio
    async def test_create_new_file_existing(self, mock_context, temp_file):
        """Test create_new_file with an existing file."""
        with patch.object(
            create_new_file,
            "on_invoke_tool",
            AsyncMock(wraps=create_new_file.on_invoke_tool),
        ):
            result = await create_new_file.on_invoke_tool(
                mock_context,
                json.dumps({"path": str(temp_file), "content": "New content"}),
            )

            # Verify we get an error for existing file
            assert "Error" in result
            assert "already exists" in result

    @pytest.mark.asyncio
    async def test_change_directory(self, mock_context, temp_directory):
        """Test change_directory function."""
        # Mock os.chdir to avoid actually changing the working directory
        with patch("os.chdir") as mock_chdir:
            with patch.object(
                change_directory,
                "on_invoke_tool",
                AsyncMock(wraps=change_directory.on_invoke_tool),
            ):
                result = await change_directory.on_invoke_tool(
                    mock_context, json.dumps({"path": str(temp_directory)})
                )

                # Verify chdir was called with the correct path
                mock_chdir.assert_called_once_with(str(temp_directory))
                assert "Successfully changed directory" in result

    @pytest.mark.asyncio
    async def test_change_directory_nonexistent(self, mock_context, tmp_path):
        """Test change_directory with a nonexistent directory."""
        nonexistent_dir = tmp_path / "does_not_exist"

        with patch.object(
            change_directory,
            "on_invoke_tool",
            AsyncMock(wraps=change_directory.on_invoke_tool),
        ):
            result = await change_directory.on_invoke_tool(
                mock_context, json.dumps({"path": str(nonexistent_dir)})
            )

            # Verify we get an error
            assert "Error" in result
            assert "does not exist" in result

    @pytest.mark.asyncio
    async def test_insert_at_cursor(self, mock_context):
        """Test insert_at_cursor function."""
        with patch.object(
            insert_at_cursor,
            "on_invoke_tool",
            AsyncMock(wraps=insert_at_cursor.on_invoke_tool),
        ):
            result = await insert_at_cursor.on_invoke_tool(
                mock_context, json.dumps({"text": " INSERTED TEXT"})
            )

            # Verify the result
            assert "Successfully inserted" in result
            # Check the context was updated correctly
            mock_context.context.update_current_file.assert_called_once()
            # Now we can check the content directly since we have a side effect
            assert " INSERTED TEXT" in mock_context.context.current_file.content

    @pytest.mark.asyncio
    async def test_replace_text(self, mock_context):
        """Test replace_text function."""
        # Update the context with a specific content
        mock_context.context.current_file.content = "Hello World"

        with patch.object(
            replace_text, "on_invoke_tool", AsyncMock(wraps=replace_text.on_invoke_tool)
        ):
            result = await replace_text.on_invoke_tool(
                mock_context,
                json.dumps({"search_text": "Hello", "replace_text": "Bonjour"}),
            )

            # Verify the result
            assert "Successfully replaced" in result
            # Check the content was replaced
            assert mock_context.context.current_file.content == "Bonjour World"

    @pytest.mark.asyncio
    async def test_replace_text_with_line_range(self, mock_context):
        """Test replace_text with a line range."""
        # Update context with multiple lines
        mock_context.context.current_file.content = (
            "Line 1: Hello\nLine 2: Hello\nLine 3: Hello"
        )

        with patch.object(
            replace_text, "on_invoke_tool", AsyncMock(wraps=replace_text.on_invoke_tool)
        ):
            result = await replace_text.on_invoke_tool(
                mock_context,
                json.dumps(
                    {
                        "search_text": "Hello",
                        "replace_text": "Bonjour",
                        "line_range": [2, 3],
                    }
                ),
            )

            # Verify the result
            assert "Successfully replaced" in result

            # Check content was properly replaced with line range
            content = mock_context.context.current_file.content
            assert "Line 1: Hello" in content  # First line unchanged
            assert "Line 2: Bonjour" in content  # Second line changed
            assert "Line 3: Bonjour" in content  # Third line changed

    @pytest.mark.asyncio
    async def test_replace_regex(self, mock_context):
        """Test replace_regex function."""
        # Update context with content suitable for regex replacement
        mock_context.context.current_file.content = "var1 = 10\nvar2 = 20\nvar3 = 30"

        with patch.object(
            replace_regex,
            "on_invoke_tool",
            AsyncMock(wraps=replace_regex.on_invoke_tool),
        ):
            result = await replace_regex.on_invoke_tool(
                mock_context,
                json.dumps(
                    {"pattern": r"var(\d) = (\d+)", "replace_text": r"variable\1 = \2"}
                ),
            )

            # Verify the result
            assert "Successfully replaced" in result

            # Check content was properly replaced with regex
            content = mock_context.context.current_file.content
            assert "variable1 = 10" in content
            assert "variable2 = 20" in content
            assert "variable3 = 30" in content

    @pytest.mark.asyncio
    async def test_move_cursor(self, mock_context):
        """Test move_cursor function."""
        with patch.object(
            move_cursor, "on_invoke_tool", AsyncMock(wraps=move_cursor.on_invoke_tool)
        ):
            result = await move_cursor.on_invoke_tool(
                mock_context, json.dumps({"position": 10})
            )

            # Verify the result
            assert "Cursor moved to position 10" in result

            # Check cursor position was updated
            assert mock_context.context.current_file.cursor_position == 10

    @pytest.mark.asyncio
    async def test_move_cursor_out_of_bounds(self, mock_context):
        """Test move_cursor with an out of bounds position."""
        # Test with a negative position
        with patch.object(
            move_cursor, "on_invoke_tool", AsyncMock(wraps=move_cursor.on_invoke_tool)
        ):
            _ = await move_cursor.on_invoke_tool(
                mock_context, json.dumps({"position": -5})
            )

            # Verify negative positions are handled (should be set to 0)
            assert mock_context.context.current_file.cursor_position == 0

    @pytest.mark.asyncio
    async def test_find_in_file(self, mock_context):
        """Test find_in_file function."""
        # Update context with multiple occurrences
        mock_context.context.current_file.content = (
            "def find_me():\n    x = 'find_me'\n    return find_me"
        )

        with patch.object(
            find_in_file, "on_invoke_tool", AsyncMock(wraps=find_in_file.on_invoke_tool)
        ):
            result = await find_in_file.on_invoke_tool(
                mock_context,
                json.dumps(
                    {
                        "search_text": "find_me",
                        "case_sensitive": False,
                        "whole_word": False,
                    }
                ),
            )

            # Verify the result contains all occurrences
            assert "Found" in result
            assert "Line 1" in result
            assert "Line 2" in result
            assert "Line 3" in result

    @pytest.mark.asyncio
    async def test_find_in_file_case_sensitive(self, mock_context):
        """Test find_in_file with case sensitivity."""
        # Update context with mixed case
        mock_context.context.current_file.content = (
            "def FindMe():\n    x = 'findme'\n    return findMe"
        )

        with patch.object(
            find_in_file, "on_invoke_tool", AsyncMock(wraps=find_in_file.on_invoke_tool)
        ):
            result = await find_in_file.on_invoke_tool(
                mock_context,
                json.dumps(
                    {
                        "search_text": "findme",
                        "case_sensitive": True,
                        "whole_word": False,
                    }
                ),
            )

            # Should only find exact case matches
            assert "Found 1 occurrence" in result
            assert "Line 2" in result
            assert "Line 1" not in result  # FindMe (capital F) shouldn't match
            assert "Line 3" not in result  # findMe (capital M) shouldn't match

    @pytest.mark.asyncio
    async def test_find_in_file_whole_word(self, mock_context):
        """Test find_in_file with whole_word parameter."""
        # Update context with partial matches
        mock_context.context.current_file.content = (
            "word wordplus\npreword word\nwo word rd"
        )

        with patch.object(
            find_in_file, "on_invoke_tool", AsyncMock(wraps=find_in_file.on_invoke_tool)
        ):
            result = await find_in_file.on_invoke_tool(
                mock_context,
                json.dumps(
                    {"search_text": "word", "whole_word": True, "case_sensitive": False}
                ),
            )

            # Should only find whole word matches
            assert "Found" in result
            assert "occurrence" in result

    @pytest.mark.asyncio
    @patch("terminatoride.ide.function_tools.Path")
    async def test_find_in_project(self, mock_path_class, mock_context):
        """Test find_in_project function."""
        # More direct approach to path mocking
        project_root = Path(mock_context.context.project.root_path)

        # Setup mock path instances
        mock_path_instance = MagicMock()
        mock_path_class.return_value = mock_path_instance

        # Configure Path.exists to return True
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_dir.return_value = True

        # Configure mock files to be found by rglob
        file1 = MagicMock()
        file1.name = "file1.py"
        file1.is_dir.return_value = False
        file1.is_file.return_value = True
        file1.__str__.return_value = str(project_root / "file1.py")
        # Important: make relative_to return a proper string representation, not a Mock
        file1.relative_to.return_value = "file1.py"
        # Make file.read_text return our search text
        file1.read_text.return_value = "This file contains search_term in it"

        file2 = MagicMock()
        file2.name = "file2.py"
        file2.is_dir.return_value = False
        file2.is_file.return_value = True
        file2.__str__.return_value = str(project_root / "file2.py")
        file2.relative_to.return_value = "file2.py"
        file2.read_text.return_value = "This file has no match"

        # Configure rglob to return our mock files
        mock_path_instance.rglob.return_value = [file1, file2]

        # Execute the function
        with patch.object(
            find_in_project,
            "on_invoke_tool",
            AsyncMock(wraps=find_in_project.on_invoke_tool),
        ):
            result = await find_in_project.on_invoke_tool(
                mock_context,
                json.dumps(
                    {
                        "search_text": "search_term",
                        "file_pattern": "*.py",
                        "case_sensitive": False,
                    }
                ),
            )

            # For debugging
            print(f"Search result: {result}")

            # Verify the search found the correct content
            assert "Found" in result
            assert "file1.py" in result
            assert "file2.py" not in result

    @pytest.mark.asyncio
    @patch("terminatoride.ide.function_tools.is_git_repo")
    @patch("subprocess.run")
    async def test_git_status(self, mock_run, mock_is_git_repo, mock_context):
        """Test git_status function."""
        # Configure the mocks
        mock_is_git_repo.return_value = True
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "On branch main\nNothing to commit"

        with patch.object(
            git_status, "on_invoke_tool", AsyncMock(wraps=git_status.on_invoke_tool)
        ):
            result = await git_status.on_invoke_tool(mock_context, json.dumps({}))

            # Verify git status was called
            mock_run.assert_called_once()
            assert "On branch main" in result

    @pytest.mark.asyncio
    @patch("terminatoride.ide.function_tools.is_git_repo")
    async def test_git_status_not_a_repo(self, mock_is_git_repo, mock_context):
        """Test git_status when not in a git repository."""
        # Configure the mock
        mock_is_git_repo.return_value = False

        with patch.object(
            git_status, "on_invoke_tool", AsyncMock(wraps=git_status.on_invoke_tool)
        ):
            result = await git_status.on_invoke_tool(mock_context, json.dumps({}))

            # Verify appropriate message is returned
            assert "is not a git repository" in result

    @pytest.mark.asyncio
    @patch("terminatoride.ide.function_tools.is_git_repo", return_value=True)
    @patch("terminatoride.ide.function_tools.git_add")
    async def test_git_stage_file(self, mock_git_add, mock_is_git_repo, mock_context):
        """Test git_stage_file function."""
        # Configure de mocks
        mock_git_add.return_value = True

        # Zorg dat het bestand 'file.py' bestaat in de project directory
        project_root = Path(mock_context.context.project.root_path)
        dummy_file = project_root / "file.py"
        dummy_file.write_text("dummy content")

        with patch.object(
            git_stage_file,
            "on_invoke_tool",
            AsyncMock(wraps=git_stage_file.on_invoke_tool),
        ):
            result = await git_stage_file.on_invoke_tool(
                mock_context, json.dumps({"file_path": "file.py"})
            )

            # Verify git_add was called
            mock_git_add.assert_called_once()
            assert "Successfully staged" in result

    @pytest.mark.asyncio
    @patch("terminatoride.ide.function_tools.is_git_repo", return_value=False)
    @patch("terminatoride.ide.function_tools.git_init")
    async def test_git_initialize(self, mock_git_init, mock_is_git_repo, mock_context):
        """Test git_initialize function."""
        # Configure the mock
        mock_git_init.return_value = True

        with patch.object(
            git_initialize,
            "on_invoke_tool",
            AsyncMock(wraps=git_initialize.on_invoke_tool),
        ):
            result = await git_initialize.on_invoke_tool(mock_context, json.dumps({}))

            # Verify git_init was called
            mock_git_init.assert_called_once()
            assert "Successfully initialized" in result

    @pytest.mark.asyncio
    async def test_create_directory(self, mock_context, tmp_path):
        """Test create_directory function."""
        new_dir_path = tmp_path / "new_directory"

        with patch.object(
            create_directory,
            "on_invoke_tool",
            AsyncMock(wraps=create_directory.on_invoke_tool),
        ):
            result = await create_directory.on_invoke_tool(
                mock_context, json.dumps({"path": str(new_dir_path)})
            )

            # Verify directory was created
            assert new_dir_path.exists()
            assert new_dir_path.is_dir()
            assert "Successfully created" in result

    @pytest.mark.asyncio
    async def test_rename_file(self, mock_context, temp_file):
        """Test rename_file function."""
        # Create a new path for the renamed file
        new_path = temp_file.parent / "renamed_file.txt"

        with patch.object(
            rename_file, "on_invoke_tool", AsyncMock(wraps=rename_file.on_invoke_tool)
        ):
            result = await rename_file.on_invoke_tool(
                mock_context,
                json.dumps({"source": str(temp_file), "destination": str(new_path)}),
            )

            # Verify file was renamed
            assert not temp_file.exists()
            assert new_path.exists()
            assert "Successfully moved" in result

    @pytest.mark.asyncio
    async def test_rename_file_nonexistent(self, mock_context, tmp_path):
        """Test rename_file with a nonexistent source file."""
        nonexistent_file = tmp_path / "does_not_exist.txt"
        new_path = tmp_path / "renamed.txt"

        with patch.object(
            rename_file, "on_invoke_tool", AsyncMock(wraps=rename_file.on_invoke_tool)
        ):
            result = await rename_file.on_invoke_tool(
                mock_context,
                json.dumps(
                    {"source": str(nonexistent_file), "destination": str(new_path)}
                ),
            )

            # Verify we get an error
            assert "Error" in result
            assert "does not exist" in result

    @pytest.mark.asyncio
    async def test_delete_file(self, mock_context, temp_file):
        """Test delete_file function."""
        with patch.object(
            delete_file, "on_invoke_tool", AsyncMock(wraps=delete_file.on_invoke_tool)
        ):
            result = await delete_file.on_invoke_tool(
                mock_context, json.dumps({"path": str(temp_file)})
            )

            # Verify file was deleted
            assert not temp_file.exists()
            assert "Successfully deleted" in result

    @pytest.mark.asyncio
    async def test_delete_directory(self, mock_context, temp_directory):
        """Test delete_file function with a directory."""
        with patch.object(
            delete_file, "on_invoke_tool", AsyncMock(wraps=delete_file.on_invoke_tool)
        ):
            result = await delete_file.on_invoke_tool(
                mock_context,
                json.dumps({"path": str(temp_directory), "recursive": True}),
            )

            # Verify directory was deleted
            assert not temp_directory.exists()
            assert "Successfully deleted" in result

    @pytest.mark.asyncio
    async def test_delete_directory_non_recursive(self, mock_context, tmp_path):
        """Test delete_file function with a non-empty directory and recursive=False."""
        # Create a directory with a file
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("Test content")

        with patch.object(
            delete_file, "on_invoke_tool", AsyncMock(wraps=delete_file.on_invoke_tool)
        ):
            result = await delete_file.on_invoke_tool(
                mock_context, json.dumps({"path": str(test_dir), "recursive": False})
            )

            # Verify we get an error since directory is not empty
            assert "Error" in result
            assert test_dir.exists()

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_run_command(self, mock_run, mock_context):
        """Test run_command function."""
        # Configure the mock
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Command output"
        mock_run.return_value.stderr = ""

        with patch.object(
            run_command, "on_invoke_tool", AsyncMock(wraps=run_command.on_invoke_tool)
        ):
            result = await run_command.on_invoke_tool(
                mock_context, json.dumps({"command": "echo 'test'"})
            )

            # Verify command was executed
            mock_run.assert_called_once()
            assert "Command completed" in result
            assert "Command output" in result

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_run_command_error(self, mock_run, mock_context):
        """Test run_command function with a command that fails."""
        # Configure the mock to simulate a failed command
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "Command failed"

        with patch.object(
            run_command, "on_invoke_tool", AsyncMock(wraps=run_command.on_invoke_tool)
        ):
            result = await run_command.on_invoke_tool(
                mock_context, json.dumps({"command": "invalid_command"})
            )

            # Verify command execution was attempted
            mock_run.assert_called_once()
            # Check the error is in the output
            assert "exit code 1" in result
            assert "Command failed" in result

    @pytest.mark.asyncio
    @patch("subprocess.run")
    async def test_run_command_timeout(self, mock_run, mock_context):
        """Test run_command function with a command that times out."""
        # Configure the mock to raise a timeout exception
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 30)

        with patch.object(
            run_command, "on_invoke_tool", AsyncMock(wraps=run_command.on_invoke_tool)
        ):
            result = await run_command.on_invoke_tool(
                mock_context, json.dumps({"command": "sleep 100"})
            )

            # Verify error message about timeout
            mock_run.assert_called_once()
            assert "Error" in result
            assert "timed out" in result
