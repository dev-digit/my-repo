"""
Teach mode for educational and instructional conversations
"""

from typing import Dict, Any, Optional
import re

from .base_mode import BaseMode, ModeConfig
from app.utils.logging import setup_logging

logger = setup_logging(__name__)


class TeachMode(BaseMode):
    """Teach mode - focuses on education, explanation, and learning"""

    def __init__(self):
        config = ModeConfig(
            name="teach",
            description="Educational mode that explains concepts step-by-step with examples",
            capabilities=["teaching", "explanation", "step_by_step", "analogy", "learning_support"],
            recommended_models=["gpt-4", "mistral", "gpt-3.5"],
            temperature_range=(0.4, 0.7),
            max_tokens_suggestion=2000
        )
        super().__init__(config)

    def get_system_prompt(self, user_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate system prompt for teach mode"""
        base_prompt = (
            "You are Pombi in TEACH mode. Your purpose is to educate and explain concepts clearly and effectively. "
            "Break down complex topics into simple, understandable steps. Use real-world examples and analogies. "
            "Ask follow-up questions to ensure understanding. Be patient, encouraging, and adapt your explanations "
            "to the learner's level. Offer progressive difficulty and check for comprehension. "
            "Focus on building intuition and deep understanding, not just memorization."
        )

        # Add context-specific enhancements
        if user_context:
            level = user_context.get("level", "beginner")
            if level == "beginner":
                base_prompt += " Use simple language, avoid jargon, and explain every technical term."
            elif level == "intermediate":
                base_prompt += " Assume some background knowledge but still explain key concepts thoroughly."
            elif level == "advanced":
                base_prompt += " Dive deep into nuances, advanced concepts, and practical applications."

            topic = user_context.get("topic")
            if topic == "math":
                base_prompt += " Show step-by-step calculations, explain the reasoning, and provide multiple solution methods."
            elif topic == "science":
                base_prompt += " Explain underlying principles, use experiments as examples, and connect to real-world phenomena."
            elif topic == "programming":
                base_prompt += " Show code examples, explain each line, discuss best practices, and suggest exercises."

        return base_prompt

    def process_response(self, response: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process and enhance educational responses"""
        if not response:
            return "I'd be happy to help you learn! What topic would you like to explore?"

        processed = response.strip()

        # Ensure educational structure
        processed = self._add_educational_structure(processed)

        # Add learning checks
        processed = self._add_comprehension_checks(processed, context)

        # Include practice suggestions
        processed = self._add_practice_suggestions(processed, context)

        return processed

    def enhance_prompt(self, user_prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Enhance user prompt for teach mode"""
        enhanced = user_prompt

        # Add educational framing if not present
        teach_keywords = ["explain", "teach", "learn", "understand", "how does", "what is"]
        if not any(keyword in user_prompt.lower() for keyword in teach_keywords):
            enhanced = f"Please teach me about: {user_prompt}"

        # Add level-specific guidance
        if context:
            level = context.get("level", "beginner")
            enhanced += f"\n\nPlease explain this for a {level} level."

        # Add request for examples if not present
        if "example" not in user_prompt.lower():
            enhanced += "\n\nPlease include examples to help me understand better."

        return enhanced

    def validate_response(self, response: str) -> bool:
        """Validate educational response quality"""
        if not super().validate_response(response):
            return False

        # Check for educational elements
        response_lower = response.lower()

        # Look for teaching indicators
        teaching_indicators = [
            "step", "first", "second", "third", "example", "imagine", "think of",
            "analogy", "metaphor", "in other words", "to put it simply",
            "for instance", "such as", "like", "similar to"
        ]

        educational_score = sum(1 for indicator in teaching_indicators if indicator in response_lower)

        # Should have multiple educational elements
        return educational_score >= 2 or len(response) > 300

    def _add_educational_structure(self, text: str) -> str:
        """Add proper educational structure to response"""
        # If response doesn't have clear structure, add it
        has_structure = any(
            indicator in text.lower()
            for indicator in ["step", "first", "second", "1.", "2.", "•", "-"]
        )

        if not has_structure and len(text) > 200:
            # Try to identify logical breaks and add structure
            sentences = text.split('. ')
            if len(sentences) >= 3:
                # Add introductory phrase
                text = "Let me break this down for you step by step:\n\n" + text

        return text

    def _add_comprehension_checks(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Add comprehension checks to encourage learning"""
        # Avoid adding too many questions
        question_count = text.count('?')
        has_question = question_count > 0

        # Add follow-up question if not present and response is substantial
        if not has_question and len(text) > 200:
            questions = [
                "\n\nDoes this make sense so far?",
                "\n\nWhat part would you like me to explain further?",
                "\n\nCan you think of a real-world example of this?",
                "\n\nWould you like me to go into more detail on any aspect?"
            ]

            import random
            text += random.choice(questions)

        return text

    def _add_practice_suggestions(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Add practice suggestions when appropriate"""
        # Add practice suggestion for technical topics
        technical_keywords = ["code", "math", "formula", "algorithm", "function", "equation"]
        if any(keyword in text.lower() for keyword in technical_keywords):
            if "practice" not in text.lower() and "try" not in text.lower():
                text += "\n\nThe best way to solidify your understanding is to practice this concept. Try working through a few examples on your own!"

        return text