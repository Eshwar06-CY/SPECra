"""
Unit tests for Gemini Provider, caching, structured product extraction,
provenance, brand reconciliation, missing values, and intelligence services.
All LLM calls are mocked to ensure zero API quota usage and offline reliability.
"""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from app.ai.provider import AIProvider
from app.ai.schemas import (
    Provenance,
    ExtractionMethod,
    ProductAttribute,
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
    ProductConflict,
    SourceFieldValue,
    EvidenceCandidate,
)
from app.ai.gemini_provider import GeminiProvider
from app.ai.product_intelligence import (
    ProductIntelligenceEngine,
    compute_raw_data_hash,
)


class MockGeminiAIProvider(AIProvider):
    """Mock Gemini AI Provider for zero-quota isolated testing."""

    def __init__(self, structured_return: ProductIntelligence):
        self._return_val = structured_return
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return "gemini-2.5-flash"

    async def health_check(self):
        return {"provider": "gemini", "model": "gemini-2.5-flash", "status": "connected"}

    async def generate(self, prompt: str, system_instruction=None, temperature=0.1):
        return "mock text"

    async def generate_structured(self, prompt: str, response_schema, system_instruction=None, temperature=0.1):
        self.call_count += 1
        return self._return_val


class TestProductIntelligenceAI(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.sample_intel = ProductIntelligence(
            identity=ProductIdentity(
                product_type="Sanding Belt",
                product_name="Diablo 1/2 in. x 18 in. Sanding Belt 6-Pack",
                brand_name="Diablo",
                manufacturer_name="Freud Inc",
                manufacturer_part_number="DCB518ASTS06G",
                part_number="DCB518ASTS06G",
                brand_evidence=EvidenceCandidate(
                    source_location="Part_Desc",
                    source_text="Diablo",
                    provenance=Provenance.DIRECT,
                    confidence=1.0,
                ),
            ),
            summary="Industrial grade abrasive sanding belt pack for wood and metal.",
            features=[
                ProductFeature(
                    name="Pack Count",
                    value="6 Sanding Belts per pack",
                    provenance=Provenance.DIRECT,
                    confidence=0.98,
                )
            ],
            physical_specifications=PhysicalSpecifications(
                length="18",
                length_uom="in",
                width="0.5",
                width_uom="in",
            ),
            commerce=CommerceInfo(
                selling_quantity="6",
                selling_uom="Pack",
                standard_packaging_information="6 Belts per Pack",
            ),
            attributes=[
                ProductAttribute(
                    name="dimensions",
                    value="1/2\"x18\"",
                    normalized_value="0.5 in x 18.0 in",
                    unit="in",
                    original_value="1/2\"x18\"",
                    provenance=Provenance.DIRECT,
                    confidence=0.98,
                    evidence_text="1/2\"x18\"",
                    source_field="Part_Desc",
                    extraction_method=ExtractionMethod.LLM,
                ),
                ProductAttribute(
                    name="pack_quantity",
                    value="6",
                    normalized_value="6",
                    unit="pc",
                    original_value="6pc",
                    provenance=Provenance.DIRECT,
                    confidence=0.95,
                    evidence_text="6pc",
                    source_field="Part_Desc",
                    extraction_method=ExtractionMethod.LLM,
                ),
            ],
            missing_attributes=["grit", "backing_material", "abrasive_material"],
            conflicts=[
                ProductConflict(
                    field="brand",
                    conflicting_values=[
                        SourceFieldValue(source_field="E1_Brand", value="-- Unbranded --"),
                        SourceFieldValue(source_field="Unilog_Brand", value="-- No Unilog Brand --"),
                        SourceFieldValue(source_field="DIB_Brand", value="-- No DIB Brand --"),
                        SourceFieldValue(source_field="Part_Desc", value="Diablo"),
                    ],
                    sources=["E1_Brand", "Unilog_Brand", "DIB_Brand", "Part_Desc"],
                    resolution="Diablo",
                    explanation="Reconciled brand Diablo explicitly identified in Part_Desc despite placeholder catalog flags."
                )
            ],
            overall_confidence=0.96,
            reasoning="High confidence extraction from explicit part description."
        )

    async def test_product_intelligence_schema_validation(self):
        self.assertEqual(self.sample_intel.identity.product_type, "Sanding Belt")
        self.assertEqual(self.sample_intel.identity.brand_name, "Diablo")
        self.assertEqual(self.sample_intel.identity.manufacturer_name, "Freud Inc")
        self.assertEqual(len(self.sample_intel.features), 1)
        self.assertEqual(self.sample_intel.physical_specifications.length, "18")
        self.assertEqual(self.sample_intel.commerce.selling_quantity, "6")
        self.assertEqual(len(self.sample_intel.attributes), 2)
        self.assertEqual(self.sample_intel.attributes[0].provenance, Provenance.DIRECT)
        self.assertEqual(self.sample_intel.attributes[1].provenance, Provenance.DIRECT)
        self.assertEqual(len(self.sample_intel.missing_attributes), 3)
        self.assertEqual(self.sample_intel.conflicts[0].resolution, "Diablo")

    async def test_confidence_clamping(self):
        attr_high = ProductAttribute(
            name="test",
            value="100",
            confidence=1.5,  # should clamp to 1.0
        )
        self.assertEqual(attr_high.confidence, 1.0)

        attr_low = ProductAttribute(
            name="test",
            value="100",
            confidence=-0.5,  # should clamp to 0.0
        )
        self.assertEqual(attr_low.confidence, 0.0)

    async def test_product_caching(self):
        mock_provider = MockGeminiAIProvider(self.sample_intel)
        engine = ProductIntelligenceEngine(provider=mock_provider)

        raw_data = {
            "Mfg_Part_Num": "DCB518ASTS06G",
            "Part_Desc": "DCB518ASTS06G Diablo 1/2\"x18\" - Sanding Belt 6pc",
            "E1_Brand": "-- Unbranded --",
            "Unilog_Brand": "-- No Unilog Brand --",
            "DIB_Brand": "-- No DIB Brand --",
            "Part_Manuf": "Freud Inc (2435)"
        }

        # First call -> triggers provider
        res1 = await engine.analyze_product(raw_data, use_cache=True)
        self.assertEqual(mock_provider.call_count, 1)
        self.assertEqual(res1.identity.product_type, "Sanding Belt")

        # Second call with identical data -> hits in-memory cache, no provider call
        res2 = await engine.analyze_product(raw_data, use_cache=True)
        self.assertEqual(mock_provider.call_count, 1)
        self.assertEqual(res2.identity.brand_name, "Diablo")

    async def test_gemini_unconfigured_health_check(self):
        gemini = GeminiProvider(api_key="", model="gemini-2.5-flash")
        health = await gemini.health_check()
        self.assertEqual(health["status"], "unconfigured")
        self.assertEqual(health["provider"], "gemini")
        self.assertEqual(health["model"], "gemini-2.5-flash")

    async def test_gemini_provider_attributes(self):
        gemini = GeminiProvider(api_key="mock_key", model="gemini-2.5-flash")
        self.assertEqual(gemini.provider_name, "gemini")
        self.assertEqual(gemini.model_name, "gemini-2.5-flash")
        self.assertTrue(gemini.is_configured())

    def test_schema_developer_api_compatibility(self):
        """
        Verify that the Pydantic schema used for Gemini Developer API does not produce
        unsupported 'additionalProperties' fields anywhere in its derived JSON schema.
        """
        schema = ProductIntelligence.model_json_schema()
        
        def _check_no_additional_properties(d, path=""):
            if isinstance(d, dict):
                self.assertNotIn(
                    "additionalProperties",
                    d,
                    f"Unsupported 'additionalProperties' found at path: {path}"
                )
                for k, v in d.items():
                    _check_no_additional_properties(v, f"{path}.{k}" if path else k)
            elif isinstance(d, list):
                for i, item in enumerate(d):
                    _check_no_additional_properties(item, f"{path}[{i}]")

        _check_no_additional_properties(schema)

    def test_deterministic_brand_reconciliation_from_desc(self):
        """Test 1: Brand extracted from Part_Desc with DIRECT provenance"""
        from app.ai.reconciliation import reconcile_product_intelligence
        intel = ProductIntelligence(
            identity=ProductIdentity(
                brand_name="Acme",
            )
        )
        raw_data = {
            "Part_Desc": "ABC123 Acme 10mm Valve",
            "E1_Brand": "-- Unbranded --",
        }
        reconciled = reconcile_product_intelligence(intel, raw_data)
        self.assertEqual(reconciled.identity.brand_name, "Acme")
        self.assertIsNotNone(reconciled.identity.brand_evidence)
        self.assertEqual(reconciled.identity.brand_evidence.provenance, Provenance.DIRECT)
        self.assertEqual(reconciled.identity.brand_evidence.source_location, "Part_Desc")

    def test_deterministic_placeholder_brand_handling(self):
        """Test 2: Placeholder brand fields do not override explicit description brand"""
        from app.ai.reconciliation import reconcile_product_intelligence
        intel = ProductIntelligence(
            identity=ProductIdentity()
        )
        raw_data = {
            "Part_Desc": "DCB518ASTS06G Diablo 1/2x18 Sanding Belt",
            "E1_Brand": "-- Unbranded --",
            "Unilog_Brand": "-- No Unilog Brand --",
            "DIB_Brand": "-- No DIB Brand --",
        }
        # If Gemini proposed Diablo
        intel.identity.brand_name = "Diablo"
        reconciled = reconcile_product_intelligence(intel, raw_data)
        self.assertEqual(reconciled.identity.brand_name, "Diablo")
        self.assertEqual(reconciled.identity.brand_evidence.provenance, Provenance.DIRECT)
        self.assertEqual(reconciled.identity.brand_evidence.source_location, "Part_Desc")

    def test_deterministic_manufacturer_from_raw_field(self):
        """Test 3: Manufacturer deterministically mapped from Part_Manuf with DIRECT provenance"""
        from app.ai.reconciliation import reconcile_product_intelligence
        intel = ProductIntelligence()
        raw_data = {
            "Part_Manuf": "Freud Inc (2435)",
            "Part_Desc": "DCB518ASTS06G Sanding Belt",
        }
        reconciled = reconcile_product_intelligence(intel, raw_data)
        self.assertEqual(reconciled.identity.manufacturer_name, "Freud Inc (2435)")
        self.assertIsNotNone(reconciled.identity.manufacturer_evidence)
        self.assertEqual(reconciled.identity.manufacturer_evidence.provenance, Provenance.DIRECT)
        self.assertEqual(reconciled.identity.manufacturer_evidence.source_location, "Part_Manuf")

    def test_deterministic_manufacturer_part_number(self):
        """Test 4: MPN mapped from Mfg_Part_Num with DIRECT provenance"""
        from app.ai.reconciliation import reconcile_product_intelligence
        intel = ProductIntelligence()
        raw_data = {
            "Mfg_Part_Num": "ABC123",
        }
        reconciled = reconcile_product_intelligence(intel, raw_data)
        self.assertEqual(reconciled.identity.manufacturer_part_number, "ABC123")
        self.assertEqual(reconciled.identity.part_number_evidence.provenance, Provenance.DIRECT)
        self.assertEqual(reconciled.identity.part_number_evidence.source_location, "Mfg_Part_Num")

    def test_deterministic_pack_quantity_provenance(self):
        """Test 5: Explicit '6pc' in description forces DIRECT provenance for pack_quantity"""
        from app.ai.reconciliation import reconcile_product_intelligence
        intel = ProductIntelligence(
            attributes=[
                ProductAttribute(
                    name="pack_quantity",
                    value="6",
                    normalized_value="6",
                    unit="pc",
                    provenance=Provenance.INFERRED,  # LLM erroneously called it INFERRED
                )
            ]
        )
        raw_data = {
            "Part_Desc": "Product XYZ 6pc",
        }
        reconciled = reconcile_product_intelligence(intel, raw_data)
        attr = reconciled.attributes[0]
        self.assertEqual(attr.provenance, Provenance.DIRECT)
        self.assertEqual(attr.source_field, "Part_Desc")
        self.assertEqual(attr.evidence_text, "6pc")
        self.assertEqual(attr.evidence.provenance, Provenance.DIRECT)

    def test_unsupported_claim_downgraded_from_direct(self):
        """Test 6: Hallucinated DIRECT claim with no matching raw text is downgraded to INFERRED"""
        from app.ai.reconciliation import reconcile_product_intelligence
        intel = ProductIntelligence(
            attributes=[
                ProductAttribute(
                    name="material",
                    value="Titanium",
                    provenance=Provenance.DIRECT,  # LLM falsely claimed DIRECT
                )
            ]
        )
        raw_data = {
            "Part_Desc": "Plastic Valve 10mm",
        }
        reconciled = reconcile_product_intelligence(intel, raw_data)
        attr = reconciled.attributes[0]
        self.assertEqual(attr.provenance, Provenance.INFERRED)
        self.assertEqual(attr.evidence.provenance, Provenance.INFERRED)

    def test_feature_deduplication_against_structured_attributes(self):
        """Test 7: Features that duplicate structured attributes are deduplicated"""
        from app.ai.reconciliation import reconcile_product_intelligence
        intel = ProductIntelligence(
            attributes=[
                ProductAttribute(
                    name="width",
                    value="1/2 in",
                    normalized_value="0.5",
                    unit="in",
                    extraction_method=ExtractionMethod.DETERMINISTIC,
                ),
                ProductAttribute(
                    name="length",
                    value="18 in",
                    normalized_value="18.0",
                    unit="in",
                    extraction_method=ExtractionMethod.DETERMINISTIC,
                ),
                ProductAttribute(
                    name="pack_quantity",
                    value="6 pieces",
                    normalized_value="6",
                    unit="pieces",
                    extraction_method=ExtractionMethod.DETERMINISTIC,
                ),
            ],
            features=[
                ProductFeature(
                    name="dimensions",
                    value="1/2 in width by 18 in length",
                ),
                ProductFeature(
                    name="pack_quantity",
                    value="Includes 6 sanding belts per pack",
                ),
                ProductFeature(
                    name="durability",
                    value="Heavy-duty cloth backing for extended life",
                ),
            ]
        )
        raw_data = {
            "Part_Desc": "DCB518ASTS06G Diablo 1/2\"x18\" Sanding Belt 6pc Heavy-duty cloth backing",
        }
        reconciled = reconcile_product_intelligence(intel, raw_data)
        
        # Verify structured attributes remain authoritative
        attr_names = [a.name for a in reconciled.attributes]
        self.assertIn("width", attr_names)
        self.assertIn("length", attr_names)
        self.assertIn("pack_quantity", attr_names)

        # Verify duplicate features were removed, but distinct features preserved
        feat_names = [f.name for f in reconciled.features]
        self.assertNotIn("dimensions", feat_names)
        self.assertNotIn("pack_quantity", feat_names)
        self.assertIn("durability", feat_names)

    def test_model_metadata_comes_from_configuration(self):
        """Test 8: Model configuration reflects settings.GEMINI_MODEL rather than hardcoded string"""
        from app.core.config import settings
        from app.ai.gemini_provider import GeminiProvider
        provider = GeminiProvider(api_key="test_key")
        self.assertEqual(provider.model_name, settings.GEMINI_MODEL)
        self.assertTrue(settings.GEMINI_MODEL.startswith("gemini-"))

    def test_classify_ai_exception_503(self):
        """Test 9: 503 High Demand / Unavailable is classified as provider_unavailable"""
        from app.services.intelligence_service import classify_ai_exception
        exc = Exception("503 UNAVAILABLE: This model is currently experiencing high demand. Spikes in demand are usually temporary.")
        category, msg = classify_ai_exception(exc)
        self.assertEqual(category, "provider_unavailable")
        self.assertIn("503", msg)

    def test_classify_ai_exception_429(self):
        """Test 10: 429 Quota / Rate limit is classified as rate_limit"""
        from app.services.intelligence_service import classify_ai_exception
        exc = Exception("429 RESOURCE_EXHAUSTED: Quota exceeded for quota metric 'GenerateContent'")
        category, msg = classify_ai_exception(exc)
        self.assertEqual(category, "rate_limit")
        self.assertIn("429", msg)

    def test_classify_ai_exception_timeout(self):
        """Test 11: TimeoutError is classified as timeout"""
        import asyncio
        from app.services.intelligence_service import classify_ai_exception
        exc = asyncio.TimeoutError()
        category, msg = classify_ai_exception(exc)
        self.assertEqual(category, "timeout")

    def test_normalize_and_clean_product_removes_duplicates(self):
        """Test 12: normalize_and_clean_product removes redundant feature rows from DB"""
        import uuid
        from app.core.database import SessionLocal
        from app.models.product import Product, ProductAttribute, Evidence
        from app.services.intelligence_service import IntelligenceService
        from app.core.config import settings

        db = SessionLocal()
        test_prod = Product(
            id=uuid.uuid4(),
            product_name="Test Belt",
            category="Abrasives",
            raw_data={"Part_Desc": "Test Belt 18in 1/2in 6pc"},
        )
        db.add(test_prod)
        db.flush()

        # Add structured attributes
        attr_width = ProductAttribute(
            product_id=test_prod.id,
            attribute_name="width",
            attribute_value="1/2 in",
            extraction_method="DETERMINISTIC",
        )
        attr_length = ProductAttribute(
            product_id=test_prod.id,
            attribute_name="length",
            attribute_value="18 in",
            extraction_method="DETERMINISTIC",
        )
        attr_qty = ProductAttribute(
            product_id=test_prod.id,
            attribute_name="pack_quantity",
            attribute_value="6 pieces",
            extraction_method="DETERMINISTIC",
        )
        # Add redundant features
        feat_dim = ProductAttribute(
            product_id=test_prod.id,
            attribute_name="feature_dimensions",
            attribute_value="1/2 in width by 18 in length",
            extraction_method="LLM",
        )
        feat_qty = ProductAttribute(
            product_id=test_prod.id,
            attribute_name="feature_pack_quantity",
            attribute_value="Includes 6 sanding belts",
            extraction_method="LLM",
        )
        # Add legitimate feature
        feat_dur = ProductAttribute(
            product_id=test_prod.id,
            attribute_name="feature_durability",
            attribute_value="Industrial strength",
            extraction_method="LLM",
        )

        db.add_all([attr_width, attr_length, attr_qty, feat_dim, feat_qty, feat_dur])
        db.flush()

        # Add evidence with old model note
        ev = Evidence(
            product_id=test_prod.id,
            attribute_id=attr_width.id,
            source_name="test.csv",
            source_type="input_dataset",
            source_location="Part_Desc",
            source_text="1/2in",
            evidence_metadata={"notes": "Extracted via Gemini Intelligence Engine (gemini-3.6-flash)"},
        )
        db.add(ev)
        db.commit()

        # Run normalization
        IntelligenceService.normalize_and_clean_product(db, test_prod.id)

        # Inspect details
        details = IntelligenceService.get_product_intelligence_details(db, test_prod.id)
        self.assertEqual(details["total_attributes"], 3)
        self.assertEqual(len(details["features"]), 1)
        self.assertEqual(details["features"][0]["name"], "Durability")
        self.assertIn(settings.GEMINI_MODEL, details["evidence"][0]["metadata"]["notes"])

        # Clean up test DB record
        db.delete(test_prod)
        db.commit()
        db.close()


if __name__ == "__main__":
    unittest.main()
