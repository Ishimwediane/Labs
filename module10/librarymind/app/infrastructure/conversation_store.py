import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ConversationStore:
    """In-memory store mapping conversation IDs to their message history."""

    def __init__(self) -> None:
        self._store: Dict[str, List[Dict[str, Any]]] = {}
        logger.info("ConversationStore initialised (in-memory).")

    def get_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Return all messages for a conversation, oldest first; [] if unknown."""
        history = self._store.get(conversation_id, [])
        logger.debug(f"Loaded {len(history)} messages for '{conversation_id}'.")
        return history

    def append_message(self, conversation_id: str, role: str, content: str) -> None:
        """Append a user or assistant message to a conversation.

        Args:
            conversation_id: Unique session identifier.
            role: Either 'user' or 'assistant'.
            content: Message text.

        Raises:
            ValueError: If role is not 'user' or 'assistant'.
        """
        if role not in ("user", "assistant"):
            raise ValueError(f"Invalid role '{role}'. Must be 'user' or 'assistant'.")

        message: Dict[str, Any] = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }
        self._store.setdefault(conversation_id, []).append(message)
        logger.debug(
            f"Appended [{role}] to '{conversation_id}'. "
            f"Total: {len(self._store[conversation_id])}."
        )

    def clear_history(self, conversation_id: str) -> None:
        """Delete all messages for a conversation; no-op if not found."""
        if conversation_id in self._store:
            del self._store[conversation_id]
            logger.info(f"Cleared history for '{conversation_id}'.")

    def list_conversations(self) -> List[str]:
        """Return all active conversation IDs."""
        return list(self._store.keys())

    def get_message_count(self, conversation_id: str) -> int:
        """Return the number of stored messages for a conversation (0 if unknown)."""
        return len(self._store.get(conversation_id, []))
