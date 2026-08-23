"""
Google Gemini AI Provider for Deadlock Industrial Product Intelligence.
Handles API communication, attribute extraction, and schema-constrained LLM reasoning.
"""
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiProvider:
    """
    Direct client for Google Gemini API.
    Used for product intelligence, attribute extraction, normalization, and confidence scoring.
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL

    def is_configured(self) -> bool:
        """Checks if Gemini API key is configured."""
        return bool(self.api_key and self.api_key.strip() and self.api_key != "your_api_key_here")

    async def check_health(self) -> Dict[str, Any]:
        """
        Validates Gemini API configuration and connectivity.
        """
        if not self.is_configured():
            return {
                "provider": "gemini",
                "status": "unconfigured",
                "model": self.model,
                "message": "GEMINI_API_KEY is not set or using placeholder.",
            }

        url = f"{self.BASE_URL}/models/{self.model}?key={self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return {
                        "provider": "gemini",
                        "status": "healthy",
                        "model": self.model,
                        "message": "Gemini API connected successfully.",
                    }
                else:
                    return {
                        "provider": "gemini",
                        "status": "error",
                        "model": self.model,
                        "status_code": response.status_code,
                        "message": response.json().get("error", {}).get("message", "API request failed"),
                    }
        except Exception as exc:
            logger.exception(f"Gemini health check error: {exc}")
            return {
                "provider": "gemini",
                "status": "unreachable",
                "model": self.model,
                "message": str(exc),
            }

    async def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Sends structured prompt to Gemini API.
        """
        if not self.is_configured():
            raise ValueError("Gemini API key is not configured. Please set GEMINI_API_KEY in backend/.env.")

        url = f"{self.BASE_URL}/models/{self.model}:generateContent?key={self.api_key}"
        payload: Dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()


gemini_provider = GeminiProvider()
