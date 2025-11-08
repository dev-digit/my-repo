"""
Creative mode for imaginative and engaging conversations
"""

from typing import Dict, Any, Optional
import re

from .base_mode import BaseMode, ModeConfig
from app.utils.logging import setup_logging

logger = setup_logging(__name__)


class CreativeMode(BaseMode):
    """Creative mode - focuses on imagination, storytelling, and idea generation"""

    def __init__(self):
        config = ModeConfig(
            name="creative",
            description="Generates creative content with imagination and engaging language",
            capabilities=["writing", "storytelling", "idea_generation", "brainstorming", "creative_thinking"],
            recommended_models=["gpt-4", "llama2", "mistral"],
            temperature_range=(0.7, 1.0),
            max_tokens_suggestion=2500
        )
        super().__init__(config)

    def get_system_prompt(self, user_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate system prompt for creative mode"""
        base_prompt = (
            "You are Pombi in CREATIVE mode. Your purpose is to be imaginative, engaging, and creative. "
            "Use descriptive language, storytelling techniques, and explore multiple perspectives. "
            "Don't be afraid to be expressive, use metaphors, and paint vivid pictures with your words. "
            "Generate novel ideas, scenarios, and creative solutions. Think outside the box and encourage creativity."
        )

        # Add context-specific enhancements
        if user_context:
            if user_context.get("topic") == "writing":
                base_prompt += " Focus on narrative techniques, character development, and engaging prose."
            elif user_context.get("topic") == "brainstorming":
                base_prompt += " Generate diverse ideas, encourage wild thinking, and build on concepts."
            elif user_context.get("topic") == "art":
                base_prompt += " Use visual language, describe aesthetics, and explore artistic concepts."

        return base_prompt

    def process_response(self, response: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process and enhance creative responses"""
        if not response:
            return "I'd love to help you create something amazing! What would you like to explore creatively?"

        processed = response.strip()

        # Enhance creativity if response is too dry
        if self._is_too_formal(processed):
            processed = self._add_creative_flair(processed)

        # Add creative sign-offs for certain contexts
        if context and context.get("add_signoff", False):
            processed = self._add_creative_signoff(processed)

        return processed

    def enhance_prompt(self, user_prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Enhance user prompt for creative mode"""
        enhanced = user_prompt

        # Add creative encouragement if not present
        creative_keywords = ["create", "imagine", "design", "write", "story", "poem", "art"]
        if not any(keyword in user_prompt.lower() for keyword in creative_keywords):
            enhanced = f"Let's explore this creatively: {user_prompt}"

        # Add sensory details prompt for descriptive tasks
        if any(word in user_prompt.lower() for word in ["describe", "scene", "setting", "character"]):
            enhanced += "\n\nPlease include vivid sensory details - what do we see, hear, smell, feel, or taste?"

        return enhanced

    def validate_response(self, response: str) -> bool:
        """Validate creative response quality"""
        if not super().validate_response(response):
            return False

        # Check for minimum creative elements
        response_lower = response.lower()

        # Avoid very short, uncreative responses
        if len(response.strip()) < 50:
            return False

        # Look for creative indicators
        creative_indicators = [
            "imagine", "picture this", "envision", "what if", "perhaps", "maybe",
            "could be", "might", "story", "tale", "adventure", "journey"
        ]

        return any(indicator in response_lower for indicator in creative_indicators) or len(response) > 200

    def _is_too_formal(self, text: str) -> bool:
        """Check if text is too formal for creative mode"""
        formal_indicators = ["therefore", "consequently", "furthermore", "moreover", "in conclusion"]
        return sum(1 for indicator in formal_indicators if indicator in text.lower()) >= 2

    def _add_creative_flair(self, text: str) -> str:
        """Add creative elements to formal text"""
        # Replace formal transitions with creative ones
        replacements = {
            "therefore": "imagine then",
            "consequently": "and so it unfolds",
            "furthermore": "adding to our canvas",
            "moreover": "let's paint more of this picture",
            "in conclusion": "as our creative journey comes to a close"
        }

        for formal, creative in replacements.items():
            text = re.sub(rf'\b{formal}\b', creative, text, flags=re.IGNORECASE)

        return text

    def _add_creative_signoff(self, text: str) -> str:
        """Add creative sign-off to response"""
        signoffs = [
            "\n\nKeep creating and exploring!",
            "\n\nLet your imagination soar!",
            "\n\nThe canvas of possibility awaits!",
            "\n\nWhat wonders will you create next?",
            "\n\nDream, design, and bring it to life!"
        ]

        import random
        return text + random.choice(signoffs)