"""
Base mode interface for Pombi AI Assistant conversation modes
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pydantic import BaseModel


class ModeConfig(BaseModel):
    """Configuration for conversation modes"""
    name: str
    description: str
    capabilities: List[str]
    recommended_models: List[str]
    temperature_range: tuple = (0.0, 1.0)
    max_tokens_suggestion: int = 2000


class BaseMode(ABC):
    """Abstract base class for all conversation modes"""

    def __init__(self, config: ModeConfig):
        self.config = config
        self.name = config.name
        self.description = config.description
        self.capabilities = config.capabilities

    @abstractmethod
    def process_response(self, response: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process and enhance the AI model response based on mode characteristics

        Args:
            response: Raw response from the AI model
            context: Additional context about the conversation

        Returns:
            str: Processed response with mode-specific enhancements
        """
        pass

    @abstractmethod
    def get_system_prompt(self, user_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate system prompt for this mode

        Args:
            user_context: Context about the user or conversation

        Returns:
            str: System prompt specific to this mode
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Get mode metadata and configuration"""
        return {
            "name": self.name,
            "description": self.description,
            "capabilities": self.capabilities,
            "recommended_models": self.config.recommended_models,
            "temperature_range": self.config.temperature_range,
            "max_tokens_suggestion": self.config.max_tokens_suggestion
        }

    def validate_response(self, response: str) -> bool:
        """
        Validate if the response meets mode requirements

        Args:
            response: The generated response

        Returns:
            bool: True if response is appropriate for this mode
        """
        # Base validation - can be overridden by specific modes
        if not response or not response.strip():
            return False

        if len(response.strip()) < 10:
            return False

        return True

    def enhance_prompt(self, user_prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Enhance user prompt with mode-specific modifications

        Args:
            user_prompt: Original user prompt
            context: Additional context

        Returns:
            str: Enhanced prompt
        """
        # Default implementation returns original prompt
        # Can be overridden by specific modes
        return user_prompt