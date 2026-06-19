"""
ConversationStore — Redis-backed with graceful in-memory fallback.

Storage strategy:
  - Primary: Redis List  key = "conv:{conversation_id}"
             Each element is a JSON-serialised message dict.
             TTL is refreshed to CONVERSATION_TTL on every write.
  - Fallback: plain Python dict (same as the original implementation)
              used automatically when Redis is unavailable.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConversationStore:
    """Persist conversation histories in Redis (with in-memory fallback)."""

    KEY_PREFIX = "conv:"

    def __init__(self, redis_url: str = "redis://localhost:6379/0", ttl: int = 86400) -> None:
        self._ttl = ttl
        self._fallback: Dict[str, List[Dict[str, Any]]] = {}
        self._redis = None
        self._redis_ok = False

        self._connect(redis_url)

    # ------------------------------------------------------------------
    # Internal — Redis connection
    # ------------------------------------------------------------------

    def _connect(self, redis_url: str) -> None:
        try:
            import redis as redis_lib
            client = redis_lib.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            client.ping()
            self._redis = client
            self._redis_ok = True
            logger.info(f"ConversationStore: connected to Redis at {redis_url}.")
        except Exception as exc:
            logger.warning(
                f"ConversationStore: Redis unavailable ({exc}). "
                "Falling back to in-memory store."
            )
            self._redis_ok = False

    def _key(self, conversation_id: str) -> str:
        return f"{self.KEY_PREFIX}{conversation_id}"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Return all messages for a conversation, oldest first; [] if unknown."""
        if self._redis_ok:
            try:
                raw = self._redis.lrange(self._key(conversation_id), 0, -1)
                messages = [json.loads(m) for m in raw]
                logger.debug(
                    f"Redis: loaded {len(messages)} messages for '{conversation_id}'."
                )
                return messages
            except Exception as exc:
                logger.warning(f"Redis read error: {exc}. Reading from fallback.")

        # Fallback
        history = self._fallback.get(conversation_id, [])
        logger.debug(
            f"In-memory: loaded {len(history)} messages for '{conversation_id}'."
        )
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

        if self._redis_ok:
            try:
                key = self._key(conversation_id)
                self._redis.rpush(key, json.dumps(message))
                self._redis.expire(key, self._ttl)  # refresh TTL on every write
                total = self._redis.llen(key)
                logger.debug(
                    f"Redis: appended [{role}] to '{conversation_id}'. Total: {total}."
                )
                return
            except Exception as exc:
                logger.warning(f"Redis write error: {exc}. Writing to fallback.")

        # Fallback
        self._fallback.setdefault(conversation_id, []).append(message)
        logger.debug(
            f"In-memory: appended [{role}] to '{conversation_id}'. "
            f"Total: {len(self._fallback[conversation_id])}."
        )

    def clear_history(self, conversation_id: str) -> None:
        """Delete all messages for a conversation; no-op if not found."""
        if self._redis_ok:
            try:
                self._redis.delete(self._key(conversation_id))
                logger.info(f"Redis: cleared history for '{conversation_id}'.")
                return
            except Exception as exc:
                logger.warning(f"Redis delete error: {exc}. Clearing from fallback.")

        if conversation_id in self._fallback:
            del self._fallback[conversation_id]
            logger.info(f"In-memory: cleared history for '{conversation_id}'.")

    def list_conversations(self) -> List[str]:
        """Return all active conversation IDs."""
        if self._redis_ok:
            try:
                keys = self._redis.keys(f"{self.KEY_PREFIX}*")
                ids = [k[len(self.KEY_PREFIX):] for k in keys]
                logger.debug(f"Redis: found {len(ids)} active conversations.")
                return ids
            except Exception as exc:
                logger.warning(f"Redis scan error: {exc}. Listing from fallback.")

        return list(self._fallback.keys())

    def get_message_count(self, conversation_id: str) -> int:
        """Return the number of stored messages for a conversation (0 if unknown)."""
        if self._redis_ok:
            try:
                return self._redis.llen(self._key(conversation_id))
            except Exception as exc:
                logger.warning(f"Redis llen error: {exc}. Counting from fallback.")

        return len(self._fallback.get(conversation_id, []))

    def session_exists(self, conversation_id: str) -> bool:
        """Return True if the conversation has at least one stored message."""
        return self.get_message_count(conversation_id) > 0

    @property
    def backend(self) -> str:
        """Returns 'redis' or 'memory' indicating the active storage backend."""
        return "redis" if self._redis_ok else "memory"
