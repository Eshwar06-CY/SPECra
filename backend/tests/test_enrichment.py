"""
Unit tests for the Deadlock Product Enrichment Engine.
Runs 100% offline without calling any LLM API.
"""
import unittest
import uuid

from app.models.product import Product, ProductAttribute, Evidence, ProductEnrichment
from app.ai.normalizer import (
    normalize_numeric_string,
    normalize_unit,
    parse_measurement,
)
from app.services.enrichment_engine import (
    ProductEnrichmentEngine,
    EnrichedField,
    ProductEnrichmentReport,
)
from app.services.enrichment_service import EnrichmentService
from app.core.database import SessionLocal


class TestEnrichmentEngine(unittest.TestCase):
    """
    Comprehensive offline test suite for ProductEnrichmentEngine and Normalizer.
    """

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_fraction_normalization(self):
        """Test 1: Fraction normalization converts fractional measurements to standardized decimals"""
        self.assertEqual(normalize_numeric_string("1/2"), "0.5")
        self.assertEqual(normalize_numeric_string("1/4"), "0.25")
        self.assertEqual(normalize_numeric_string("3/4"), "0.75")
        self.assertEqual(normalize_numeric_string("1 1/2"), "1.5")
        self.assertEqual(normalize_numeric_string("18"), "18")
        self.assertEqual(normalize_numeric_string("0.5"), "0.5")

    def test_unit_normalization(self):
        """Test 2: Unit normalization standardizes various unit spellings"""
        self.assertEqual(normalize_unit("\""), "in")
        self.assertEqual(normalize_unit("inch"), "in")
        self.assertEqual(normalize_unit("inches"), "in")
        self.assertEqual(normalize_unit("in"), "in")
        self.assertEqual(normalize_unit("pcs"), "pieces")
        self.assertEqual(normalize_unit("pc"), "pieces")
        self.assertEqual(normalize_unit("pack"), "pieces")
        self.assertEqual(normalize_unit("pk"), "pieces")
        self.assertEqual(normalize_unit("volts"), "V")
        self.assertEqual(normalize_unit("psi"), "PSI")

    def test_pack_quantity_normalization_6pc(self):
        """Test 3: Pack quantity normalization extracts '6pc' as 6 pieces per pack"""
        product = Product(
            id=uuid.uuid4(),
            product_name="Sanding Belts",
            category="Abrasives",
            raw_data={"Part_Desc": "DCB518ASTS06G Diablo 1/2\"x18\" Sanding Belt 6pc"},
        )
        report = ProductEnrichmentEngine.enrich_product(product)
        qty_item = next((e for e in report.enrichments if e.field == "Selling Qty"), None)
        uom_item = next((e for e in report.enrichments if e.field == "Selling UOM"), None)
        pkg_item = next((e for e in report.enrichments if e.field == "Standard Packaging Information"), None)

        self.assertIsNotNone(qty_item)
        self.assertEqual(qty_item.value, "6")
        self.assertEqual(qty_item.provenance, "DERIVED")

        self.assertIsNotNone(uom_item)
        self.assertEqual(uom_item.value, "pieces")

        self.assertIsNotNone(pkg_item)
        self.assertEqual(pkg_item.value, "6 pieces per pack")

    def test_pack_quantity_6pack(self):
        """Test 3b: '6-pack' parses Selling Qty=6, Selling UOM=Pack, Packaging='6 pieces per pack'"""
        product = Product(
            id=uuid.uuid4(),
            raw_data={"Part_Desc": "Diablo Sanding Belt 6-pack"},
        )
        report = ProductEnrichmentEngine.enrich_product(product)
        qty_item = next((e for e in report.enrichments if e.field == "Selling Qty"), None)
        uom_item = next((e for e in report.enrichments if e.field == "Selling UOM"), None)
        pkg_item = next((e for e in report.enrichments if e.field == "Standard Packaging Information"), None)

        self.assertEqual(qty_item.value, "6")
        self.assertEqual(uom_item.value, "Pack")
        self.assertEqual(pkg_item.value, "6 pieces per pack")

    def test_pack_quantity_10_pieces(self):
        """Test 3c: '10 pieces' parses Selling Qty=10, Selling UOM=pieces, Packaging='10 pieces per pack'"""
        product = Product(
            id=uuid.uuid4(),
            raw_data={"Part_Desc": "Abrasive Discs 10 pieces"},
        )
        report = ProductEnrichmentEngine.enrich_product(product)
        qty_item = next((e for e in report.enrichments if e.field == "Selling Qty"), None)
        uom_item = next((e for e in report.enrichments if e.field == "Selling UOM"), None)
        pkg_item = next((e for e in report.enrichments if e.field == "Standard Packaging Information"), None)

        self.assertEqual(qty_item.value, "10")
        self.assertEqual(uom_item.value, "pieces")
        self.assertEqual(pkg_item.value, "10 pieces per pack")

    def test_unsupported_packaging_information_remains_blank(self):
        """Test 3d: Products with no packaging mentions do not fabricate packaging information"""
        product = Product(
            id=uuid.uuid4(),
            raw_data={"Part_Desc": "Single Diablo Sanding Belt"},
        )
        report = ProductEnrichmentEngine.enrich_product(product)
        fields = {e.field for e in report.enrichments}

        self.assertNotIn("Selling Qty", fields)
        self.assertNotIn("Selling UOM", fields)
        self.assertNotIn("Standard Packaging Information", fields)

    def test_dimension_extraction(self):
        """Test 4: Dimension extraction parses width x length patterns with units"""
        product = Product(
            id=uuid.uuid4(),
            product_name="Sanding Belt",
            category="Abrasives",
            raw_data={"Part_Desc": "DCB518ASTS06G Diablo 1/2\"x18\" Sanding Belt 6pc"},
        )
        report = ProductEnrichmentEngine.enrich_product(product)

        width_item = next((e for e in report.enrichments if e.field == "WIDTH"), None)
        width_uom = next((e for e in report.enrichments if e.field == "WIDTH_UOM"), None)
        len_item = next((e for e in report.enrichments if e.field == "LENGTH"), None)
        len_uom = next((e for e in report.enrichments if e.field == "LENGTH_UOM"), None)

        self.assertIsNotNone(width_item)
        self.assertEqual(width_item.value, "0.5")
        self.assertEqual(width_uom.value, "in")

        self.assertIsNotNone(len_item)
        self.assertEqual(len_item.value, "18")
        self.assertEqual(len_uom.value, "in")

    def test_product_name_mapping(self):
        """Test 5: Product name mapping populates 'Product Name' field with DERIVED provenance"""
        product = Product(
            id=uuid.uuid4(),
            product_name="Diablo 1/2\" x 18\" Sanding Belt, 6-Pack",
            raw_data={"Part_Desc": "Diablo Sanding Belt 1/2\"x18\" 6pc"},
        )
        report = ProductEnrichmentEngine.enrich_product(product)
        name_item = next((e for e in report.enrichments if e.field == "Product Name"), None)
        self.assertIsNotNone(name_item)
        self.assertEqual(name_item.value, "Diablo 1/2\" x 18\" Sanding Belt, 6-Pack")

    def test_selling_quantity_mapping(self):
        """Test 6: Selling quantity maps accurately from '6-pack' or '6pc'"""
        product = Product(
            id=uuid.uuid4(),
            raw_data={"Part_Desc": "Sanding Belt 10-pack"},
        )
        report = ProductEnrichmentEngine.enrich_product(product)
        qty_item = next((e for e in report.enrichments if e.field == "Selling Qty"), None)
        self.assertIsNotNone(qty_item)
        self.assertEqual(qty_item.value, "10")

    def test_provenance_generation(self):
        """Test 8: Provenance is marked as DIRECT for verbatim strings and DERIVED for calculated values"""
        product = Product(
            id=uuid.uuid4(),
            product_name="Diablo Sanding Belt",
            raw_data={
                "Mfg_Part_Num": "DCB518ASTS06G",
                "Part_Manuf": "Freud Inc",
                "Part_Desc": "Diablo 1/2\"x18\" Sanding Belt 6pc",
            },
        )
        report = ProductEnrichmentEngine.enrich_product(product)
        mpn_item = next(e for e in report.enrichments if e.field == "MANUFACTURER_PART_NUMBER")
        self.assertEqual(mpn_item.provenance, "DIRECT")

        dim_item = next(e for e in report.enrichments if e.field == "WIDTH")
        self.assertEqual(dim_item.provenance, "DERIVED")

    def test_unsupported_field_remains_blank(self):
        """Test 9: Unsupported fields without evidence are never hallucinated or enriched"""
        product = Product(
            id=uuid.uuid4(),
            product_name="Diablo Sanding Belt",
            raw_data={"Part_Desc": "Diablo Sanding Belt"},
        )
        report = ProductEnrichmentEngine.enrich_product(product)
        enriched_fields = {e.field for e in report.enrichments}

        self.assertNotIn("UPC", enriched_fields)
        self.assertNotIn("GTIN", enriched_fields)
        self.assertNotIn("EAN", enriched_fields)
        self.assertNotIn("List Price", enriched_fields)
        self.assertNotIn("Warranty", enriched_fields)
        self.assertNotIn("Country Of Origin", enriched_fields)

    def test_conflict_detection(self):
        """Test 10: Conflicting brands produce an EnrichmentConflict without guessing"""
        product = Product(
            id=uuid.uuid4(),
            product_name="Belt",
            raw_data={
                "E1_Brand": "Milwaukee",
                "Part_Desc": "DeWalt Sanding Belt",
            },
        )
        report = ProductEnrichmentEngine.enrich_product(product)
        self.assertEqual(len(report.conflicts), 1)
        self.assertEqual(report.conflicts[0].field, "BRAND_NAME")
        self.assertIn("Milwaukee", report.conflicts[0].candidate_values)
        self.assertIn("DeWalt", report.conflicts[0].candidate_values)


if __name__ == "__main__":
    unittest.main()
