"""
Context window management for Pombi AI Assistant
"""

from typing import List, Dict, Any, Optional
import tiktoken

from app.config import settings
from app.memory.conversation_memory import ConversationTurn
from app.utils.logging import setup_logging

logger = setup_logging(__name__)


class ContextManager:
    """Manages context window for AI models"""

    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
        self.tokenizer = None
        self._initialize_tokenizer()

    def _initialize_tokenizer(self):
        """Initialize token counter"""
        try:
            # Use cl100k_base tokenizer (GPT-4/GPT-3.5-turbo)
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Failed to initialize tokenizer: {e}")
            self.tokenizer = None

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        if not text:
            return 0

        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                logger.warning(f"Token counting failed: {e}")

        # Fallback: rough estimate (4 chars per token)
        return len(text) // 4

    def prepare_context(
        self,
        system_prompt: str,
        conversation_turns: List[ConversationTurn],
        user_message: str,
        reserve_tokens: int = 500
    ) -> tuple[List[Dict[str, str]], int]:
        """
        Prepare context window for model input

        Args:
            system_prompt: System instructions
            conversation_turns: Previous conversation history
            user_message: Current user message
            reserve_tokens: Tokens to reserve for model response

        Returns:
            tuple: (formatted_messages, total_tokens)
        """
        available_tokens = self.max_tokens - reserve_tokens

        # Start with system prompt
        messages = []
        system_tokens = self.count_tokens(system_prompt)

        if system_tokens > available_tokens:
            logger.warning("System prompt exceeds available tokens")
            # Truncate system prompt
            system_prompt = self._truncate_text(system_prompt, available_tokens - 100)
            system_tokens = self.count_tokens(system_prompt)

        messages.append({"role": "system", "content": system_prompt})
        used_tokens = system_tokens

        # Add user message (required)
        user_tokens = self.count_tokens(user_message)
        if used_tokens + user_tokens > available_tokens:
            logger.warning("User message exceeds available tokens")
            user_message = self._truncate_text(user_message, available_tokens - used_tokens - 100)
            user_tokens = self.count_tokens(user_message)

        # Build conversation history backwards
        conversation_messages = []
        conversation_tokens = 0

        # Process conversation turns in reverse order
        for turn in reversed(conversation_turns):
            turn_content = f"{turn.role}: {turn.content}"
            turn_tokens = self.count_tokens(turn_content)

            # Check if we can include this turn
            if used_tokens + conversation_tokens + turn_tokens + user_tokens <= available_tokens:
                conversation_messages.insert(0, {
                    "role": turn.role,
                    "content": turn.content
                })
                conversation_tokens += turn_tokens
            else:
                break

        # Combine all messages
        messages.extend(conversation_messages)
        messages.append({"role": "user", "content": user_message})

        total_tokens = used_tokens + conversation_tokens + user_tokens

        logger.debug(
            f"Context prepared: {len(messages)} messages, {total_tokens} tokens",
            extra={
                "system_tokens": system_tokens,
                "conversation_tokens": conversation_tokens,
                "user_tokens": user_tokens,
                "conversation_turns_included": len(conversation_messages)
            }
        )

        return messages, total_tokens

    def summarize_context(self, turns: List[ConversationTurn]) -> str:
        """Create a summary of conversation turns"""
        if not turns:
            return ""

        summary_parts = []

        # Extract key information
        topics_discussed = set()
        modes_used = set()
        questions_asked = []
        key_points = []

        for turn in turns:
            modes_used.add(turn.mode)

            # Look for questions (simple heuristic)
            if turn.role == "user" and "?" in turn.content:
                # Extract first sentence ending with ?
                question = turn.content.split("?")[0] + "?"
                if len(question) < 200:  # Keep reasonable length
                    questions_asked.append(question)

            # Extract key information from assistant responses
            if turn.role == "assistant" and len(turn.content) > 50:
                # Take first sentence as key point
                first_sentence = turn_content = turn.content.split(".")[0] + "."
                if len(first_sentence) < 200:
                    key_points.append(first_sentence)

        # Build summary
        if modes_used:
            summary_parts.append(f"Modes used: {', '.join(modes_used)}")

        if questions_asked:
            summary_parts.append(f"Questions discussed: {'; '.join(questions_asked[:3])}")

        if key_points:
            summary_parts.append(f"Key points: {'; '.join(key_points[:2])}")

        return " | ".join(summary_parts)

    def truncate_message(self, message: str, max_tokens: int) -> str:
        """Truncate message to fit within token limit"""
        return self._truncate_text(message, max_tokens)

    def _truncate_text(self, text: str, max_tokens: int) -> str:
        """Truncate text to specified token count"""
        if not text:
            return text

        current_tokens = self.count_tokens(text)

        if current_tokens <= max_tokens:
            return text

        if self.tokenizer:
            # Use tokenizer for accurate truncation
            tokens = self.tokenizer.encode(text)
            truncated_tokens = tokens[:max_tokens]
            return self.tokenizer.decode(truncated_tokens)
        else:
            # Fallback: simple character-based truncation
            target_chars = max_tokens * 4  # Rough estimate
            if len(text) <= target_chars:
                return text

            # Try to truncate at sentence boundary
            truncated = text[:target_chars]
            last_period = truncated.rfind(".")
            if last_period > target_chars * 0.8:  # If we can keep most of it
                return truncated[:last_period + 1]
            else:
                return truncated + "..."

    def estimate_response_tokens(self, context_tokens: int) -> int:
        """Estimate tokens available for response"""
        reserve_for_response = min(1000, self.max_tokens // 3)
        available = self.max_tokens - context_tokens - reserve_for_response
        return max(100, available)  # Ensure minimum response capacity

    def get_context_stats(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Get statistics about current context"""
        total_tokens = sum(self.count_tokens(msg["content"]) for msg in messages)
        message_count = len(messages)
        user_messages = sum(1 for msg in messages if msg["role"] == "user")
        assistant_messages = sum(1 for msg in messages if msg["role"] == "assistant")
        system_messages = sum(1 for msg in messages if msg["role"] == "system")

        # Calculate average message length
        avg_length = total_tokens / max(message_count, 1)

        # Context utilization
        utilization = (total_tokens / self.max_tokens) * 100

        return {
            "total_tokens": total_tokens,
            "max_tokens": self.max_tokens,
            "message_count": message_count,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "system_messages": system_messages,
            "average_tokens_per_message": round(avg_length, 1),
            "context_utilization_percent": round(utilization, 1),
            "tokens_available_for_response": self.estimate_response_tokens(total_tokens)
        }

    def optimize_context(
        self,
        messages: List[Dict[str, str]],
        target_tokens: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """Optimize context to fit within target token count"""
        if target_tokens is None:
            target_tokens = self.max_tokens - 500  # Reserve space for response

        current_tokens = sum(self.count_tokens(msg["content"]) for msg in messages)

        if current_tokens <= target_tokens:
            return messages

        # Need to truncate - start by removing oldest non-system messages
        optimized = []
        tokens_used = 0

        # Keep system messages
        for msg in messages:
            if msg["role"] == "system":
                optimized.append(msg)
                tokens_used += self.count_tokens(msg["content"])

        # Add recent messages until we hit the limit
        for msg in reversed(messages):
            if msg["role"] != "system":
                msg_tokens = self.count_tokens(msg["content"])
                if tokens_used + msg_tokens <= target_tokens:
                    optimized.insert(1, msg)  # Insert after system messages
                    tokens_used += msg_tokens
                else:
                    break

        return optimized