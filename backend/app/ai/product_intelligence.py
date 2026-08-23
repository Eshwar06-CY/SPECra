"""
Product Intelligence Engine module for Deadlock.
Orchestrates AI reasoning, prompt construction, structured extraction, caching, and confidence validation using Google Gemini.
"""
import hashlib
import json
import logging
from typing import Any, Dict, Optional

from app.core.config import settings
from app.ai.provider import AIProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.schemas import ProductIntelligence
from app.ai.prompts import PRODUCT_INTELLIGENCE_SYSTEM_INSTRUCTION, build_product_analysis_prompt

logger = logging.getLogger(__name__)

# In-memory deterministic product cache (hash(raw_data) -> ProductIntelligence)
_INTELLIGENCE_CACHE: Dict[str, ProductIntelligence] = {}


def compute_raw_data_hash(raw_data: Dict[str, Any]) -> str:
    """Computes a deterministic MD5 hash for a dictionary of raw product fields."""
    serialized = json.dumps(raw_data, sort_keys=True, default=str)
    return hashlib.md5(serialized.encode("utf-8")).hexdigest()


def get_ai_provider() -> AIProvider:
    """
    Returns the configured GeminiProvider for Deadlock.
    """
    return GeminiProvider()


class ProductIntelligenceEngine:
    """
    Core AI reasoning engine for extracting structured industrial specifications from raw product data using Gemini.
    """

    def __init__(self, provider: Optional[AIProvider] = None):
        self.provider = provider or get_ai_provider()

    async def analyze_product(
        self,
        raw_data: Dict[str, Any],
        use_cache: bool = True,
    ) -> ProductIntelligence:
        """
        Runs semantic extraction, classification, attribute discovery, and conflict analysis
        for a single product row.
        """
        # 1. Check in-memory deterministic cache
        cache_key = compute_raw_data_hash(raw_data)
        if use_cache and cache_key in _INTELLIGENCE_CACHE:
            logger.debug(f"Cache hit for product hash: {cache_key}")
            return _INTELLIGENCE_CACHE[cache_key]

        # 2. Build structured prompt
        prompt = build_product_analysis_prompt(raw_data)

        # 3. Call Gemini AI Provider for structured Pydantic output
        intelligence: ProductIntelligence = await self.provider.generate_structured(
            prompt=prompt,
            response_schema=ProductIntelligence,
            system_instruction=PRODUCT_INTELLIGENCE_SYSTEM_INSTRUCTION,
            temperature=0.1,
        )

        # 4. Deterministic Provenance & Evidence Validation and Brand Reconciliation
        from app.ai.provenance_validator import ProvenanceValidator
        intelligence = ProvenanceValidator.validate_and_enrich_canonical_product(
            canonical=intelligence,
            raw_data=raw_data,
        )

        # 5. Save into cache
        if use_cache:
            _INTELLIGENCE_CACHE[cache_key] = intelligence

        return intelligence
