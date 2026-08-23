"""
Google Gemini AI Provider implementation for Deadlock.
Utilizes the official google-genai Python SDK and structured JSON output.
"""
import asyncio
import json
import logging
from typing import Any, Dict, Optional, Type, TypeVar
from pydantic import BaseModel
from google import genai
from google.genai import types

from app.core.config import settings
from app.ai.provider import AIProvider

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class GeminiProvider(AIProvider):
    """
    Primary AI provider for Deadlock using official google-genai SDK.
    Supports native structured Pydantic response generation and controlled retries.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: Optional[int] = None,
        request_timeout: Optional[float] = None,
    ):
        self._api_key = settings.GEMINI_API_KEY if api_key is None else api_key
        self._model = model or settings.GEMINI_MODEL
        self._max_retries = max_retries or settings.GEMINI_MAX_RETRIES
        self._request_timeout = request_timeout or settings.GEMINI_REQUEST_TIMEOUT
        
        # Initialize client if API key is present
        self._client: Optional[genai.Client] = None
        if self.is_configured():
            try:
                self._client = genai.Client(api_key=self._api_key)
            except Exception as e:
                logger.error(f"Failed to initialize google-genai Client: {e}")

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    def is_configured(self) -> bool:
        return bool(
            self._api_key
            and self._api_key.strip()
            and self._api_key != "your_api_key_here"
            and not self._api_key.startswith("your_")
        )

    def _get_client(self) -> genai.Client:
        if not self.is_configured():
            raise ValueError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in backend/.env"
            )
        if self._client is None:
            self._client = genai.Client(api_key=self._api_key)
        return self._client

    async def health_check(self) -> Dict[str, Any]:
        """
        Validates Gemini API configuration and live connectivity.
        """
        if not self.is_configured():
            return {
                "provider": self.provider_name,
                "model": self.model_name,
                "status": "unconfigured",
                "message": "GEMINI_API_KEY is not configured or using placeholder.",
            }

        try:
            client = self._get_client()
            # Perform a lightweight metadata query or test call with timeout
            # Using asyncio.to_thread for synchronous SDK methods
            def _check():
                return client.models.get(model=self._model)

            await asyncio.wait_for(
                asyncio.to_thread(_check),
                timeout=10.0,
            )

            return {
                "provider": self.provider_name,
                "model": self.model_name,
                "status": "connected",
                "message": "Google Gemini API connected successfully.",
            }
        except Exception as exc:
            logger.warning(f"Gemini health check failure: {exc}")
            return {
                "provider": self.provider_name,
                "model": self.model_name,
                "status": "error",
                "message": f"Connection check failed: {str(exc)}",
            }

    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
    ) -> str:
        """
        Generates standard unstructured text response with exponential backoff.
        """
        client = self._get_client()
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
        )

        for attempt in range(1, self._max_retries + 1):
            try:
                def _call():
                    return client.models.generate_content(
                        model=self._model,
                        contents=prompt,
                        config=config,
                    )

                response = await asyncio.wait_for(
                    asyncio.to_thread(_call),
                    timeout=self._request_timeout,
                )
                return response.text or ""

            except Exception as exc:
                if attempt == self._max_retries:
                    logger.error(f"Gemini generate failed after {attempt} attempts: {exc}")
                    raise exc
                backoff = 2 ** attempt
                logger.warning(f"Gemini call attempt {attempt} failed ({exc}). Retrying in {backoff}s...")
                await asyncio.sleep(backoff)

        return ""

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
    ) -> T:
        """
        Generates response constrained to the given Pydantic schema using response_schema.
        """
        client = self._get_client()
        config = types.GenerateContentConfig(
            temperature=temperature,
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=response_schema,
        )

        for attempt in range(1, self._max_retries + 1):
            try:
                def _call():
                    return client.models.generate_content(
                        model=self._model,
                        contents=prompt,
                        config=config,
                    )

                response = await asyncio.wait_for(
                    asyncio.to_thread(_call),
                    timeout=self._request_timeout,
                )

                # If the SDK parsed the object directly
                if hasattr(response, "parsed") and response.parsed is not None:
                    if isinstance(response.parsed, response_schema):
                        return response.parsed
                    elif isinstance(response.parsed, dict):
                        return response_schema.model_validate(response.parsed)

                # Fallback to validating response.text JSON string
                raw_text = response.text
                if not raw_text:
                    raise ValueError("Gemini returned an empty response text.")

                data = json.loads(raw_text)
                return response_schema.model_validate(data)

            except Exception as exc:
                if attempt == self._max_retries:
                    logger.error(f"Gemini structured generation failed after {attempt} attempts: {exc}")
                    raise exc
                backoff = 2 ** attempt
                logger.warning(f"Gemini structured call attempt {attempt} failed ({exc}). Retrying in {backoff}s...")
                await asyncio.sleep(backoff)

        raise RuntimeError("Failed to generate structured response.")
