import logging
from typing import Dict, List, Optional

from app.config import get_settings
from app.providers.base import BaseAIProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)


class ResilientAIService:
    """
    A service that provides resilient AI generation by falling back to 
    alternative providers if the primary one fails.
    """

    def __init__(self):
        self.settings = get_settings()
        self.providers: Dict[str, BaseAIProvider] = self._initialize_providers()
        self.provider_order: List[str] = self._build_provider_order()

        if not self.providers:
            logger.critical("No AI providers configured. Check your API keys.")
            raise RuntimeError("No AI providers available. Ensure at least one API key is set in .env")

    def _initialize_providers(self) -> Dict[str, BaseAIProvider]:
        """
        Initialize instances of available providers if their API keys are present.
        """
        available_providers = {}

        if self.settings.OPENAI_API_KEY and "your_openai_api_key_here" not in self.settings.OPENAI_API_KEY:
            try:
                available_providers["openai"] = OpenAIProvider()
                logger.info("OpenAI provider initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI provider: {e}")

        if self.settings.ANTHROPIC_API_KEY and "your_anthropic_api_key_here" not in self.settings.ANTHROPIC_API_KEY:
            try:
                available_providers["anthropic"] = AnthropicProvider()
                logger.info("Anthropic provider initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic provider: {e}")

        if self.settings.GEMINI_API_KEY and "your_gemini_api_key_here" not in self.settings.GEMINI_API_KEY:
            try:
                available_providers["gemini"] = GeminiProvider()
                logger.info("Gemini provider initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini provider: {e}")

        return available_providers

    def _build_provider_order(self) -> List[str]:
        """
        Build the order in which providers should be tried.
        The primary provider comes first, followed by others.
        """
        primary = self.settings.PRIMARY_PROVIDER
        all_available = list(self.providers.keys())

        order = []
        if primary in all_available:
            order.append(primary)
            for p in all_available:
                if p != primary:
                    order.append(p)
        else:
            # If primary is not available, just use whatever is left
            if all_available:
                logger.warning(f"Primary provider '{primary}' not available. Using fallback order.")
                order = all_available
            
        return order

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 300,
    ) -> str:
        """
        Generate text using the first available provider. 
        Falls back to other providers if one fails.
        """
        last_exception = None

        for provider_name in self.provider_order:
            provider = self.providers[provider_name]
            try:
                result = provider.generate(
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                logger.info(f"Successfully generated response using {provider_name}.")
                return result
            except Exception as e:
                logger.warning(f"Provider {provider_name} failed. Attempting fallback if possible. Error: {e}")
                last_exception = e
                continue

        # If we get here, all providers failed
        error_msg = f"All available AI providers ({', '.join(self.provider_order)}) failed to generate a response."
        logger.error(error_msg)
        raise RuntimeError(error_msg) from last_exception
