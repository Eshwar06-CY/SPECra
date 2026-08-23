"""
Abstract base class and interface for AI Providers in Deadlock.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class AIProvider(ABC):
    """
    Abstract AI provider contract supporting plain generation, structured Pydantic extraction,
    and health status inspection.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'gemini')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the configured model."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Inspects provider configuration and network connectivity.
        Returns standard dictionary with provider, model, status, and details.
        """
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
    ) -> str:
        """
        Generates standard text completion for a given prompt.
        """
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        """
        Generates structured output strictly validated against the given Pydantic schema class.
        """
        pass
