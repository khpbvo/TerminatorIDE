import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class OpenAIConfig:
    api_key: str
    organization: Optional[str] = None
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: Optional[int] = None


@dataclass
class AppConfig:
    theme: str = "dark"
    editor_type: str = "vim"  # Options: vim, nano, emacs
    show_line_numbers: bool = True
    auto_save: bool = True


@dataclass
class Config:
    openai: OpenAIConfig
    app: AppConfig

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        if "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        api_key = os.environ.get("OPENAI_API_KEY")
        return cls(
            openai=OpenAIConfig(
                api_key=api_key,
                organization=os.environ.get("OPENAI_ORGANIZATION"),
                model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
                temperature=float(os.environ.get("OPENAI_TEMPERATURE", "0.7")),
                max_tokens=(
                    int(os.environ.get("OPENAI_MAX_TOKENS"))
                    if os.environ.get("OPENAI_MAX_TOKENS")
                    else None
                ),
            ),
            app=AppConfig(
                theme=os.environ.get("TERMINATOR_THEME", "dark"),
                editor_type=os.environ.get("TERMINATOR_EDITOR", "vim"),
                show_line_numbers=os.environ.get(
                    "TERMINATOR_SHOW_LINE_NUMBERS", "True"
                ).lower()
                == "true",
                auto_save=os.environ.get("TERMINATOR_AUTO_SAVE", "True").lower()
                == "true",
            ),
        )

    @classmethod
    def load_from_file(cls, config_path: Path) -> "Config":
        """Load configuration from a JSON file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found at {config_path}")

        with open(config_path, "r") as f:
            config_data = json.load(f)

        openai_data = config_data.get("openai", {})
        app_data = config_data.get("app", {})

        return cls(
            openai=OpenAIConfig(
                api_key=openai_data.get(
                    "api_key", os.environ.get("OPENAI_API_KEY", "")
                ),
                organization=openai_data.get("organization"),
                model=openai_data.get("model", "gpt-4o"),
                temperature=openai_data.get("temperature", 0.7),
                max_tokens=openai_data.get("max_tokens"),
            ),
            app=AppConfig(
                theme=app_data.get("theme", "dark"),
                editor_type=app_data.get("editor_type", "vim"),
                show_line_numbers=app_data.get("show_line_numbers", True),
                auto_save=app_data.get("auto_save", True),
            ),
        )

    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to a JSON file."""
        config_data = {
            "openai": {
                "api_key": "[REDACTED]",  # Never save API key to file
                "organization": self.openai.organization,
                "model": self.openai.model,
                "temperature": self.openai.temperature,
                "max_tokens": self.openai.max_tokens,
            },
            "app": {
                "theme": self.app.theme,
                "editor_type": self.app.editor_type,
                "show_line_numbers": self.app.show_line_numbers,
                "auto_save": self.app.auto_save,
            },
        }

        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=2)


def get_config() -> Config:
    """Get the application configuration."""
    # Check for config file
    config_path = Path.home() / ".config" / "terminatoride" / "config.json"

    if config_path.exists():
        try:
            return Config.load_from_file(config_path)
        except (json.JSONDecodeError, FileNotFoundError):
            # Fall back to env vars if config file is invalid
            pass

    # Fall back to environment variables
    return Config.from_env()
