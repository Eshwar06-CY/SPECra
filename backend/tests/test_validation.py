"""
Unit tests for the Deadlock Deterministic Product Validation Engine.
Runs 100% offline without calling any LLM API.
"""
import unittest
import uuid
from typing import Dict, Any

from app.models.product import Product, ProductAttribute, Evidence, ValidationResult
from app.services.validation_engine import (
    ProductValidationEngine,
    ValidationSeverity,
    ValidationStatus,
    ValidationIssue,
)
from app.services.validation_service import ValidationService
from app.core.database import SessionLocal


class TestProductValidationEngine(unittest.TestCase):
    """
    Comprehensive offline test suite for ProductValidationEngine.
    """

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_completely_valid_product(self):
        """Test 1: Completely valid product passes with score >= 90 (PASSED)"""
        product = Product(
            id=uuid.uuid4(),
            external_product_id="DCB518ASTS06G",
            product_name="Diablo 1/2 in x 18 in Sanding Belt 6pc",
            category="Sanding Belt",
            raw_data={"Mfg_Part_Num": "DCB518ASTS06G", "Part_Desc": "Diablo Sanding Belt 6pc", "Part_Manuf": "Freud Inc"},
        )
        # Add attributes with evidence
        attr_brand = ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="brand", attribute_value="Diablo", confidence_score=1.0, extraction_method="DETERMINISTIC")
        ev_brand = Evidence(product_id=product.id, attribute_id=attr_brand.id, source_name="test.csv", source_type="csv", source_location="Part_Desc", source_text="Diablo", evidence_metadata={"provenance": "DIRECT"})
        attr_brand.evidences = [ev_brand]

        attr_manuf = ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="manufacturer", attribute_value="Freud Inc", confidence_score=1.0, extraction_method="DETERMINISTIC")
        ev_manuf = Evidence(product_id=product.id, attribute_id=attr_manuf.id, source_name="test.csv", source_type="csv", source_location="Part_Manuf", source_text="Freud Inc", evidence_metadata={"provenance": "DIRECT"})
        attr_manuf.evidences = [ev_manuf]

        attr_width = ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="width", attribute_value="1/2 in", normalized_value="0.5", unit="in", confidence_score=1.0, extraction_method="DETERMINISTIC")
        ev_width = Evidence(product_id=product.id, attribute_id=attr_width.id, source_name="test.csv", source_type="csv", source_location="Part_Desc", source_text="1/2 in", evidence_metadata={"provenance": "DIRECT"})
        attr_width.evidences = [ev_width]

        attr_len = ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="length", attribute_value="18 in", normalized_value="18.0", unit="in", confidence_score=1.0, extraction_method="DETERMINISTIC")
        ev_len = Evidence(product_id=product.id, attribute_id=attr_len.id, source_name="test.csv", source_type="csv", source_location="Part_Desc", source_text="18 in", evidence_metadata={"provenance": "DIRECT"})
        attr_len.evidences = [ev_len]

        attr_qty = ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="pack_quantity", attribute_value="6 pieces", normalized_value="6", unit="pieces", confidence_score=1.0, extraction_method="DETERMINISTIC")
        ev_qty = Evidence(product_id=product.id, attribute_id=attr_qty.id, source_name="test.csv", source_type="csv", source_location="Part_Desc", source_text="6pc", evidence_metadata={"provenance": "DIRECT"})
        attr_qty.evidences = [ev_qty]

        product.attributes = [attr_brand, attr_manuf, attr_width, attr_len, attr_qty]

        report = ProductValidationEngine.validate_product(product)
        self.assertEqual(report.status, ValidationStatus.PASSED)
        self.assertEqual(report.score, 100.0)
        self.assertEqual(report.errors, 0)
        self.assertEqual(report.warnings, 0)

    def test_missing_manufacturer_warning(self):
        """Test 2: Missing manufacturer generates INCOMPLETE_IDENTITY warning"""
        product = Product(
            id=uuid.uuid4(),
            external_product_id="DCB518ASTS06G",
            product_name="Sanding Belt 6pc",
            category="Sanding Belt",
            raw_data={"Mfg_Part_Num": "DCB518ASTS06G"},
        )
        product.attributes = []
        report = ProductValidationEngine.validate_product(product)
        types = [r.validation_type for r in report.results]
        self.assertIn("INCOMPLETE_IDENTITY", types)
        # Manufacturer is warning (-7)
        manuf_issue = next(r for r in report.results if r.field == "manufacturer")
        self.assertEqual(manuf_issue.severity, ValidationSeverity.WARNING)

    def test_missing_mpn_error(self):
        """Test 3: Missing MPN produces MISSING_REQUIRED_FIELD ERROR"""
        product = Product(
            id=uuid.uuid4(),
            external_product_id=None,
            product_name="Generic Sanding Belt",
            category="Sanding Belt",
            raw_data={},
        )
        product.attributes = []
        report = ProductValidationEngine.validate_product(product)
        mpn_issue = next((r for r in report.results if r.field == "manufacturer_part_number"), None)
        self.assertIsNotNone(mpn_issue)
        self.assertEqual(mpn_issue.severity, ValidationSeverity.ERROR)
        self.assertEqual(mpn_issue.validation_type, "MISSING_REQUIRED_FIELD")

    def test_missing_evidence_error(self):
        """Test 4: Attribute without evidence generates MISSING_EVIDENCE ERROR"""
        product = Product(
            id=uuid.uuid4(),
            external_product_id="PN123",
            product_name="Product",
            category="Tools",
            raw_data={"Mfg_Part_Num": "PN123"},
        )
        attr = ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="voltage", attribute_value="120V", confidence_score=0.95)
        attr.evidences = []  # No evidence
        product.attributes = [attr]

        report = ProductValidationEngine.validate_product(product)
        ev_issue = next((r for r in report.results if r.validation_type == "MISSING_EVIDENCE"), None)
        self.assertIsNotNone(ev_issue)
        self.assertEqual(ev_issue.severity, ValidationSeverity.ERROR)

    def test_invalid_confidence_range(self):
        """Test 5: Confidence outside 0.0-1.0 produces INVALID_CONFIDENCE_RANGE ERROR"""
        product = Product(
            id=uuid.uuid4(),
            external_product_id="PN123",
            product_name="Product",
            category="Tools",
        )
        attr = ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="grit", attribute_value="80", confidence_score=1.5)
        attr.evidences = [Evidence(product_id=product.id, attribute_id=attr.id, source_name="s", source_type="s", source_location="l", source_text="80", evidence_metadata={"provenance": "DIRECT"})]
        product.attributes = [attr]

        report = ProductValidationEngine.validate_product(product)
        conf_issue = next((r for r in report.results if r.validation_type == "INVALID_CONFIDENCE_RANGE"), None)
        self.assertIsNotNone(conf_issue)
        self.assertEqual(conf_issue.severity, ValidationSeverity.ERROR)

    def test_low_confidence_thresholds(self):
        """Test 6: Confidence < 0.70 produces WARNING, < 0.50 produces ERROR"""
        product = Product(id=uuid.uuid4(), external_product_id="PN123", product_name="Product", category="Tools")
        
        # Marginal confidence 0.65 -> WARNING
        attr_warn = ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="grit", attribute_value="80", confidence_score=0.65)
        attr_warn.evidences = [Evidence(product_id=product.id, attribute_id=attr_warn.id, source_name="s", source_type="s", source_location="l", source_text="80", evidence_metadata={"provenance": "DIRECT"})]

        # Critical confidence 0.35 -> ERROR
        attr_err = ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="material", attribute_value="Steel", confidence_score=0.35)
        attr_err.evidences = [Evidence(product_id=product.id, attribute_id=attr_err.id, source_name="s", source_type="s", source_location="l", source_text="Steel", evidence_metadata={"provenance": "DIRECT"})]

        product.attributes = [attr_warn, attr_err]
        report = ProductValidationEngine.validate_product(product)

        grit_issue = next(r for r in report.results if r.field == "grit")
        self.assertEqual(grit_issue.severity, ValidationSeverity.WARNING)

        mat_issue = next(r for r in report.results if r.field == "material")
        self.assertEqual(mat_issue.severity, ValidationSeverity.ERROR)

    def test_duplicate_attribute_warning(self):
        """Test 7: Duplicate attributes with identical values produce DUPLICATE_ATTRIBUTE WARNING"""
        product = Product(id=uuid.uuid4(), external_product_id="PN123", product_name="Product", category="Tools")
        attr1 = ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="width", attribute_value="1/2 in", confidence_score=0.95)
        attr1.evidences = [Evidence(product_id=product.id, attribute_id=attr1.id, source_name="s", source_type="s", source_location="l", source_text="1/2 in", evidence_metadata={"provenance": "DIRECT"})]
        attr2 = ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="width", attribute_value="1/2 in", confidence_score=0.95)
        attr2.evidences = [Evidence(product_id=product.id, attribute_id=attr2.id, source_name="s", source_type="s", source_location="l", source_text="1/2 in", evidence_metadata={"provenance": "DIRECT"})]
        product.attributes = [attr1, attr2]

        report = ProductValidationEngine.validate_product(product)
        dup_issue = next((r for r in report.results if r.validation_type == "DUPLICATE_ATTRIBUTE"), None)
        self.assertIsNotNone(dup_issue)
        self.assertEqual(dup_issue.severity, ValidationSeverity.WARNING)

    def test_conflicting_value_error(self):
        """Test 8: Conflicting attribute values produce CONFLICTING_VALUE ERROR"""
        product = Product(id=uuid.uuid4(), external_product_id="PN123", product_name="Product", category="Tools")
        attr1 = ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="width", attribute_value="1/2 in", confidence_score=0.95)
        attr1.evidences = [Evidence(product_id=product.id, attribute_id=attr1.id, source_name="s", source_type="s", source_location="l", source_text="1/2 in", evidence_metadata={"provenance": "DIRECT"})]
        attr2 = ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="width", attribute_value="3/4 in", confidence_score=0.95)
        attr2.evidences = [Evidence(product_id=product.id, attribute_id=attr2.id, source_name="s", source_type="s", source_location="l", source_text="3/4 in", evidence_metadata={"provenance": "DIRECT"})]
        product.attributes = [attr1, attr2]

        report = ProductValidationEngine.validate_product(product)
        conflict_issue = next((r for r in report.results if r.validation_type == "CONFLICTING_VALUE"), None)
        self.assertIsNotNone(conflict_issue)
        self.assertEqual(conflict_issue.severity, ValidationSeverity.ERROR)

    def test_invalid_unit_error(self):
        """Test 9: Invalid or unrecognized unit produces INVALID_UNIT ERROR"""
        product = Product(id=uuid.uuid4(), external_product_id="PN123", product_name="Product", category="Tools")
        attr = ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="length", attribute_value="18 bananas", normalized_value="18", unit="bananas", confidence_score=0.95)
        attr.evidences = [Evidence(product_id=product.id, attribute_id=attr.id, source_name="s", source_type="s", source_location="l", source_text="18 bananas", evidence_metadata={"provenance": "DIRECT"})]
        product.attributes = [attr]

        report = ProductValidationEngine.validate_product(product)
        unit_issue = next((r for r in report.results if r.validation_type == "INVALID_UNIT"), None)
        self.assertIsNotNone(unit_issue)
        self.assertEqual(unit_issue.severity, ValidationSeverity.ERROR)

    def test_valid_physical_measurements_pass(self):
        """Test 10: Valid width/length/pack_quantity attributes pass with no unit or normalization errors"""
        product = Product(id=uuid.uuid4(), external_product_id="PN123", product_name="Product", category="Tools")
        attr1 = ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="width", attribute_value="1/2 in", normalized_value="0.5", unit="in", confidence_score=1.0)
        attr1.evidences = [Evidence(product_id=product.id, attribute_id=attr1.id, source_name="s", source_type="s", source_location="l", source_text="1/2 in", evidence_metadata={"provenance": "DIRECT"})]
        attr2 = ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="length", attribute_value="18 in", normalized_value="18", unit="in", confidence_score=1.0)
        attr2.evidences = [Evidence(product_id=product.id, attribute_id=attr2.id, source_name="s", source_type="s", source_location="l", source_text="18 in", evidence_metadata={"provenance": "DIRECT"})]
        attr3 = ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="pack_quantity", attribute_value="6 pieces", normalized_value="6", unit="pieces", confidence_score=1.0)
        attr3.evidences = [Evidence(product_id=product.id, attribute_id=attr3.id, source_name="s", source_type="s", source_location="l", source_text="6pc", evidence_metadata={"provenance": "DIRECT"})]
        product.attributes = [attr1, attr2, attr3]

        report = ProductValidationEngine.validate_product(product)
        unit_or_norm_issues = [r for r in report.results if r.validation_type in {"INVALID_UNIT", "INVALID_NORMALIZATION"}]
        self.assertEqual(len(unit_or_norm_issues), 0)

    def test_unbranded_sentinel_does_not_fail_as_error(self):
        """Test 11: Explicit unbranded sentinel in raw dataset creates INFO, not ERROR"""
        product = Product(
            id=uuid.uuid4(),
            external_product_id="PN123",
            product_name="Diablo Sanding Belt",
            category="Sanding Belt",
            raw_data={"E1_Brand": "-- Unbranded --", "Part_Manuf": "Freud Inc"},
        )
        product.attributes = [
            ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="manufacturer", attribute_value="Freud Inc", confidence_score=1.0, evidences=[Evidence(product_id=product.id, source_name="s", source_type="s", source_location="l", source_text="Freud Inc", evidence_metadata={"provenance": "DIRECT"})])
        ]
        report = ProductValidationEngine.validate_product(product)
        brand_issue = next((r for r in report.results if r.field == "brand"), None)
        self.assertIsNotNone(brand_issue)
        self.assertEqual(brand_issue.severity, ValidationSeverity.INFO)
        self.assertEqual(brand_issue.validation_type, "UNBRANDED_CATALOG_ITEM")

    def test_quality_score_calculation(self):
        """Test 12: Quality score deductions (-20 error, -7 warning, -2 info) and clamping"""
        # Baseline = 100
        # 1 error (-20) + 1 warning (-7) + 1 info (-2) = 71.0 -> 'warning'
        issues = [
            ValidationIssue(validation_type="ERR", severity=ValidationSeverity.ERROR, field="f1", message="m"),
            ValidationIssue(validation_type="WARN", severity=ValidationSeverity.WARNING, field="f2", message="m"),
            ValidationIssue(validation_type="INF", severity=ValidationSeverity.INFO, field="f3", message="m"),
        ]
        score, status, errs, warns, infos = ProductValidationEngine.calculate_quality_score(issues)
        self.assertEqual(score, 71.0)
        self.assertEqual(status, ValidationStatus.WARNING)
        self.assertEqual(errs, 1)
        self.assertEqual(warns, 1)
        self.assertEqual(infos, 1)

        # Clamping test: 6 errors (-120) -> score = 0.0, status = 'failed'
        severe_issues = [ValidationIssue(validation_type="ERR", severity=ValidationSeverity.ERROR, field=f"f{i}", message="m") for i in range(6)]
        score_clamp, status_clamp, _, _, _ = ProductValidationEngine.calculate_quality_score(severe_issues)
        self.assertEqual(score_clamp, 0.0)
        self.assertEqual(status_clamp, ValidationStatus.FAILED)

    def test_product_with_multiple_issues(self):
        """Test 13: Product with multiple combined issues aggregates correctly"""
        product = Product(
            id=uuid.uuid4(),
            external_product_id=None,  # Missing MPN (ERROR -20)
            product_name="Product",
            category=None,  # Missing Category (WARNING -7)
            raw_data={},
        )
        # Empty value attribute (ERROR -20)
        attr = ProductAttribute(id=uuid.uuid4(), product_id=product.id, attribute_name="voltage", attribute_value="", confidence_score=0.9)
        attr.evidences = []
        product.attributes = [attr]

        report = ProductValidationEngine.validate_product(product)
        self.assertGreaterEqual(report.errors, 2)
        self.assertGreaterEqual(report.warnings, 1)
        self.assertLess(report.score, 70.0)
        self.assertEqual(report.status, ValidationStatus.FAILED)

    def test_empty_validation_results(self):
        """Test 14: Empty issues list returns 100 score and PASSED status"""
        score, status, errs, warns, infos = ProductValidationEngine.calculate_quality_score([])
        self.assertEqual(score, 100.0)
        self.assertEqual(status, ValidationStatus.PASSED)
        self.assertEqual(errs, 0)
        self.assertEqual(warns, 0)
        self.assertEqual(infos, 0)

    def test_part_manuf_satisfies_validation(self):
        """Test 15: Part_Manuf in raw_data satisfies manufacturer validation rule"""
        product = Product(
            id=uuid.uuid4(),
            external_product_id="3MABR-7100048736",
            product_name="3M 775L Stikit Film P80",
            category="Sanding Disc",
            raw_data={
                "Mfg_Part_Num": "3MABR-7100048736",
                "Part_Manuf": "Jam Industrial Supply LLC (JAMIN)",
                "Part_Desc": "3M 775L Stikit Film P80 - Cubitron II 50 Disc/Box",
            },
        )
        report = ProductValidationEngine.validate_product(product)
        # Manufacturer issue must NOT be present
        manuf_issues = [i for i in report.results if i.field == "manufacturer"]
        self.assertEqual(len(manuf_issues), 0, "Part_Manuf should satisfy manufacturer validation")

    def test_enrichments_visible_to_validation(self):
        """Test 16: Deterministically enriched fields are visible to validation engine"""
        from app.models.product import ProductEnrichment
        product = Product(
            id=uuid.uuid4(),
            external_product_id=None,
            product_name=None,
            category=None,
            raw_data={},
        )
        e_name = ProductEnrichment(field_name="Product Name", value="Enriched Standard Title")
        e_mpn = ProductEnrichment(field_name="MANUFACTURER_PART_NUMBER", value="MPN-999")
        e_manuf = ProductEnrichment(field_name="MANUFACTURER_NAME", value="Jam Industrial Supply LLC (JAMIN)")
        e_brand = ProductEnrichment(field_name="BRAND_NAME", value="3M")
        e_class = ProductEnrichment(field_name="Class", value="Abrasives")
        product.enrichments = [e_name, e_mpn, e_manuf, e_brand, e_class]

        report = ProductValidationEngine.validate_product(product)
        # None of the core identity elements should report MISSING_REQUIRED_FIELD or INCOMPLETE_IDENTITY
        identity_errors = [i for i in report.results if i.field in ["product_name", "manufacturer_part_number", "manufacturer", "brand", "product_type"]]
        self.assertEqual(len(identity_errors), 0, "Enriched fields must satisfy validation identity requirements")

    def test_unsupported_product_type_remains_blank(self):
        """Test 17: Unsupported product_type remains blank rather than hallucinating categories"""
        product = Product(
            id=uuid.uuid4(),
            external_product_id="SKU-123",
            product_name="Generic Non-Standard Item",
            category=None,
            raw_data={"Mfg_Part_Num": "SKU-123", "Part_Manuf": "Jam Industrial Supply"},
        )
        report = ProductValidationEngine.validate_product(product)
        type_issues = [i for i in report.results if i.field == "product_type"]
        self.assertEqual(len(type_issues), 1)
        self.assertEqual(type_issues[0].severity, ValidationSeverity.WARNING)
        self.assertEqual(type_issues[0].validation_type, "INCOMPLETE_IDENTITY")


if __name__ == "__main__":
    unittest.main()
