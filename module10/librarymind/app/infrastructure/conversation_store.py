"""
app/infrastructure/conversation_store.py
=========================================
Part 5 — LibraryMind AI Librarian Chatbot

WHAT THIS FILE DOES:
    Stores the message history for every chat session.
    Each session is identified by a unique conversation_id (a UUID string).
    Think of it like a notebook: one page per patron, each page holding
    everything they said and what the librarian replied.

MEMORY LAYOUT:
    {
        "conv-abc-123": [
            {"role": "user",      "content": "Hi!",            "timestamp": "..."},
            {"role": "assistant", "content": "Hello! ...",     "timestamp": "..."},
            {"role": "user",      "content": "Recommend sci-fi", "timestamp": "..."},
            {"role": "assistant", "content": "Try Dune ...",   "timestamp": "..."},
        ],
        "conv-xyz-789": [
            ...   # completely separate from the conversation above
        ]
    }

NOTE FOR PRODUCTION:
    This uses a plain Python dict (in-memory).
    On server restart all history is lost.
    For persistence, swap the dict for a Redis client — the interface stays the same.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ConversationStore:
    """
    A simple in-memory store for per-session conversation history.

    Each conversation_id maps to a list of message dicts.
    Messages are stored in order from oldest to newest.

    Each message dict has the shape:
        {
            "role":      "user" | "assistant",
            "content":   "the text of the message",
            "timestamp": "ISO-8601 UTC datetime string"
        }
    """

    def __init__(self) -> None:
        # The main storage: conversation_id (str) -> list of message dicts
        # This dict is the "memory" of the entire chatbot.
        self._store: Dict[str, List[Dict[str, Any]]] = {}
        logger.info("ConversationStore initialised (in-memory).")

    # ------------------------------------------------------------------
    # Public Interface
    # ------------------------------------------------------------------

    def get_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Return the full message history for a given conversation_id.

        If the conversation_id has never been seen before, return an empty
        list — this is how a brand-new conversation starts.

        Args:
            conversation_id: The unique ID of the chat session.

        Returns:
            A list of message dicts, oldest first.
            Returns [] for unknown conversation IDs.
        """
        # dict.get() returns the default (empty list) if the key doesn't exist.
        history = self._store.get(conversation_id, [])
        logger.debug(
            f"Loaded {len(history)} messages for conversation '{conversation_id}'."
        )
        return history

    def append_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> None:
        """
        Append a single message to the history of a conversation.

        If this is the first message in the conversation, the entry is
        created automatically — you do not need to initialise it first.

        Args:
            conversation_id: The unique ID of the chat session.
            role:            Either "user" or "assistant".
            content:         The text of the message.
        """
        # Validate role to catch bugs early.
        if role not in ("user", "assistant"):
            raise ValueError(
                f"Invalid role '{role}'. Must be 'user' or 'assistant'."
            )

        # Build the message dict.
        message: Dict[str, Any] = {
            "role": role,
            "content": content,
            # Timestamps are useful for debugging and future audit logs.
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }

        # setdefault creates the list the first time this conv_id appears.
        self._store.setdefault(conversation_id, []).append(message)

        logger.debug(
            f"Appended [{role}] message to conversation '{conversation_id}'. "
            f"Total messages: {len(self._store[conversation_id])}."
        )

    def clear_history(self, conversation_id: str) -> None:
        """
        Delete all messages for a given conversation_id.

        Useful for:
        - "Start over" buttons in a UI.
        - Test teardown.
        - Privacy / GDPR deletion requests.

        Args:
            conversation_id: The unique ID of the chat session to clear.
        """
        if conversation_id in self._store:
            del self._store[conversation_id]
            logger.info(f"Cleared history for conversation '{conversation_id}'.")
        else:
            # Clearing a non-existent conversation is not an error.
            logger.debug(
                f"clear_history called for unknown conversation '{conversation_id}' — nothing to clear."
            )

    def list_conversations(self) -> List[str]:
        """
        Return all active conversation IDs.

        Useful for admin dashboards, debugging, or cleanup jobs.

        Returns:
            A list of conversation_id strings.
        """
        return list(self._store.keys())

    def get_message_count(self, conversation_id: str) -> int:
        """
        Return the number of stored messages for a conversation.

        Args:
            conversation_id: The unique ID of the chat session.

        Returns:
            Integer message count (0 if not found).
        """
        return len(self._store.get(conversation_id, []))
