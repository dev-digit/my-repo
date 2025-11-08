"""
Analyze mode for analysis, comparison, and critical thinking
"""

from typing import Dict, Any, Optional
import re

from .base_mode import BaseMode, ModeConfig
from app.utils.logging import setup_logging

logger = setup_logging(__name__)


class AnalyzeMode(BaseMode):
    """Analyze mode - focuses on analysis, comparison, and structured thinking"""

    def __init__(self):
        config = ModeConfig(
            name="analyze",
            description="Provides systematic analysis, comparisons, and balanced perspectives",
            capabilities=["analysis", "comparison", "summarization", "critical_thinking", "structured_information"],
            recommended_models=["gpt-4", "gpt-3.5", "mistral"],
            temperature_range=(0.2, 0.5),
            max_tokens_suggestion=2000
        )
        super().__init__(config)

    def get_system_prompt(self, user_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate system prompt for analyze mode"""
        base_prompt = (
            "You are Pombi in ANALYZE mode. Your purpose is to provide systematic analysis and balanced perspectives. "
            "Break down complex information into clear, structured components. Compare and contrast different viewpoints. "
            "Identify patterns, trends, and insights. Provide objective analysis with supporting evidence. "
            "Structure information clearly with headings, bullet points, or numbered lists. "
            "Acknowledge limitations and uncertainties in the analysis. Consider multiple perspectives and avoid bias."
        )

        # Add context-specific enhancements
        if user_context:
            analysis_type = user_context.get("analysis_type", "")
            if analysis_type == "comparison":
                base_prompt += " Use clear comparison criteria. Provide similarities and differences. Use tables or structured formats when helpful."
            elif analysis_type == "swot":
                base_prompt += " Structure analysis into Strengths, Weaknesses, Opportunities, and Threats. Be specific and provide evidence."
            elif analysis_type == "risk":
                base_prompt += " Identify potential risks, assess their likelihood and impact, and suggest mitigation strategies."
            elif analysis_type == "cost_benefit":
                base_prompt += " Quantify costs and benefits where possible. Consider both short-term and long-term implications."
            elif analysis_type == "trend":
                base_prompt += " Identify historical patterns, current status, and future projections. Use data to support trends."

        return base_prompt

    def process_response(self, response: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process and enhance analytical responses"""
        if not response:
            return "I'd be happy to help analyze that! Could you provide more details about what you'd like me to analyze?"

        processed = response.strip()

        # Ensure analytical structure
        processed = self._add_analytical_structure(processed)

        # Add balanced perspective elements
        processed = self._ensure_balance(processed)

        # Include limitations and considerations
        processed = self._add_limitations(processed)

        return processed

    def enhance_prompt(self, user_prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Enhance user prompt for analyze mode"""
        enhanced = user_prompt

        # Add analytical framing if not present
        analyze_keywords = ["analyze", "compare", "evaluate", "assess", "review", "examine"]
        if not any(keyword in user_prompt.lower() for keyword in analyze_keywords):
            enhanced = f"Please analyze: {user_prompt}"

        # Add request for structured analysis
        if "structure" not in user_prompt.lower():
            enhanced += "\n\nPlease provide a structured analysis with clear sections."

        # Add perspective request
        if "perspective" not in user_prompt.lower() and "viewpoint" not in user_prompt.lower():
            enhanced += "\n\nConsider multiple perspectives in your analysis."

        return enhanced

    def validate_response(self, response: str) -> bool:
        """Validate analytical response quality"""
        if not super().validate_response(response):
            return False

        # Check for analytical elements
        response_lower = response.lower()

        # Look for analytical indicators
        analytical_indicators = [
            "analysis", "compare", "contrast", "similarly", "however", "whereas",
            "on the other hand", "in contrast", "advantage", "disadvantage",
            "pro", "con", "benefit", "drawback", "factor", "consideration"
        ]

        analytical_score = sum(1 for indicator in analytical_indicators if indicator in response_lower)

        # Should have multiple analytical elements or be substantial
        return analytical_score >= 2 or len(response) > 250

    def _add_analytical_structure(self, text: str) -> str:
        """Add clear analytical structure to response"""
        # Check if response already has structure
        has_structure = any(
            indicator in text.lower()
            for indicator in [
                "##", "###", "1.", "2.", "•", "-",
                "first", "second", "third", "finally",
                "overview", "summary", "conclusion"
            ]
        )

        # Add structure if missing and response is substantial
        if not has_structure and len(text) > 200:
            # Add analytical framework
            if "analysis" not in text.lower()[:100]:
                text = "## Analysis\n\n" + text

            # Add conclusion if missing
            if "conclusion" not in text.lower()[-100:] and len(text) > 300:
                text += "\n\n## Conclusion\n\nThis analysis provides a structured overview of the key factors and considerations involved."

        return text

    def _ensure_balance(self, text: str) -> str:
        """Ensure the analysis considers multiple perspectives"""
        text_lower = text.lower()

        # Check for balanced perspective indicators
        balance_indicators = [
            "however", "on the other hand", "alternatively", "conversely",
            "despite", "although", "while", "whereas", "in contrast"
        ]

        has_balance = any(indicator in text_lower for indicator in balance_indicators)

        # Add balance if missing and appropriate
        if not has_balance and len(text) > 200:
            # Look for absolute statements and add nuance
            if "always" in text_lower or "never" in text_lower:
                text += "\n\nHowever, it's important to note that these patterns may vary depending on specific contexts and conditions."

        return text

    def _add_limitations(self, text: str) -> str:
        """Add discussion of limitations and considerations"""
        text_lower = text.lower()

        # Check if limitations are already mentioned
        limitation_words = ["limitation", "constraint", "consideration", "caveat", "however"]

        has_limitations = any(word in text_lower for word in limitation_words)

        # Add limitations section if missing and response is analytical
        if not has_limitations and len(text) > 300:
            text += "\n\n## Limitations and Considerations\n\nThis analysis is based on available information and may not account for all variables. Additional context or data could provide further insights."

        return text