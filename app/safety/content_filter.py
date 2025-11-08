"""
Content filtering and moderation for Pombi AI Assistant
"""

import re
from typing import Dict, List, Tuple, Optional
from enum import Enum

from app.config import settings
from app.utils.logging import setup_logging

logger = setup_logging(__name__)


class ContentCategory(Enum):
    """Categories of content to filter"""
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    SELF_HARM = "self_harm"
    SEXUAL_CONTENT = "sexual_content"
    ILLEGAL_ACTIVITIES = "illegal_activities"
    PERSONAL_DATA = "personal_data"
    SPAM = "spam"
    MISINFORMATION = "misinformation"


class FilterResult(Enum):
    """Result of content filtering"""
    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"
    REJECT = "reject"


class ContentFilter:
    """Content filtering and moderation system"""

    def __init__(self):
        self.enabled = settings.enable_content_filter
        self._initialize_filters()

    def _initialize_filters(self):
        """Initialize content filtering patterns"""
        # Define patterns for different categories
        self.filter_patterns = {
            ContentCategory.HATE_SPEECH: [
                r'\b(hate|kill.*\w+(?:s|ers)?|destroy.*\w+(?:s|ers)?)\b.*\b(?:race|religion|ethnic|national|gender|sexual)\b',
                r'\b(slur|derogatory|discriminat\w+)\b',
            ],
            ContentCategory.VIOLENCE: [
                r'\b(kill|murder|violence|harm|injure|attack)\b',
                r'\b(weapon|bomb|gun|knife|shoot)\b',
            ],
            ContentCategory.SELF_HARM: [
                r'\b(suicide|self.harm|kill.myself|hurt.myself)\b',
                r'\b(depression|anxiety|panic attack)\b.*\b(help|support)\b',
            ],
            ContentCategory.SEXUAL_CONTENT: [
                r'\b(explicit|sexual|nsfw|porn|adult)\b',
                r'\b(inappropriate|offensive)\s+(?:content|material)\b',
            ],
            ContentCategory.ILLEGAL_ACTIVITIES: [
                r'\b(illegal|hack|crack|pirate|steal|theft)\b',
                r'\b(drug|substance)\s+(?:abuse|use|sell)\b',
            ],
            ContentCategory.PERSONAL_DATA: [
                r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',  # SSN pattern
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit card pattern
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email pattern
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone number pattern
            ],
            ContentCategory.SPAM: [
                r'(buy now|click here|limited time|act now|free money)',
                r'(http[s]?://\S+)',  # URLs
            ],
            ContentCategory.MISINFORMATION: [
                r'\b(fake.news|conspiracy|hoax|misinformation)\b',
                r'\b(cure.*cancer|miracle.*cure)\b',
            ]
        }

        # Keywords that should trigger warnings
        self.warning_keywords = [
            "dangerous", "harmful", "unsafe", "risky",
            "medical advice", "legal advice", "financial advice",
            "diagnosis", "treatment", "prescription"
        ]

    def filter_content(self, content: str, user_id: Optional[str] = None) -> Tuple[FilterResult, List[ContentCategory]]:
        """
        Filter content for policy violations

        Args:
            content: Content to filter
            user_id: Optional user identifier for logging

        Returns:
            tuple: (filter_result, triggered_categories)
        """
        if not self.enabled:
            return FilterResult.ALLOW, []

        triggered_categories = []
        content_lower = content.lower()

        # Check each category
        for category, patterns in self.filter_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content_lower, re.IGNORECASE):
                    triggered_categories.append(category)
                    break

        # Check for warning keywords
        has_warnings = any(keyword in content_lower for keyword in self.warning_keywords)

        # Determine filter result
        if not triggered_categories:
            return FilterResult.ALLOW, []

        # High severity categories get blocked
        high_severity = {ContentCategory.HATE_SPEECH, ContentCategory.VIOLENCE, ContentCategory.SELF_HARM}
        if any(cat in high_severity for cat in triggered_categories):
            logger.warning(
                "Content blocked",
                extra={
                    "user_id": user_id,
                    "categories": [cat.value for cat in triggered_categories],
                    "content_length": len(content)
                }
            )
            return FilterResult.BLOCK, triggered_categories

        # Medium severity categories get warnings
        medium_severity = {ContentCategory.SEXUAL_CONTENT, ContentCategory.ILLEGAL_ACTIVITIES}
        if any(cat in medium_severity for cat in triggered_categories):
            logger.info(
                "Content warning triggered",
                extra={
                    "user_id": user_id,
                    "categories": [cat.value for cat in triggered_categories],
                    "content_length": len(content)
                }
            )
            return FilterResult.WARN, triggered_categories

        # Low severity categories are rejected but can be appealed
        low_severity = {ContentCategory.SPAM, ContentCategory.MISINFORMATION, ContentCategory.PERSONAL_DATA}
        if any(cat in low_severity for cat in triggered_categories):
            logger.info(
                "Content rejected",
                extra={
                    "user_id": user_id,
                    "categories": [cat.value for cat in triggered_categories],
                    "content_length": len(content)
                }
            )
            return FilterResult.REJECT, triggered_categories

        # Default to warning if unexpected categories
        return FilterResult.WARN, triggered_categories

    def filter_response(self, response: str) -> str:
        """Filter AI-generated response content"""
        if not self.enabled:
            return response

        # Remove personal data patterns from responses
        filtered = response

        # Remove email addresses
        filtered = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL REMOVED]', filtered)

        # Remove phone numbers
        filtered = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE REMOVED]', filtered)

        # Remove SSN patterns
        filtered = re.sub(r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b', '[SSN REMOVED]', filtered)

        # Remove credit card patterns
        filtered = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD REMOVED]', filtered)

        # Add safety disclaimer for certain topics
        if any(keyword in filtered.lower() for keyword in ["medical", "legal", "financial"]):
            if "disclaimer" not in filtered.lower():
                filtered += "\n\n⚠️ **Disclaimer**: This information is for educational purposes only and should not be considered professional advice. Please consult with qualified professionals for medical, legal, or financial matters."

        return filtered

    def get_filter_summary(self, content: str) -> Dict[str, any]:
        """Get detailed filtering analysis for content"""
        if not self.enabled:
            return {"enabled": False}

        result, categories = self.filter_content(content)
        content_lower = content.lower()

        # Count keyword matches by category
        category_matches = {}
        for category in categories:
            patterns = self.filter_patterns[category]
            matches = 0
            for pattern in patterns:
                matches += len(re.findall(pattern, content_lower, re.IGNORECASE))
            category_matches[category.value] = matches

        # Count warning keywords
        warning_matches = sum(1 for keyword in self.warning_keywords if keyword in content_lower)

        return {
            "enabled": True,
            "result": result.value,
            "categories": [cat.value for cat in categories],
            "category_matches": category_matches,
            "warning_keywords_found": warning_matches,
            "content_length": len(content),
            "has_warnings": result == FilterResult.WARN,
            "is_blocked": result == FilterResult.BLOCK,
            "is_rejected": result == FilterResult.REJECT
        }

    def is_safe_content(self, content: str) -> bool:
        """Quick check if content passes all filters"""
        if not self.enabled:
            return True

        result, _ = self.filter_content(content)
        return result == FilterResult.ALLOW

    def get_safety_message(self, result: FilterResult, categories: List[ContentCategory]) -> str:
        """Get appropriate safety message for filter result"""
        if result == FilterResult.BLOCK:
            return "I cannot process this request as it violates safety guidelines. If you need help, please contact appropriate support services."

        elif result == FilterResult.WARN:
            if ContentCategory.SELF_HARM in categories:
                return "I notice you're going through a difficult time. Please reach out to mental health professionals or call emergency services if you're in immediate danger."
            elif ContentCategory.ILLEGAL_ACTIVITIES in categories:
                return "I cannot assist with activities that may be illegal or harmful. Please ensure your request complies with all applicable laws."
            else:
                return "Please be aware that this topic may involve sensitive content. Proceed with caution and consider seeking professional guidance if needed."

        elif result == FilterResult.REJECT:
            if ContentCategory.SPAM in categories:
                return "Please provide a genuine question or request without promotional content or links."
            elif ContentCategory.MISINFORMATION in categories:
                return "I cannot provide information that may be misleading or inaccurate. Please consult verified sources for this topic."
            elif ContentCategory.PERSONAL_DATA in categories:
                return "Please remove any personal information such as email addresses, phone numbers, or financial data from your request."
            else:
                return "I cannot process this request as formatted. Please rephrase without including sensitive information."

        return ""  # No message for ALLOW result