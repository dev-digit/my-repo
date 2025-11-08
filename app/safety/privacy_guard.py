"""
Privacy protection for Pombi AI Assistant
"""

import re
import hashlib
from typing import Dict, List, Optional, Set
from datetime import datetime

from app.config import settings
from app.utils.logging import setup_logging

logger = setup_logging(__name__)


class PrivacyGuard:
    """Privacy protection and personal data anonymization"""

    def __init__(self):
        self.enabled = True
        self.sensitive_patterns = self._initialize_patterns()
        self.redaction_token = "[REDACTED]"
        self.hash_cache: Dict[str, str] = {}

    def _initialize_patterns(self) -> Dict[str, re.Pattern]:
        """Initialize patterns for detecting sensitive information"""
        return {
            # Email addresses
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', re.IGNORECASE),

            # Phone numbers (US format)
            "phone": re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'),

            # Social Security Numbers
            "ssn": re.compile(r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b'),

            # Credit card numbers
            "credit_card": re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),

            # IP addresses
            "ip_address": re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),

            # URLs (potential sensitive data)
            "url": re.compile(r'https?://[^\s<>"{}|\\^`[\]]+', re.IGNORECASE),

            # Bank account numbers (simplified)
            "bank_account": re.compile(r'\b(?:account|acct)\s*(?:#|number)?\s*:?\s*\d{8,}\b', re.IGNORECASE),

            # Driver's license patterns (US)
            "drivers_license": re.compile(r'\b(?:dl|driver\'s? license)\s*(?:#|number)?\s*:?\s*[A-Z0-9]{8,}\b', re.IGNORECASE),

            # Passport numbers
            "passport": re.compile(r'\b(?:passport)\s*(?:#|number)?\s*:?\s*[A-Z0-9]{6,}\b', re.IGNORECASE),

            # Medical record numbers
            "medical_record": re.compile(r'\b(?:mrn|medical\s*record)\s*(?:#|number)?\s*:?\s*\d{6,}\b', re.IGNORECASE),

            # Addresses (simplified pattern)
            "address": re.compile(r'\d+\s+[\w\s]+\s+(?:street|st|avenue|ave|road|rd|lane|ln|drive|dr|boulevard|blvd)\b', re.IGNORECASE),

            # Dates of birth (MM/DD/YYYY format)
            "dob": re.compile(r'\b(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])/(19|20)\d{2}\b'),
        }

    def sanitize_input(self, text: str, user_id: Optional[str] = None) -> tuple[str, Dict[str, List[str]]]:
        """
        Sanitize input text by removing sensitive information

        Args:
            text: Input text to sanitize
            user_id: Optional user ID for logging

        Returns:
            tuple: (sanitized_text, detected_info)
        """
        if not text or not self.enabled:
            return text, {}

        sanitized = text
        detected_info = {}

        # Check each pattern
        for info_type, pattern in self.sensitive_patterns.items():
            matches = pattern.findall(sanitized)
            if matches:
                detected_info[info_type] = matches
                # Replace with redaction token
                sanitized = pattern.sub(f"{self.redaction_token} {info_type.upper()}", sanitized)

        # Additional checks for patterns that are harder to catch with regex
        sanitized = self._additional_checks(sanitized, detected_info)

        # Log privacy events
        if detected_info:
            logger.info(
                "Sensitive data detected and redacted",
                extra={
                    "user_id": user_id,
                    "data_types": list(detected_info.keys()),
                    "total_matches": sum(len(matches) for matches in detected_info.values()),
                    "original_length": len(text),
                    "sanitized_length": len(sanitized)
                }
            )

        return sanitized, detected_info

    def sanitize_response(self, text: str) -> str:
        """Sanitize AI-generated response content"""
        if not text or not self.enabled:
            return text

        sanitized = text

        # Remove any personal data that might have been accidentally included
        for info_type, pattern in self.sensitive_patterns.items():
            sanitized = pattern.sub(f"{self.redaction_token} {info_type.upper()}", sanitized)

        # Add privacy disclaimer for certain content
        if any(keyword in sanitized.lower() for keyword in ["personal", "private", "confidential"]):
            sanitized += "\n\n🔒 **Privacy Note**: Avoid sharing personal, sensitive, or confidential information in our conversations."

        return sanitized

    def hash_sensitive_data(self, text: str) -> str:
        """
        Hash text for privacy-preserving analytics

        Args:
            text: Text to hash

        Returns:
            str: Hashed representation
        """
        if not text:
            return ""

        # Check cache first
        if text in self.hash_cache:
            return self.hash_cache[text]

        # Create hash
        hash_obj = hashlib.sha256(text.encode())
        hash_hex = hash_obj.hexdigest()[:16]  # Use first 16 characters

        # Cache result
        self.hash_cache[text] = hash_hex
        return hash_hex

    def _additional_checks(self, text: str, detected_info: Dict[str, List[str]]) -> str:
        """Additional privacy checks beyond regex patterns"""
        # Check for potential passwords (common patterns)
        password_indicators = ["password", "pwd", "pass", "secret", "key"]
        words = text.lower().split()

        for i, word in enumerate(words):
            if word in password_indicators and i + 1 < len(words):
                # Look for what follows password indicator
                next_word = words[i + 1]
                if len(next_word) >= 8:  # Potential password
                    # Replace the pattern
                    pattern = rf'{word}\s+{re.escape(next_word)}'
                    text = re.sub(pattern, f'{word} {self.redaction_token}', text, flags=re.IGNORECASE)
                    detected_info.setdefault("potential_password", []).append(f"{word} [REDACTED]")

        # Check for API keys (simplified pattern)
        api_key_pattern = re.compile(r'\b(?:api[_-]?key|token|secret)[\s:=]+\s*[A-Za-z0-9+/]{20,}\b', re.IGNORECASE)
        api_matches = api_key_pattern.findall(text)
        if api_matches:
            detected_info["api_key"] = api_matches
            text = api_key_pattern.sub(f"api_key {self.redaction_token}", text)

        return text

    def detect_privacy_risks(self, text: str) -> Dict[str, any]:
        """
        Analyze text for privacy risks

        Args:
            text: Text to analyze

        Returns:
            Dict containing privacy risk assessment
        """
        if not text or not self.enabled:
            return {"risk_level": "low", "risks": []}

        _, detected_info = self.sanitize_input(text)

        risks = []
        risk_score = 0

        # Score different types of sensitive data
        risk_weights = {
            "email": 2,
            "phone": 3,
            "ssn": 5,
            "credit_card": 5,
            "bank_account": 5,
            "drivers_license": 4,
            "passport": 4,
            "medical_record": 4,
            "address": 3,
            "dob": 2,
            "ip_address": 2,
            "api_key": 4,
            "potential_password": 3
        }

        total_score = 0
        for info_type, matches in detected_info.items():
            weight = risk_weights.get(info_type, 1)
            count = len(matches)
            item_score = weight * count
            total_score += item_score

            risks.append({
                "type": info_type,
                "count": count,
                "severity": "high" if weight >= 4 else "medium" if weight >= 2 else "low",
                "examples": matches[:2]  # Show first 2 examples
            })

        # Determine overall risk level
        if total_score >= 10:
            risk_level = "high"
        elif total_score >= 5:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_level": risk_level,
            "risk_score": total_score,
            "risks": risks,
            "total_sensitive_items": sum(len(matches) for matches in detected_info.values()),
            "recommendation": self._get_privacy_recommendation(risk_level)
        }

    def _get_privacy_recommendation(self, risk_level: str) -> str:
        """Get privacy recommendation based on risk level"""
        recommendations = {
            "high": "This message contains highly sensitive personal information. Consider removing all personal identifiers before sharing.",
            "medium": "This message contains some personal information. Review and remove sensitive details before sharing.",
            "low": "This message appears to have minimal privacy concerns, but always avoid sharing unnecessary personal information."
        }
        return recommendations.get(risk_level, "Be cautious about sharing personal information.")

    def get_privacy_stats(self) -> Dict[str, any]:
        """Get privacy protection statistics"""
        return {
            "enabled": self.enabled,
            "patterns_count": len(self.sensitive_patterns),
            "cache_size": len(self.hash_cache),
            "supported_data_types": list(self.sensitive_patterns.keys()),
            "redaction_token": self.redaction_token
        }

    def clear_cache(self):
        """Clear the hash cache"""
        self.hash_cache.clear()
        logger.info("Privacy guard cache cleared")