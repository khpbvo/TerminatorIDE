import os
import pytest
from pathlib import Path
from terminatoride.config import Config, OpenAIConfig, AppConfig, get_config

class TestConfig:
    
    def test_config_from_env(self, monkeypatch):
        """Test loading config from environment variables."""
        # Set environment variables
        monkeypatch.setenv("OPENAI_API_KEY", "test_key")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4")
        monkeypatch.setenv("TERMINATOR_THEME", "light")
        
        # Load config from environment
        config = Config.from_env()
        
        # Check that values were loaded correctly
        assert config.openai.api_key == "test_key"
        assert config.openai.model == "gpt-4"
        assert config.app.theme == "light"
    
    def test_config_from_file(self, temp_config_file):
        """Test loading config from a file."""
        config = Config.load_from_file(temp_config_file)
        
        # Check that values were loaded correctly
        assert config.openai.model == "gpt-3.5-turbo"
        assert config.openai.temperature == 0.5
        assert config.app.theme == "dark"
        assert config.app.editor_type == "nano"
        assert config.app.show_line_numbers is True
        assert config.app.auto_save is False
    
    def test_save_config_to_file(self, tmp_path):
        """Test saving config to a file."""
        # Create a config
        config = Config(
            openai=OpenAIConfig(
                api_key="test_key",
                model="gpt-4",
                temperature=0.8
            ),
            app=AppConfig(
                theme="dark",
                editor_type="vim",
                show_line_numbers=True,
                auto_save=True
            )
        )
        
        # Save to file
        config_path = tmp_path / "test_config.json"
        config.save_to_file(config_path)
        
        # Load it back and verify
        loaded_config = Config.load_from_file(config_path)
        
        # API key should be redacted in the file
        assert loaded_config.openai.api_key != "test_key"
        assert loaded_config.openai.model == "gpt-4"
        assert loaded_config.openai.temperature == 0.8
        assert loaded_config.app.theme == "dark"
        assert loaded_config.app.editor_type == "vim"
