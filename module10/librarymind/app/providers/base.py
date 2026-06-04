from abc import ABC, abstractmethod
from typing import Optional


class BaseAIProvider(ABC):
    """
    Abstract base class for all AI providers.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """The name of the provider (e.g., 'openai', 'anthropic')."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 300,
    ) -> str:
        """
        Generate a text response based on a prompt and optional system message.
        """
        pass
