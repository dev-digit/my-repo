"""
Base model interface and data structures for AI models
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime


class ModelConfig(BaseModel):
    """Configuration for AI models"""
    name: str
    provider: str
    max_tokens: int = 2000
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 30


class ModelResponse(BaseModel):
    """Standard response format for all AI models"""
    content: str
    model_used: str
    tokens_used: int = 0
    confidence_score: float = 0.0
    response_time_ms: float = 0.0
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.utcnow()


class ModelError(Exception):
    """Custom exception for model-related errors"""
    def __init__(self, message: str, error_code: str = "MODEL_ERROR", status_code: int = 500):
        super().__init__(message)
        self.error_code = error_code
        self.status_code = status_code


class BaseModel(ABC):
    """Abstract base class for all AI models"""

    def __init__(self, config: ModelConfig):
        self.config = config
        self.name = config.name
        self.provider = config.provider

    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        mode: str = "precise",
        **kwargs
    ) -> ModelResponse:
        """
        Generate a response from the model

        Args:
            prompt: The user's input message
            conversation_history: Previous conversation turns
            mode: The conversation mode (creative, precise, teach, code, analyze)
            **kwargs: Additional model-specific parameters

        Returns:
            ModelResponse: The model's response with metadata
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the model is available and healthy"""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """Get model capabilities and metadata"""
        pass

    def _prepare_system_prompt(self, mode: str) -> str:
        """Generate system prompt based on conversation mode"""
        base_prompt = "You are Pombi, an advanced conversational AI assistant. "

        mode_prompts = {
            "creative": (
                "You are in CREATIVE mode. Focus on imaginative and engaging responses. "
                "Use descriptive language, storytelling techniques, and generate creative ideas. "
                "Be expressive and explore multiple perspectives."
            ),
            "precise": (
                "You are in PRECISE mode. Prioritize factual accuracy and concise answers. "
                "Provide evidence-based information when possible. Avoid speculation. "
                "Be direct, clear, and focus on accuracy over creativity."
            ),
            "teach": (
                "You are in TEACH mode. Break down complex topics into simple, understandable steps. "
                "Use real-world examples and analogies. Ask follow-up questions to ensure understanding. "
                "Offer progressive difficulty and be encouraging."
            ),
            "code": (
                "You are in CODE mode. Provide working code examples with clear explanations. "
                "Explain code logic step-by-step. Include best practices and optimization suggestions. "
                "Use proper syntax highlighting and comments."
            ),
            "analyze": (
                "You are in ANALYZE mode. Summarize and compare information systematically. "
                "Identify patterns, insights, and balanced perspectives. Structure information clearly. "
                "Provide objective analysis with evidence."
            )
        }

        mode_prompt = mode_prompts.get(mode, mode_prompts["precise"])

        return base_prompt + mode_prompt

    def _format_conversation_history(
        self, history: Optional[List[Dict[str, str]]]
    ) -> List[Dict[str, str]]:
        """Format conversation history for the model"""
        if not history:
            return []

        # Ensure proper format and limit history length
        formatted_history = []
        for turn in history[-10:]:  # Limit to last 10 turns
            if isinstance(turn, dict) and "role" in turn and "content" in turn:
                formatted_history.append({
                    "role": turn["role"],
                    "content": turn["content"]
                })

        return formatted_history