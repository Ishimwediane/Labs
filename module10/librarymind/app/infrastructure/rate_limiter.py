import time
import logging
import threading
from app.config import get_settings

logger = logging.getLogger(__name__)

class RateLimitExceededError(Exception):
    """Exception raised when the rate limit is exceeded."""
    pass

class TokenBucketRateLimiter:
    """
    A thread-safe token-bucket rate limiter.
    Limits the number of requests based on RATE_LIMIT_PER_MINUTE.
    """

    def __init__(self):
        settings = get_settings()
        self.rate_limit = settings.RATE_LIMIT_PER_MINUTE
        self.capacity = self.rate_limit
        self.tokens = float(self.capacity)
        self.fill_rate = self.rate_limit / 60.0  # tokens per second
        
        self.last_refill_time = time.time()
        self.lock = threading.Lock()
        
        logger.info(f"Rate Limiter initialized: {self.rate_limit} requests/minute")

    def _refill(self) -> None:
        """
        Add tokens to the bucket based on elapsed time.
        Called automatically by acquire().
        """
        now = time.time()
        elapsed = now - self.last_refill_time
        
        added_tokens = elapsed * self.fill_rate
        if added_tokens > 0:
            self.tokens = min(self.capacity, self.tokens + added_tokens)
            self.last_refill_time = now
            logger.debug(f"Refilled tokens. Current balance: {self.tokens:.2f}")

    def acquire(self) -> None:
        """
        Consume one token from the bucket.
        Raises RateLimitExceededError if no tokens are available.
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                logger.info(f"Token acquired. Remaining: {int(self.tokens)}")
            else:
                logger.warning("Rate limit exceeded. No tokens available.")
                raise RateLimitExceededError("Rate limit exceeded. Please try again later.")
