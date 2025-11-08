"""
Code mode for programming and technical assistance
"""

from typing import Dict, Any, Optional
import re

from .base_mode import BaseMode, ModeConfig
from app.utils.logging import setup_logging

logger = setup_logging(__name__)


class CodeMode(BaseMode):
    """Code mode - specializes in programming and technical assistance"""

    def __init__(self):
        config = ModeConfig(
            name="code",
            description="Provides working code examples with explanations and best practices",
            capabilities=["programming", "code_examples", "debugging", "best_practices", "technical_explanation"],
            recommended_models=["gpt-4", "mistral", "gpt-3.5"],
            temperature_range=(0.1, 0.3),
            max_tokens_suggestion=2500
        )
        super().__init__(config)

    def get_system_prompt(self, user_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate system prompt for code mode"""
        base_prompt = (
            "You are Pombi in CODE mode. Your purpose is to help with programming and technical tasks. "
            "Provide working code examples with clear explanations. Explain code logic step-by-step. "
            "Include syntax highlighting and comments. Suggest best practices and optimizations. "
            "Focus on practical, usable solutions. When providing code, ensure it's complete and runnable. "
            "Explain the reasoning behind your approach and discuss alternative solutions."
        )

        # Add language-specific guidance
        if user_context:
            language = user_context.get("language", "").lower()
            if language == "python":
                base_prompt += " Follow PEP 8 style guidelines. Use type hints where appropriate. Include docstrings for functions."
            elif language == "javascript":
                base_prompt += " Use modern ES6+ syntax. Include proper error handling. Consider browser and Node.js compatibility."
            elif language == "java":
                base_prompt += " Follow Java naming conventions. Include proper access modifiers. Consider design patterns."
            elif language == "cpp":
                base_prompt += " Use RAII principles. Include proper memory management. Consider modern C++ features."
            elif language == "sql":
                base_prompt += " Use proper indexing. Consider performance implications. Include JOIN explanations."

            task_type = user_context.get("task_type", "")
            if task_type == "debugging":
                base_prompt += " Systematically identify potential issues. Explain the debugging process. Provide specific fixes."
            elif task_type == "optimization":
                base_prompt += " Analyze performance bottlenecks. Suggest specific optimizations. Include complexity analysis."
            elif task_type == "design":
                base_prompt += " Consider scalability and maintainability. Discuss design patterns and architecture."

        return base_prompt

    def process_response(self, response: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process and enhance code responses"""
        if not response:
            return "I'd be happy to help you with your coding task! Could you provide more details about what you're trying to accomplish?"

        processed = response.strip()

        # Ensure code blocks are properly formatted
        processed = self._format_code_blocks(processed)

        # Add explanations to code
        processed = self._ensure_code_explanations(processed)

        # Add best practices reminders
        processed = self._add_best_practices(processed, context)

        return processed

    def enhance_prompt(self, user_prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Enhance user prompt for code mode"""
        enhanced = user_prompt

        # Detect programming language if not specified
        language_indicators = {
            "python": ["def ", "import ", "print(", "self.", "elif "],
            "javascript": ["function ", "const ", "let ", "=>", "console.log"],
            "java": ["public class", "public static void", "System.out"],
            "cpp": ["#include", "std::", "cout", "int main"],
            "sql": ["SELECT", "FROM", "WHERE", "JOIN"]
        }

        detected_language = None
        for lang, indicators in language_indicators.items():
            if any(indicator in user_prompt for indicator in indicators):
                detected_language = lang
                break

        if detected_language and "language" not in user_prompt.lower():
            enhanced = f"Language: {detected_language}\n\n{enhanced}"

        # Add requirement for working code
        if "code" in user_prompt.lower() and "example" not in user_prompt.lower():
            enhanced += "\n\nPlease provide a complete, working code example."

        return enhanced

    def validate_response(self, response: str) -> bool:
        """Validate code response quality"""
        if not super().validate_response(response):
            return False

        # Check for code elements
        has_code = (
            "```" in response or
            "function" in response or
            "def " in response or
            "class " in response or
            "{" in response or
            ";" in response
        )

        # For code mode, should have code or explanation
        response_lower = response.lower()
        has_explanation = any(
            indicator in response_lower
            for indicator in ["explain", "this code", "here's how", "the way this works", "step by step"]
        )

        return has_code or has_explanation

    def _format_code_blocks(self, text: str) -> str:
        """Ensure code blocks are properly formatted with language hints"""
        # Find code blocks without language specification
        code_blocks = re.findall(r'```(\w*)\n(.*?)```', text, re.DOTALL)

        for lang, code in code_blocks:
            if not lang:  # No language specified
                # Try to detect language
                if "def " in code or "import " in code:
                    detected_lang = "python"
                elif "function" in code or "const " in code or "=>" in code:
                    detected_lang = "javascript"
                elif "public class" in code or "System.out" in code:
                    detected_lang = "java"
                elif "#include" in code or "std::" in code:
                    detected_lang = "cpp"
                else:
                    detected_lang = ""

                # Replace with language-specific code block
                if detected_lang:
                    old_block = f"```\n{code}```"
                    new_block = f"```{detected_lang}\n{code}```"
                    text = text.replace(old_block, new_block)

        return text

    def _ensure_code_explanations(self, text: str) -> str:
        """Ensure code blocks have explanations"""
        code_blocks = re.findall(r'```(\w*)\n(.*?)```', text, re.DOTALL)

        for lang, code in code_blocks:
            # Check if there's explanation before or after the code block
            block_start = text.find(f"```{lang}\n{code}```")

            # Look for explanation in text before and after
            before_text = text[:block_start][-200:]  # 200 chars before
            after_text = text[block_start + len(f"```{lang}\n{code}```")][:200]  # 200 chars after

            has_explanation = any(
                indicator in (before_text + after_text).lower()
                for indicator in ["explain", "this code", "here's how", "does", "works", "accomplish"]
            )

            # Add explanation if missing
            if not has_explanation and len(code.strip()) > 20:
                explanation = "\n\nThis code accomplishes the task by"
                text = text.replace(
                    f"```{lang}\n{code}```",
                    f"```{lang}\n{code}```{explanation} implementing the core logic step by step."
                )

        return text

    def _add_best_practices(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Add best practices reminders when appropriate"""
        # Check if best practices are already mentioned
        if "best practice" in text.lower() or "good practice" in text.lower():
            return text

        # Add relevant best practices based on code content
        practices_to_add = []

        if "input" in text.lower() or "user input" in text.lower():
            practices_to_add.append("always validate user input")

        if "file" in text.lower() or "open(" in text:
            practices_to_add.append("use proper error handling for file operations")

        if "database" in text.lower() or "sql" in text.lower():
            practices_to_add.append("use parameterized queries to prevent SQL injection")

        if "password" in text.lower() or "secret" in text.lower():
            practices_to_add.append("never hardcode sensitive information")

        if practices_to_add:
            practices_text = ", ".join(practices_to_add)
            text += f"\n\n💡 **Best practices:** {practices_text}."

        return text