"""
Conversation memory management for Pombi AI Assistant
"""

import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

from app.config import settings
from app.utils.logging import setup_logging

logger = setup_logging(__name__)


@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation"""
    role: str  # "user" or "assistant"
    content: str
    mode: str
    timestamp: datetime
    tokens_used: int = 0
    model_used: str = ""
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationTurn":
        """Create from dictionary"""
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class ConversationMemory:
    """Manages conversation history with session-based storage"""

    def __init__(self):
        self.conversations: Dict[str, List[ConversationTurn]] = {}
        self.session_metadata: Dict[str, Dict[str, Any]] = {}
        self._cleanup_expired_sessions()

    def create_conversation(self) -> str:
        """Create a new conversation and return its ID"""
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = []
        self.session_metadata[conversation_id] = {
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "turn_count": 0,
            "total_tokens": 0
        }

        logger.info(f"Created new conversation: {conversation_id}")
        return conversation_id

    def add_turn(
        self,
        conversation_id: str,
        role: str,
        content: str,
        mode: str,
        tokens_used: int = 0,
        model_used: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a conversation turn"""
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        turn = ConversationTurn(
            role=role,
            content=content,
            mode=mode,
            timestamp=datetime.utcnow(),
            tokens_used=tokens_used,
            model_used=model_used,
            metadata=metadata or {}
        )

        self.conversations[conversation_id].append(turn)

        # Update session metadata
        session = self.session_metadata[conversation_id]
        session["last_activity"] = datetime.utcnow()
        session["turn_count"] += 1
        session["total_tokens"] += tokens_used

        # Limit conversation length
        if len(self.conversations[conversation_id]) > settings.max_conversation_length:
            self.conversations[conversation_id] = self.conversations[conversation_id][-settings.max_conversation_length:]

        logger.debug(f"Added turn to conversation {conversation_id}: {role} ({len(content)} chars)")

    def get_conversation(self, conversation_id: str) -> List[ConversationTurn]:
        """Get conversation history"""
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Update last activity
        self.session_metadata[conversation_id]["last_activity"] = datetime.utcnow()

        return self.conversations[conversation_id]

    def get_conversation_for_model(
        self,
        conversation_id: str,
        max_turns: int = 10
    ) -> List[Dict[str, str]]:
        """Get conversation formatted for AI model input"""
        if conversation_id not in self.conversations:
            return []

        turns = self.conversations[conversation_id][-max_turns:]
        return [
            {
                "role": turn.role,
                "content": turn.content
            }
            for turn in turns
        ]

    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation summary and metadata"""
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        session = self.session_metadata[conversation_id]
        turns = self.conversations[conversation_id]

        # Calculate mode distribution
        mode_counts = {}
        for turn in turns:
            mode_counts[turn.mode] = mode_counts.get(turn.mode, 0) + 1

        # Calculate model usage
        model_usage = {}
        for turn in turns:
            if turn.model_used:
                model_usage[turn.model_used] = model_usage.get(turn.model_used, 0) + 1

        return {
            "conversation_id": conversation_id,
            "created_at": session["created_at"].isoformat(),
            "last_activity": session["last_activity"].isoformat(),
            "turn_count": session["turn_count"],
            "total_tokens": session["total_tokens"],
            "duration_minutes": (datetime.utcnow() - session["created_at"]).total_seconds() / 60,
            "mode_distribution": mode_counts,
            "model_usage": model_usage,
            "is_active": self._is_session_active(conversation_id)
        }

    def delete_conversation(self, conversation_id: str) -> None:
        """Delete conversation and its metadata"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
        if conversation_id in self.session_metadata:
            del self.session_metadata[conversation_id]

        logger.info(f"Deleted conversation: {conversation_id}")

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and return count of cleaned sessions"""
        return self._cleanup_expired_sessions()

    def _cleanup_expired_sessions(self) -> int:
        """Internal method to clean up expired sessions"""
        expired_cutoff = datetime.utcnow() - timedelta(minutes=settings.session_timeout_minutes)
        expired_sessions = []

        for conversation_id, metadata in self.session_metadata.items():
            if metadata["last_activity"] < expired_cutoff:
                expired_sessions.append(conversation_id)

        for conversation_id in expired_sessions:
            self.delete_conversation(conversation_id)

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired conversations")

        return len(expired_sessions)

    def _is_session_active(self, conversation_id: str) -> bool:
        """Check if session is still active"""
        if conversation_id not in self.session_metadata:
            return False

        last_activity = self.session_metadata[conversation_id]["last_activity"]
        cutoff = datetime.utcnow() - timedelta(minutes=settings.session_timeout_minutes)
        return last_activity >= cutoff

    def get_all_conversations(self) -> List[Dict[str, Any]]:
        """Get summaries of all conversations"""
        summaries = []
        for conversation_id in self.conversations:
            try:
                summary = self.get_conversation_summary(conversation_id)
                summaries.append(summary)
            except Exception as e:
                logger.error(f"Error getting summary for {conversation_id}: {e}")

        # Sort by last activity (most recent first)
        summaries.sort(key=lambda x: x["last_activity"], reverse=True)
        return summaries

    def export_conversation(self, conversation_id: str) -> str:
        """Export conversation as JSON string"""
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        export_data = {
            "conversation_id": conversation_id,
            "metadata": self.session_metadata[conversation_id],
            "turns": [turn.to_dict() for turn in self.conversations[conversation_id]],
            "exported_at": datetime.utcnow().isoformat()
        }

        # Convert datetime objects to strings
        export_data["metadata"]["created_at"] = export_data["metadata"]["created_at"].isoformat()
        export_data["metadata"]["last_activity"] = export_data["metadata"]["last_activity"].isoformat()

        return json.dumps(export_data, indent=2)

    def get_session_stats(self) -> Dict[str, Any]:
        """Get overall session statistics"""
        total_conversations = len(self.conversations)
        active_conversations = sum(
            1 for conv_id in self.conversations
            if self._is_session_active(conv_id)
        )

        total_turns = sum(
            len(turns) for turns in self.conversations.values()
        )

        total_tokens = sum(
            metadata["total_tokens"]
            for metadata in self.session_metadata.values()
        )

        # Mode distribution across all conversations
        all_modes = []
        for turns in self.conversations.values():
            for turn in turns:
                all_modes.append(turn.mode)

        mode_distribution = {}
        for mode in all_modes:
            mode_distribution[mode] = mode_distribution.get(mode, 0) + 1

        return {
            "total_conversations": total_conversations,
            "active_conversations": active_conversations,
            "total_turns": total_turns,
            "total_tokens": total_tokens,
            "average_turns_per_conversation": total_turns / max(total_conversations, 1),
            "mode_distribution": mode_distribution,
            "memory_storage": "in-memory"
        }