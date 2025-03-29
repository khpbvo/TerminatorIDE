"""
Model selection and configuration for TerminatorIDE agents.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class ModelType(Enum):
    """Available model types for agents."""

    GPT4O = "gpt-4o"
    GPT4 = "gpt-4"  # Added for completeness
    GPT35TURBO = "gpt-3.5-turbo"  # Added for completeness
    O3MINI = "o3-mini"

    @classmethod
    def get_default(cls) -> "ModelType":
        """Get the default model type."""
        return cls.GPT4O

    @classmethod
    def from_string(cls, name: str) -> "ModelType":
        """Convert string to model type."""
        name = name.lower()
        for model in cls:
            if model.value == name:
                return model
        # Default to GPT-4o if not found
        return cls.GPT4O


@dataclass
class ModelSettings:
    """Settings for a model."""

    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert settings to a dictionary, excluding None values.
        This ensures we only send parameters actually supported by the model.
        """
        return {
            k: v
            for k, v in {
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "top_p": self.top_p,
                "presence_penalty": self.presence_penalty,
                "frequency_penalty": self.frequency_penalty,
            }.items()
            if v is not None
        }


class ModelSelector:
    """Utility for selecting and configuring models."""

    @staticmethod
    def get_model_string(model_type: ModelType) -> str:
        """Get the string representation of a model type."""
        return model_type.value

    @staticmethod
    def get_recommended_settings(model_type: ModelType) -> ModelSettings:
        """
        Get recommended settings for a model type.
        Different models support different parameters, so we customize per model.
        """
        if model_type == ModelType.GPT4O:
            return ModelSettings(
                temperature=0.7,
                max_tokens=4096,
                top_p=1.0,
                presence_penalty=0.0,
                frequency_penalty=0.0,
            )
        elif model_type == ModelType.GPT4:
            return ModelSettings(
                temperature=0.7,
                max_tokens=4096,
                top_p=1.0,
                presence_penalty=0.0,
                frequency_penalty=0.0,
            )
        elif model_type == ModelType.GPT35TURBO:
            return ModelSettings(
                temperature=0.8,
                max_tokens=4096,
                top_p=1.0,
                presence_penalty=0.0,
                frequency_penalty=0.0,
            )
        elif model_type == ModelType.O3MINI:
            # o3-mini may have different parameter support
            # Keep it simpler with just essential parameters
            return ModelSettings(
                temperature=None,
                max_tokens=100000,
                # Omitting other parameters that might not be supported
                top_p=None,
                presence_penalty=None,
                frequency_penalty=None,
            )
        else:
            # Default settings
            return ModelSettings()

    @staticmethod
    def create_run_config(
        model_type: Optional[ModelType] = None, settings: Optional[ModelSettings] = None
    ) -> Dict[str, Any]:
        """
        Create a run configuration for the Agent SDK.

        Args:
            model_type: Optional model type to use
            settings: Optional model settings to use

        Returns:
            A dictionary suitable for use as RunConfig
        """
        config = {}

        if model_type:
            config["model"] = ModelSelector.get_model_string(model_type)

        if settings:
            # Only include settings that are not None
            config["model_settings"] = settings.to_dict()

        return config
