"""
AI package exports for Deadlock.
"""
from app.ai.provider import AIProvider
from app.ai.gemini_provider import GeminiProvider
from app.ai.schemas import (
    Provenance,
    ExtractionMethod,
    Evidence,
    EvidenceCandidate,
    SourceFieldValue,
    ProductConflict,
    ProductAttribute as AIProductAttribute,
    ProductFeature,
    ProductIdentity,
    ProductDescriptions,
    ProductClassification,
    PhysicalSpecifications,
    CommerceInfo,
    DigitalAssets,
    ProductMetadata,
    CanonicalProduct,
    ProductIntelligence,
)
from app.ai.prompts import (
    PRODUCT_INTELLIGENCE_SYSTEM_INSTRUCTION,
    build_product_analysis_prompt,
)
from app.ai.product_intelligence import (
    ProductIntelligenceEngine,
    get_ai_provider,
    compute_raw_data_hash,
)

__all__ = [
    "AIProvider",
    "GeminiProvider",
    "Provenance",
    "ExtractionMethod",
    "Evidence",
    "EvidenceCandidate",
    "SourceFieldValue",
    "ProductConflict",
    "AIProductAttribute",
    "ProductFeature",
    "ProductIdentity",
    "ProductDescriptions",
    "ProductClassification",
    "PhysicalSpecifications",
    "CommerceInfo",
    "DigitalAssets",
    "ProductMetadata",
    "CanonicalProduct",
    "ProductIntelligence",
    "PRODUCT_INTELLIGENCE_SYSTEM_INSTRUCTION",
    "build_product_analysis_prompt",
    "ProductIntelligenceEngine",
    "get_ai_provider",
    "compute_raw_data_hash",
]
