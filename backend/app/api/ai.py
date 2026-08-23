"""
AI router for Gemini health check and model status inspection.
"""
from typing import Any, Dict
from fastapi import APIRouter
from app.ai.gemini import gemini_provider

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/health", summary="Check Gemini AI provider health and connectivity")
async def get_ai_health() -> Dict[str, Any]:
    """
    Returns the status and health of the configured Google Gemini AI provider.
    """
    return await gemini_provider.check_health()
