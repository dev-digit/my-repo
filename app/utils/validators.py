"""
Input validation utilities for Pombi AI Assistant
"""

import re
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, validator


class ValidationError(Exception):
    """Custom validation error"""
    pass


def validate_message(message: str) -> str:
    """Validate message content"""
    if not isinstance(message, str):
        raise ValidationError("Message must be a string")

    message = message.strip()

    if not message:
        raise ValidationError("Message cannot be empty")

    if len(message) > 4000:
        raise ValidationError("Message cannot exceed 4000 characters")

    return message


def validate_mode(mode: str) -> str:
    """Validate conversation mode"""
    valid_modes = ["creative", "precise", "teach", "code", "analyze"]

    if not isinstance(mode, str):
        raise ValidationError("Mode must be a string")

    mode = mode.lower().strip()

    if mode not in valid_modes:
        raise ValidationError(f"Mode must be one of: {', '.join(valid_modes)}")

    return mode


def validate_conversation_id(conversation_id: Optional[str]) -> Optional[str]:
    """Validate conversation ID format"""
    if conversation_id is None:
        return None

    if not isinstance(conversation_id, str):
        raise ValidationError("Conversation ID must be a string")

    try:
        uuid.UUID(conversation_id)
        return conversation_id
    except ValueError:
        raise ValidationError("Conversation ID must be a valid UUID")


def validate_model_preference(model_preference: str) -> str:
    """Validate model preference"""
    valid_models = ["openai", "local", "auto"]

    if not isinstance(model_preference, str):
        raise ValidationError("Model preference must be a string")

    model_preference = model_preference.lower().strip()

    if model_preference not in valid_models:
        raise ValidationError(f"Model preference must be one of: {', '.join(valid_models)}")

    return model_preference


class ChatRequest(BaseModel):
    """Chat request validation model"""
    message: str
    mode: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    model_preference: str = "auto"

    @validator('message')
    def validate_message_field(cls, v):
        return validate_message(v)

    @validator('mode')
    def validate_mode_field(cls, v):
        return validate_mode(v)

    @validator('conversation_id')
    def validate_conversation_id_field(cls, v):
        return validate_conversation_id(v)

    @validator('model_preference')
    def validate_model_preference_field(cls, v):
        return validate_model_preference(v)

    @validator('context')
    def validate_context_size(cls, v):
        if v and len(str(v)) > 1024:
            raise ValueError("Context cannot exceed 1KB")
        return v