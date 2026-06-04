import logging
from typing import Optional

from anthropic import Anthropic, APIStatusError, APITimeoutError, RateLimitError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from app.config import get_settings
from app.providers.base import BaseAIProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseAIProvider):
    """
    Anthropic provider implementation with retry logic.
    """

    def __init__(self):
        settings = get_settings()
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.ANTHROPIC_MODEL
        self._provider_name = "anthropic"

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIStatusError, APITimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 300,
    ) -> str:
        """
        Generate text using Anthropic's Messages API.
        """
        logger.info(f"Attempting generation with {self.provider_name}...")

        try:
            kwargs = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if system:
                kwargs["system"] = system

            response = self.client.messages.create(**kwargs)
            return response.content[0].text.strip()

        except Exception as e:
            logger.error(f"Anthropic generation failed: {str(e)}")
            raise e
