"""
Core AI engine orchestration for Pombi AI Assistant
"""

import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from app.config import settings
from app.models.model_router import ModelRouter
from app.models.base import ModelResponse, ModelError
from app.modes import (
    BaseMode, CreativeMode, PreciseMode, TeachMode, CodeMode, AnalyzeMode
)
from app.memory.conversation_memory import ConversationMemory, ConversationTurn
from app.memory.context_manager import ContextManager
from app.safety.content_filter import ContentFilter, FilterResult
from app.safety.rate_limiter import RateLimiter
from app.safety.privacy_guard import PrivacyGuard
from app.utils.logging import setup_logging

logger = setup_logging(__name__)


class AIEngine:
    """Main AI orchestration component"""

    def __init__(self):
        self.model_router = ModelRouter()
        self.conversation_memory = ConversationMemory()
        self.context_manager = ContextManager()
        self.content_filter = ContentFilter()
        self.rate_limiter = RateLimiter()
        self.privacy_guard = PrivacyGuard()

        # Initialize modes
        self.modes = {
            "creative": CreativeMode(),
            "precise": PreciseMode(),
            "teach": TeachMode(),
            "code": CodeMode(),
            "analyze": AnalyzeMode()
        }

        logger.info("AI Engine initialized with all components")

    async def process_message(
        self,
        message: str,
        mode: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        model_preference: str = "auto",
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and generate response

        Args:
            message: User's message
            mode: Conversation mode
            conversation_id: Existing conversation ID (optional)
            context: Additional context for the conversation
            model_preference: Model preference ("openai", "local", "auto")
            user_id: User identifier for rate limiting

        Returns:
            Dict containing the response and metadata
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())

        try:
            # Validate inputs
            if mode not in self.modes:
                raise ValueError(f"Invalid mode: {mode}. Available modes: {list(self.modes.keys())}")

            # Rate limiting check
            if user_id:
                is_allowed, rate_info = await self.rate_limiter.is_allowed(user_id)
                if not is_allowed:
                    raise ModelError(
                        "Rate limit exceeded. Please try again later.",
                        error_code="RATE_LIMIT",
                        status_code=429
                    )

            # Privacy and content filtering
            sanitized_message, privacy_info = self.privacy_guard.sanitize_input(message, user_id)
            filter_result, filter_categories = self.content_filter.filter_content(sanitized_message, user_id)

            if filter_result == FilterResult.BLOCK:
                return self._create_blocked_response(filter_result, filter_categories, request_id)

            # Get or create conversation
            if conversation_id:
                try:
                    conversation = self.conversation_memory.get_conversation(conversation_id)
                except ValueError:
                    conversation_id = self.conversation_memory.create_conversation()
                    conversation = []
            else:
                conversation_id = self.conversation_memory.create_conversation()
                conversation = []

            # Get mode instance
            mode_instance = self.modes[mode]

            # Enhance prompt based on mode
            enhanced_prompt = mode_instance.enhance_prompt(sanitized_message, context)

            # Prepare context for model
            conversation_history = self.conversation_memory.get_conversation_for_model(conversation_id)
            system_prompt = mode_instance.get_system_prompt(context)

            # Get appropriate model
            model = await self.model_router.get_model(
                preference=model_preference,
                mode=mode,
                conversation_history=conversation_history
            )

            # Generate response
            model_response = await model.generate_response(
                prompt=enhanced_prompt,
                conversation_history=conversation_history,
                mode=mode
            )

            # Process response through mode
            processed_response = mode_instance.process_response(
                model_response.content,
                {"context": context, "privacy_info": privacy_info}
            )

            # Apply content filtering to response
            final_response = self.content_filter.filter_response(processed_response)

            # Apply privacy filtering to response
            final_response = self.privacy_guard.sanitize_response(final_response)

            # Add user turn to memory
            self.conversation_memory.add_turn(
                conversation_id=conversation_id,
                role="user",
                content=sanitized_message,
                mode=mode,
                metadata={
                    "original_length": len(message),
                    "sanitized_length": len(sanitized_message),
                    "privacy_detected": bool(privacy_info),
                    "content_filtered": filter_result != FilterResult.ALLOW
                }
            )

            # Add assistant turn to memory
            self.conversation_memory.add_turn(
                conversation_id=conversation_id,
                role="assistant",
                content=final_response,
                mode=mode,
                tokens_used=model_response.tokens_used,
                model_used=model_response.model_used,
                metadata={
                    "processing_time_ms": model_response.response_time_ms,
                    "confidence_score": model_response.confidence_score
                }
            )

            # Calculate total processing time
            total_time = (time.time() - start_time) * 1000

            # Create response
            response_data = {
                "response": final_response,
                "conversation_id": conversation_id,
                "mode_used": mode,
                "model_used": model_response.model_used,
                "request_id": request_id,
                "metadata": {
                    "response_time_ms": round(total_time, 2),
                    "model_response_time_ms": round(model_response.response_time_ms, 2),
                    "tokens_used": model_response.tokens_used,
                    "confidence_score": model_response.confidence_score,
                    "rate_limit_info": rate_info if user_id else None,
                    "privacy_warnings": bool(privacy_info),
                    "content_filter_result": filter_result.value if filter_result != FilterResult.ALLOW else None,
                    "conversation_turn": len(conversation) + 1
                }
            }

            logger.info(
                "Message processed successfully",
                extra={
                    "request_id": request_id,
                    "conversation_id": conversation_id,
                    "mode": mode,
                    "model": model_response.model_used,
                    "response_time_ms": total_time,
                    "tokens_used": model_response.tokens_used,
                    "user_id": user_id
                }
            )

            return response_data

        except ModelError as e:
            logger.error(
                "Model error during processing",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "error_code": e.error_code,
                    "user_id": user_id
                }
            )
            return self._create_error_response(e, request_id)

        except Exception as e:
            logger.error(
                "Unexpected error during processing",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "type": type(e).__name__,
                    "user_id": user_id
                },
                exc_info=True
            )
            return self._create_error_response(
                ModelError("An unexpected error occurred", error_code="UNKNOWN_ERROR"),
                request_id
            )

    async def get_mode_info(self) -> List[Dict[str, Any]]:
        """Get information about available modes"""
        return [mode.get_metadata() for mode in self.modes.values()]

    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        return await self.model_router.get_available_models()

    async def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history"""
        try:
            conversation = self.conversation_memory.get_conversation(conversation_id)
            return [
                {
                    "role": turn.role,
                    "content": turn.content,
                    "mode": turn.mode,
                    "timestamp": turn.timestamp.isoformat(),
                    "tokens_used": turn.tokens_used,
                    "model_used": turn.model_used
                }
                for turn in conversation
            ]
        except ValueError:
            return []

    async def get_conversation_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation summary"""
        try:
            return self.conversation_memory.get_conversation_summary(conversation_id)
        except ValueError:
            return None

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        # Check model health
        model_health = await self.model_router.health_check_all()

        # Check system health
        conversation_count = len(self.conversation_memory.conversations)
        memory_stats = self.conversation_memory.get_session_stats()

        return {
            "status": "healthy" if any(model_health.values()) else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "models": model_health,
            "conversations": {
                "active_count": conversation_count,
                "memory_stats": memory_stats
            },
            "safety": {
                "content_filter_enabled": self.content_filter.enabled,
                "rate_limiter_active": len(self.rate_limiter.blocked_users),
                "privacy_guard_enabled": self.privacy_guard.enabled
            },
            "modes": list(self.modes.keys())
        }

    def _create_blocked_response(
        self,
        filter_result: FilterResult,
        categories: List,
        request_id: str
    ) -> Dict[str, Any]:
        """Create response for blocked content"""
        safety_message = self.content_filter.get_safety_message(filter_result, categories)

        return {
            "response": safety_message,
            "conversation_id": None,
            "mode_used": "none",
            "model_used": "none",
            "request_id": request_id,
            "metadata": {
                "content_filter_result": filter_result.value,
                "blocked_categories": [cat.value for cat in categories],
                "response_time_ms": 0,
                "tokens_used": 0,
                "confidence_score": 0.0
            }
        }

    def _create_error_response(self, error: ModelError, request_id: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "response": f"Sorry, I encountered an error: {error}",
            "conversation_id": None,
            "mode_used": "none",
            "model_used": "none",
            "request_id": request_id,
            "metadata": {
                "error_code": error.error_code,
                "error_status": error.status_code,
                "response_time_ms": 0,
                "tokens_used": 0,
                "confidence_score": 0.0
            }
        }

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        return self.conversation_memory.cleanup_expired_sessions()

    async def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        return {
            "conversations": self.conversation_memory.get_session_stats(),
            "models": await self.model_router.get_available_models(),
            "rate_limiting": self.rate_limiter.get_global_stats(),
            "safety": {
                "content_filter": {"enabled": self.content_filter.enabled},
                "privacy_guard": self.privacy_guard.get_privacy_stats()
            },
            "modes": [mode.get_metadata() for mode in self.modes.values()]
        }

    async def close(self):
        """Cleanup AI engine resources"""
        await self.rate_limiter.close()
        logger.info("AI Engine shutdown complete")