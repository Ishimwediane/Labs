import logging
from typing import Optional

from google import genai
from google.genai import types
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from app.config import get_settings
from app.providers.base import BaseAIProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    """
    Google Gemini provider implementation with retry logic using the new google-genai SDK.
    """

    def __init__(self):
        settings = get_settings()
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL
        self._provider_name = "gemini"

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @retry(
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
        Generate text using Google's new Generative AI SDK (google-genai).
        """
        logger.info(f"Attempting generation with {self.provider_name}...")

        try:
            config = types.GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
            
            if not response or not response.text:
                logger.warning("Gemini returned an empty response or was blocked.")
                return ""
                
            return response.text.strip()

        except Exception as e:
            logger.error(f"Gemini generation failed: {str(e)}")
            raise e
