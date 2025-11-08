"""
Local model integration via Ollama for Pombi AI Assistant
"""

import time
import asyncio
from typing import Dict, List, Optional, Any
import aiohttp

from .base import BaseModel, ModelConfig, ModelResponse, ModelError
from app.config import settings
from app.utils.logging import setup_logging

logger = setup_logging(__name__)


class LocalModel(BaseModel):
    """Local model implementation via Ollama"""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.base_url = settings.ollama_base_url
        self.model_name = config.name or "llama2"
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def generate_response(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        mode: str = "precise",
        **kwargs
    ) -> ModelResponse:
        """Generate response using local Ollama model"""
        start_time = time.time()

        try:
            session = await self._get_session()

            # Prepare the prompt with system instructions
            full_prompt = self._prepare_full_prompt(prompt, conversation_history, mode)

            # Make API call to Ollama
            data = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": self._get_temperature_for_mode(mode),
                    "top_p": self.config.top_p,
                    "num_predict": self.config.max_tokens,
                }
            }

            async with session.post(f"{self.base_url}/api/generate", json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ModelError(
                        f"Ollama API error: {response.status} - {error_text}",
                        error_code="OLLAMA_ERROR",
                        status_code=response.status
                    )

                result = await response.json()

            # Calculate response time
            response_time = (time.time() - start_time) * 1000

            # Extract response data
            content = result.get("response", "")
            tokens_used = self._estimate_token_count(content + full_prompt)

            # Create response object
            model_response = ModelResponse(
                content=content,
                model_used=self.model_name,
                tokens_used=tokens_used,
                response_time_ms=response_time,
                metadata={
                    "done": result.get("done", False),
                    "total_duration": result.get("total_duration", 0),
                    "load_duration": result.get("load_duration", 0),
                    "prompt_eval_count": result.get("prompt_eval_count", 0),
                    "eval_count": result.get("eval_count", 0),
                }
            )

            logger.info(
                "Local model response generated",
                extra={
                    "model": self.model_name,
                    "tokens_used": tokens_used,
                    "response_time_ms": response_time,
                    "mode": mode
                }
            )

            return model_response

        except asyncio.TimeoutError:
            logger.error("Local model timeout")
            raise ModelError(
                "Request to local model timed out.",
                error_code="TIMEOUT",
                status_code=504
            )

        except aiohttp.ClientConnectorError:
            logger.error("Cannot connect to Ollama service")
            raise ModelError(
                "Cannot connect to local Ollama service. Ensure it's running.",
                error_code="CONNECTION_ERROR",
                status_code=503
            )

        except Exception as e:
            logger.error("Unexpected error in local model", extra={"error": str(e)}, exc_info=True)
            raise ModelError(
                "Unexpected error occurred while generating response.",
                error_code="UNKNOWN_ERROR",
                status_code=500
            )

    async def health_check(self) -> bool:
        """Check if local model is available"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    models = await response.json()
                    model_names = [model["name"] for model in models.get("models", [])]
                    return self.model_name in model_names
                return False
        except Exception as e:
            logger.error("Local model health check failed", extra={"error": str(e)})
            return False

    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    def get_capabilities(self) -> Dict[str, Any]:
        """Get local model capabilities"""
        return {
            "provider": "local",
            "model": self.model_name,
            "max_tokens": self.config.max_tokens,
            "supports_streaming": False,  # Could be implemented
            "supports_functions": False,
            "supports_vision": False,
            "modes": ["creative", "precise", "teach", "code", "analyze"],
            "estimated_cost_per_1k_tokens": 0.0,  # Local models are "free"
            "requires_gpu": True,
            "memory_usage": "high"
        }

    def _prepare_full_prompt(
        self,
        prompt: str,
        conversation_history: Optional[List[Dict[str, str]]],
        mode: str
    ) -> str:
        """Prepare full prompt for local model"""
        system_prompt = self._prepare_system_prompt(mode)

        # Build conversation context
        context_parts = [f"System: {system_prompt}"]

        if conversation_history:
            for turn in conversation_history[-5:]:  # Limit to last 5 turns
                role = turn.get("role", "unknown")
                content = turn.get("content", "")
                if role == "user":
                    context_parts.append(f"User: {content}")
                elif role == "assistant":
                    context_parts.append(f"Assistant: {content}")

        context_parts.append(f"User: {prompt}")
        context_parts.append("Assistant: ")

        return "\n\n".join(context_parts)

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

    def _estimate_token_count(self, text: str) -> int:
        """Rough token estimation (4 chars per token on average)"""
        return len(text) // 4