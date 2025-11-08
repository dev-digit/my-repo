"""
Precise mode for factual accuracy and concise answers
"""

from typing import Dict, Any, Optional
import re

from .base_mode import BaseMode, ModeConfig
from app.utils.logging import setup_logging

logger = setup_logging(__name__)


class PreciseMode(BaseMode):
    """Precise mode - prioritizes factual accuracy and concise answers"""

    def __init__(self):
        config = ModeConfig(
            name="precise",
            description="Provides factual, accurate, and concise answers",
            capabilities=["factual_answers", "data_analysis", "accurate_information", "clear_explanations"],
            recommended_models=["gpt-4", "gpt-3.5", "mistral"],
            temperature_range=(0.1, 0.4),
            max_tokens_suggestion=1500
        )
        super().__init__(config)

    def get_system_prompt(self, user_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate system prompt for precise mode"""
        base_prompt = (
            "You are Pombi in PRECISE mode. Your purpose is to provide accurate, factual, and concise answers. "
            "Prioritize correctness over creativity. Be direct, clear, and specific. "
            "Avoid speculation, opinion, or creative language unless explicitly asked. "
            "Focus on verified information and logical reasoning. If you're uncertain about something, acknowledge it. "
            "Structure your responses clearly with the most important information first."
        )

        # Add context-specific enhancements
        if user_context:
            if user_context.get("topic") == "science":
                base_prompt += " Emphasize scientific accuracy, cite established research, and distinguish between theory and fact."
            elif user_context.get("topic") == "history":
                base_prompt += " Focus on verified historical facts, provide context, and acknowledge historical debates."
            elif user_context.get("topic") == "technical":
                base_prompt += " Provide specific technical details, exact terminology, and practical information."

        return base_prompt

    def process_response(self, response: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process and enhance precise responses"""
        if not response:
            return "I need more specific information to provide an accurate answer."

        processed = response.strip()

        # Remove excessive hedging in precise mode
        processed = self._reduce_uncertainty_phrases(processed)

        # Ensure factual accuracy indicators
        processed = self._add_precision_markers(processed)

        # Structure for clarity
        processed = self._improve_structure(processed)

        return processed

    def enhance_prompt(self, user_prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Enhance user prompt for precise mode"""
        enhanced = user_prompt

        # Add precision focus if not explicit
        precision_keywords = ["exact", "specific", "accurate", "precise", "factual"]
        if not any(keyword in user_prompt.lower() for keyword in precision_keywords):
            enhanced = f"Please provide a precise and accurate answer to: {user_prompt}"

        # Add request for sources if dealing with factual claims
        if any(word in user_prompt.lower() for word in ["what", "who", "when", "where", "why", "how"]):
            enhanced += "\n\nPlease provide specific details and indicate the level of certainty."

        return enhanced

    def validate_response(self, response: str) -> bool:
        """Validate precise response quality"""
        if not super().validate_response(response):
            return False

        # Check for precision indicators
        response_lower = response.lower()

        # Avoid overly speculative language in precise mode
        speculative_phrases = ["might be", "could be", "perhaps", "maybe", "i think"]
        speculation_count = sum(1 for phrase in speculative_phrases if phrase in response_lower)

        # Too much speculation makes it less precise
        if speculation_count > 3:
            return False

        # Look for precision indicators
        precision_indicators = [
            "specifically", "exactly", "precisely", "according to", "data shows",
            "research indicates", "typically", "generally", "approximately"
        ]

        return any(indicator in response_lower for indicator in precision_indicators) or len(response.split()) > 20

    def _reduce_uncertainty_phrases(self, text: str) -> str:
        """Reduce excessive uncertainty phrases while maintaining accuracy"""
        # Replace weaker uncertainty with stronger, more precise language
        replacements = {
            "I think that": "Based on available information",
            "It might be": "It appears to be",
            "It could be": "Evidence suggests",
            "Maybe": "Potentially",
            "Perhaps": "Possibly"
        }

        for uncertain, precise in replacements.items():
            text = re.sub(rf'\b{uncertain}\b', precise, text, flags=re.IGNORECASE)

        return text

    def _add_precision_markers(self, text: str) -> str:
        """Add markers that indicate precision"""
        # If text contains numbers or specific data, highlight precision
        if re.search(r'\b\d+(?:\.\d+)?\b', text):
            # Add precision context if not present
            if not any(indicator in text.lower() for indicator in ["exactly", "approximately", "specifically"]):
                # Insert precision marker at the beginning
                sentences = text.split('. ')
                if sentences:
                    sentences[0] = "Specifically, " + sentences[0]
                    text = '. '.join(sentences)

        return text

    def _improve_structure(self, text: str) -> str:
        """Improve response structure for clarity"""
        # Break up long paragraphs
        sentences = text.split('. ')
        structured_sentences = []

        for sentence in sentences:
            if len(sentence) > 200:  # Long sentence
                # Try to break it down
                if ", " in sentence:
                    parts = sentence.split(", ")
                    for i, part in enumerate(parts):
                        if i > 0:
                            part = part.capitalize()
                        structured_sentences.append(part.strip())
                else:
                    structured_sentences.append(sentence.strip())
            else:
                if sentence.strip():
                    structured_sentences.append(sentence.strip())

        return '. '.join(structured_sentences)