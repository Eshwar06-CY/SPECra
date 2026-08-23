"""
Unit and regression tests for Phase 3 Natural-Language Product Query Engine.
Verifies QueryPlan validation, whitelisted mapping, SQL injection safety, filters, requested fields, and zero hallucinations.
"""
import unittest
import uuid

from app.core.database import SessionLocal
from app.models.product import Product, ProductAttribute, ProductEnrichment, Evidence
from app.schemas.query import QueryPlan, QueryFilter, FilterOperator
from app.ai.query_planner import QueryPlanner, ALLOWED_FIELDS_WHITELIST
from app.services.query_service import QueryService


class TestNaturalLanguageQueryEngine(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        self.job_id = uuid.uuid4()

    def tearDown(self):
        self.db.rollback()
        self.db.close()

    def test_01_query_plan_validation(self):
        """Test 1: QueryPlan Pydantic model validation"""
        f = QueryFilter(field="brand", operator=FilterOperator.EQUALS, value="3M")
        plan = QueryPlan(filters=[f], requested_fields=["brand", "manufacturer"])
        self.assertEqual(len(plan.filters), 1)
        self.assertEqual(plan.filters[0].field, "brand")
        self.assertEqual(plan.requested_fields, ["brand", "manufacturer"])

    def test_02_allowed_field_mapping_and_aliases(self):
        """Test 2: Whitelist resolution for aliases and unallowed fields"""
        planner = QueryPlanner()
        self.assertEqual(planner.resolve_field_name("mpn"), "manufacturer_part_number")
        self.assertEqual(planner.resolve_field_name("title"), "product_name")
        self.assertEqual(planner.resolve_field_name("category"), "product_type")
        self.assertIsNone(planner.resolve_field_name("credit_card_number"))
        self.assertIsNone(planner.resolve_field_name("internal_password"))

    def test_03_deterministic_pattern_3m_sanding(self):
        """Test 3: Deterministic interpretation of 'Show me all 3M sanding products with dimensions'"""
        planner = QueryPlanner()
        plan = planner.plan_deterministically("Show me all 3M sanding products with dimensions and packaging")
        filter_fields = [f.field for f in plan.filters]
        self.assertIn("brand", filter_fields)
        self.assertIn("product_type", filter_fields)
        self.assertIn("width", plan.requested_fields)
        self.assertIn("length", plan.requested_fields)
        self.assertIn("pack_quantity", plan.requested_fields)

    def test_04_freud_manufacturer_query(self):
        """Test 4: Deterministic interpretation of 'Show products manufactured by Freud'"""
        planner = QueryPlanner()
        plan = planner.plan_deterministically("Show products manufactured by Freud")
        filter_fields = [f.field for f in plan.filters]
        self.assertIn("manufacturer", filter_fields)
        manuf_filter = [f for f in plan.filters if f.field == "manufacturer"][0]
        self.assertEqual(manuf_filter.value, "Freud")

    def test_05_sql_injection_defense(self):
        """Test 5: Malicious query patterns are neutralized and never reach SQL execution"""
        planner = QueryPlanner()
        injection_query = "'; DROP TABLE products; -- Show me all 3M products"
        plan = planner.plan_deterministically(injection_query)
        
        # Verify that no SQL keywords leaked as field names
        for f in plan.filters:
            self.assertIn(f.field, ALLOWED_FIELDS_WHITELIST)
            self.assertNotIn("DROP", f.field)

        for req in plan.requested_fields:
            self.assertIn(req, ALLOWED_FIELDS_WHITELIST)

    def test_06_unavailable_fields_handling(self):
        """Test 6: Unknown requested fields are split into unavailable_fields without hallucination"""
        planner = QueryPlanner()
        avail, unavail = planner._validate_and_sanitize_fields(["brand", "color_scheme", "warranty_period", "width"])
        self.assertIn("brand", avail)
        self.assertIn("width", avail)
        self.assertIn("color_scheme", unavail)
        self.assertIn("warranty_period", unavail)

    def test_07_empty_query_plan(self):
        """Test 7: Empty query defaults to standard identity fields safely"""
        planner = QueryPlanner()
        plan = planner.plan_deterministically("")
        self.assertEqual(len(plan.filters), 0)
        self.assertIn("product_name", plan.requested_fields)

    def test_08_query_preview_service(self):
        """Test 8: QueryService.preview_query returns valid preview without execution errors"""
        preview = QueryService.preview_query(str(self.job_id), "Show 3M sanding products with width")
        self.assertEqual(preview.job_id, str(self.job_id))
        self.assertTrue(preview.can_execute)
        self.assertIn("width", preview.available_fields)


if __name__ == "__main__":
    unittest.main()
