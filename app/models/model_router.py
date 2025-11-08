"""
Model router for smart model selection and load balancing
"""

import random
from typing import Dict, List, Optional, Any
from enum import Enum

from .base import BaseModel, ModelConfig, ModelError
from .openai_model import OpenAIModel
from .local_model import LocalModel
from app.config import settings
from app.utils.logging import setup_logging

logger = setup_logging(__name__)


class ModelType(Enum):
    """Available model types"""
    OPENAI = "openai"
    LOCAL = "local"


class ModelRouter:
    """Smart model routing and selection"""

    def __init__(self):
        self.models: Dict[str, BaseModel] = {}
        self._initialize_models()

    def _initialize_models(self):
        """Initialize available models"""
        # Initialize OpenAI models
        if settings.openai_api_key:
            try:
                # GPT-3.5 Turbo
                gpt35_config = ModelConfig(
                    name="gpt-3.5",
                    provider="openai",
                    max_tokens=2000,
                    temperature=0.7
                )
                self.models["gpt-3.5"] = OpenAIModel(gpt35_config)

                # GPT-4
                gpt4_config = ModelConfig(
                    name="gpt-4",
                    provider="openai",
                    max_tokens=2000,
                    temperature=0.7
                )
                self.models["gpt-4"] = OpenAIModel(gpt4_config)

                logger.info("OpenAI models initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize OpenAI models", extra={"error": str(e)})

        # Initialize local models
        if settings.enable_local_models:
            try:
                # Llama 2
                llama_config = ModelConfig(
                    name="llama2",
                    provider="local",
                    max_tokens=1500,
                    temperature=0.7
                )
                self.models["llama2"] = LocalModel(llama_config)

                # Mistral
                mistral_config = ModelConfig(
                    name="mistral",
                    provider="local",
                    max_tokens=1500,
                    temperature=0.7
                )
                self.models["mistral"] = LocalModel(mistral_config)

                logger.info("Local models initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize local models", extra={"error": str(e)})

    async def get_model(
        self,
        preference: str = "auto",
        mode: str = "precise",
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> BaseModel:
        """
        Get the best available model based on preference and context

        Args:
            preference: User preference ("openai", "local", "auto")
            mode: Conversation mode
            conversation_history: Previous conversation turns

        Returns:
            BaseModel: Selected model instance
        """
        # Determine available healthy models
        healthy_models = await self._get_healthy_models()

        if not healthy_models:
            raise ModelError(
                "No healthy models available",
                error_code="NO_MODELS",
                status_code=503
            )

        # Select model based on preference
        if preference == "openai":
            return self._select_openai_model(healthy_models, mode)
        elif preference == "local":
            return self._select_local_model(healthy_models, mode)
        else:  # auto
            return self._select_best_model(healthy_models, mode, conversation_history)

    async def _get_healthy_models(self) -> List[BaseModel]:
        """Get list of healthy models"""
        healthy = []
        for name, model in self.models.items():
            try:
                if await model.health_check():
                    healthy.append(model)
            except Exception as e:
                logger.warning(f"Health check failed for model {name}", extra={"error": str(e)})

        return healthy

    def _select_openai_model(self, models: List[BaseModel], mode: str) -> BaseModel:
        """Select best OpenAI model for the mode"""
        openai_models = [m for m in models if m.provider == "openai"]

        if not openai_models:
            # Fallback to any available model
            logger.warning("No OpenAI models available, falling back to other models")
            return random.choice(models)

        # Prefer GPT-4 for creative and code modes
        if mode in ["creative", "code"] and any(m.name == "gpt-4" for m in openai_models):
            return next(m for m in openai_models if m.name == "gpt-4")

        # Default to GPT-3.5 for other modes
        if any(m.name == "gpt-3.5" for m in openai_models):
            return next(m for m in openai_models if m.name == "gpt-3.5")

        return openai_models[0]

    def _select_local_model(self, models: List[BaseModel], mode: str) -> BaseModel:
        """Select best local model for the mode"""
        local_models = [m for m in models if m.provider == "local"]

        if not local_models:
            # Fallback to any available model
            logger.warning("No local models available, falling back to other models")
            return random.choice(models)

        # Prefer Mistral for code mode
        if mode == "code" and any(m.name == "mistral" for m in local_models):
            return next(m for m in local_models if m.name == "mistral")

        # Default to Llama for other modes
        if any(m.name == "llama2" for m in local_models):
            return next(m for m in local_models if m.name == "llama2")

        return local_models[0]

    def _select_best_model(
        self,
        models: List[BaseModel],
        mode: str,
        conversation_history: Optional[List[Dict[str, str]]]
    ) -> BaseModel:
        """
        Select the best model automatically based on context and mode
        """
        # Prioritize OpenAI models for complex tasks
        if mode in ["creative", "code"]:
            openai_models = [m for m in models if m.provider == "openai"]
            if openai_models:
                return self._select_openai_model(openai_models, mode)

        # Use local models for simpler tasks or when cost is a concern
        local_models = [m for m in models if m.provider == "local"]
        if local_models and mode in ["precise", "teach", "analyze"]:
            return self._select_local_model(local_models, mode)

        # Default: choose the most capable available model
        if any(m.name == "gpt-4" for m in models):
            return next(m for m in models if m.name == "gpt-4")
        elif any(m.name == "mistral" for m in models):
            return next(m for m in models if m.name == "mistral")
        elif any(m.name == "gpt-3.5" for m in models):
            return next(m for m in models if m.name == "gpt-3.5")
        elif any(m.name == "llama2" for m in models):
            return next(m for m in models if m.name == "llama2")
        else:
            return models[0]

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models with their capabilities"""
        available = []
        healthy_models = await self._get_healthy_models()

        for model in healthy_models:
            capabilities = model.get_capabilities()
            available.append(capabilities)

        return available

    async def health_check_all(self) -> Dict[str, bool]:
        """Health check all models"""
        results = {}
        for name, model in self.models.items():
            try:
                results[name] = await model.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {name}", extra={"error": str(e)})
                results[name] = False

        return results