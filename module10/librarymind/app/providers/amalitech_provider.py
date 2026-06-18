import logging
from typing import Optional

from openai import OpenAI, APIError, RateLimitError, APIConnectionError
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


class AmalitechProvider(BaseAIProvider):
    """
    AmaliTech API provider implementation that acts as a proxy to OpenAI/Anthropic.
    """

    def __init__(self):
        settings = get_settings()
        
        self.client = OpenAI(
            api_key=settings.AMALITECH_API_KEY,
            base_url="https://ai-api.amalitech.org/api/v2/public/v1",
            default_headers={"Provider": "openai", "X-Api-Key": settings.AMALITECH_API_KEY}
        )
        self.model = settings.AMALITECH_MODEL
        self._provider_name = "amalitech"

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIConnectionError, APIError)),
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
        Generate text using AmaliTech's proxy API.
        """
        logger.info(f"Attempting generation with {self.provider_name}...")
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content
            return content.strip() if content else ""
            
        except Exception as e:
            logger.error(f"AmaliTech generation failed: {str(e)}")
            raise e
