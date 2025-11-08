"""
OpenAI model integration for Pombi AI Assistant
"""

import time
import asyncio
from typing import Dict, List, Optional, Any
import openai
from openai import AsyncOpenAI

from .base import BaseModel, ModelConfig, ModelResponse, ModelError
from app.config import settings
from app.utils.logging import setup_logging

logger = setup_logging(__name__)


class OpenAIModel(BaseModel):
    """OpenAI model implementation"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model_name = "gpt-3.5-turbo"  # Default model

        # Map model names to OpenAI model IDs
        self.model_mapping = {
            "gpt-3.5": "gpt-3.5-turbo",
            "gpt-4": "gpt-4",
            "gpt-4-turbo": "gpt-4-1106-preview",
        }

        if config.name in self.model_mapping:
            self.model_name = self.model_mapping[config.name]

    async def generate_response(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        mode: str = "precise",
        **kwargs
    ) -> ModelResponse:
        """Generate response using OpenAI API"""
        start_time = time.time()

        try:
            # Prepare messages
            messages = self._prepare_messages(prompt, conversation_history, mode)

            # Make API call
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=self.config.max_tokens,
                temperature=self._get_temperature_for_mode(mode),
                top_p=self.config.top_p,
                frequency_penalty=self.config.frequency_penalty,
                presence_penalty=self.config.presence_penalty,
                timeout=self.config.timeout
            )

            # Calculate response time
            response_time = (time.time() - start_time) * 1000

            # Extract response data
            content = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else 0

            # Create response object
            model_response = ModelResponse(
                content=content,
                model_used=self.model_name,
                tokens_used=tokens_used,
                response_time_ms=response_time,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                }
            )

            logger.info(
                "OpenAI response generated",
                extra={
                    "model": self.model_name,
                    "tokens_used": tokens_used,
                    "response_time_ms": response_time,
                    "mode": mode
                }
            )

            return model_response

        except openai.RateLimitError as e:
            logger.error("OpenAI rate limit exceeded", extra={"error": str(e)})
            raise ModelError(
                "OpenAI rate limit exceeded. Please try again later.",
                error_code="RATE_LIMIT",
                status_code=429
            )

        except openai.AuthenticationError as e:
            logger.error("OpenAI authentication failed", extra={"error": str(e)})
            raise ModelError(
                "OpenAI authentication failed. Check API key.",
                error_code="AUTH_ERROR",
                status_code=401
            )

        except openai.APIError as e:
            logger.error("OpenAI API error", extra={"error": str(e)})
            raise ModelError(
                "OpenAI API error occurred.",
                error_code="API_ERROR",
                status_code=502
            )

        except asyncio.TimeoutError:
            logger.error("OpenAI API timeout")
            raise ModelError(
                "Request to OpenAI timed out.",
                error_code="TIMEOUT",
                status_code=504
            )

        except Exception as e:
            logger.error("Unexpected error in OpenAI model", extra={"error": str(e)}, exc_info=True)
            raise ModelError(
                "Unexpected error occurred while generating response.",
                error_code="UNKNOWN_ERROR",
                status_code=500
            )

    async def health_check(self) -> bool:
        """Check if OpenAI service is available"""
        try:
            # Simple test call
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception as e:
            logger.error("OpenAI health check failed", extra={"error": str(e)})
            return False

    def get_capabilities(self) -> Dict[str, Any]:
        """Get OpenAI model capabilities"""
        return {
            "provider": "openai",
            "model": self.model_name,
            "max_tokens": self.config.max_tokens,
            "supports_streaming": True,
            "supports_functions": True,
            "supports_vision": "gpt-4-vision-preview" in self.model_name,
            "modes": ["creative", "precise", "teach", "code", "analyze"],
            "estimated_cost_per_1k_tokens": self._get_cost_per_1k_tokens()
        }

    def _prepare_messages(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]],
        mode: str
    ) -> List[Dict[str, str]]:
        """Prepare messages for OpenAI API"""
        messages = []

        # Add system prompt
        messages.append({
            "role": "system",
            "content": self._prepare_system_prompt(mode)
        })

        # Add conversation history
        if conversation_history:
            formatted_history = self._format_conversation_history(conversation_history)
            messages.extend(formatted_history)

        # Add current user message
        messages.append({
            "role": "user",
            "content": prompt
        })

        return messages

    def _get_temperature_for_mode(self, mode: str) -> float:
        """Get appropriate temperature setting for mode"""
        temperature_map = {
            "creative": 0.9,
            "precise": 0.3,
            "teach": 0.6,
            "code": 0.2,
            "analyze": 0.4
        }
        return temperature_map.get(mode, self.config.temperature)

    def _get_cost_per_1k_tokens(self) -> float:
        """Get estimated cost per 1k tokens for the model"""
        cost_map = {
            "gpt-3.5-turbo": 0.002,
            "gpt-4": 0.03,
            "gpt-4-1106-preview": 0.01,
        }
        return cost_map.get(self.model_name, 0.01)