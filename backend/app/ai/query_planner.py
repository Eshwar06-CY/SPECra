"""
Deterministic and AI-assisted Natural-Language Query Planner.
Transforms user natural language requests into structured, validated QueryPlan objects.
CRITICAL SECURITY: Does NOT generate SQL directly. Validates all fields against a strict whitelist.
"""
import re
import json
import logging
from typing import Dict, List, Set, Tuple, Optional, Any
from pydantic import BaseModel

from app.schemas.query import QueryPlan, QueryFilter, FilterOperator
from app.ai.gemini_provider import GeminiProvider

logger = logging.getLogger(__name__)

# Strict Whitelist of Allowed Search and Retrieval Fields
ALLOWED_FIELDS_WHITELIST: Dict[str, Dict[str, Any]] = {
    "brand": {
        "description": "Product brand name (e.g. 3M, Diablo, Freud)",
        "aliases": ["brand", "brand_name", "e1_brand", "unilog_brand", "dib_brand"],
    },
    "manufacturer": {
        "description": "Manufacturer name (e.g. Jam Industrial Supply, 3M Company)",
        "aliases": ["manufacturer", "mfg", "manuf", "part_manuf", "manufacturer_name"],
    },
    "manufacturer_part_number": {
        "description": "Manufacturer part number / MPN / SKU (e.g. 3MABR-7100048736)",
        "aliases": ["mpn", "part_number", "part_num", "sku", "item_number", "mfg_part_num"],
    },
    "product_name": {
        "description": "Full product title or name",
        "aliases": ["product_name", "title", "product_title", "part_desc", "description", "name"],
    },
    "product_type": {
        "description": "Product type or category (e.g. Sanding Disc, Belt, Blade)",
        "aliases": ["product_type", "category", "class", "type", "item_type"],
    },
    "width": {
        "description": "Product width dimension",
        "aliases": ["width", "w"],
    },
    "length": {
        "description": "Product length dimension",
        "aliases": ["length", "len", "l"],
    },
    "height": {
        "description": "Product height / thickness dimension",
        "aliases": ["height", "thickness", "h"],
    },
    "diameter": {
        "description": "Disc / wheel / hole diameter",
        "aliases": ["diameter", "disc_diameter", "size"],
    },
    "grit": {
        "description": "Abrasive grit size (e.g. 80, P80, 120)",
        "aliases": ["grit", "grit_size", "abrasive_grit"],
    },
    "pack_quantity": {
        "description": "Quantity per package or selling unit",
        "aliases": ["pack_quantity", "package_quantity", "selling_qty", "qty", "quantity", "package_qty", "count"],
    },
    "selling_uom": {
        "description": "Unit of measure for selling (e.g. Box, Pack, Each)",
        "aliases": ["selling_uom", "uom", "unit", "selling_unit", "package_type"],
    },
    "packaging": {
        "description": "Full standard packaging description",
        "aliases": ["packaging", "standard_packaging_information", "package_info", "packaging_info", "pack"],
    },
}

# Group aliases for natural requests like "dimensions"
FIELD_GROUPS: Dict[str, List[str]] = {
    "dimensions": ["diameter", "width", "length", "height"],
    "packaging": ["pack_quantity", "selling_uom", "packaging"],
    "packaging_quantity": ["pack_quantity"],
    "identity": ["product_name", "brand", "manufacturer", "manufacturer_part_number"],
    "specifications": ["diameter", "width", "length", "grit", "pack_quantity"],
}


class QueryPlanner:
    """
    Translates natural language product catalog questions into validated QueryPlan structures.
    Uses deterministic pattern parsing with graceful Gemini fallback for natural language synthesis.
    """

    def __init__(self, ai_provider: Optional[GeminiProvider] = None):
        self.ai_provider = ai_provider or GeminiProvider()

    @classmethod
    def resolve_field_name(cls, raw_name: str) -> Optional[str]:
        """Resolves an alias or raw field name to an allowed canonical field name."""
        clean = raw_name.lower().strip().replace("-", "_").replace(" ", "_")
        if clean in ALLOWED_FIELDS_WHITELIST:
            return clean

        for canonical_name, meta in ALLOWED_FIELDS_WHITELIST.items():
            if clean in meta["aliases"]:
                return canonical_name

        return None

    @classmethod
    def plan_deterministically(cls, query: str) -> QueryPlan:
        """
        Deterministic extraction for common catalog query patterns.
        E.g. 'Show me all 3M sanding products with dimensions and packaging'
        """
        q_lower = query.lower()
        filters: List[QueryFilter] = []
        requested_fields: Set[str] = set()

        # 1. Check Brand Filters
        if "3m" in q_lower:
            filters.append(QueryFilter(field="brand", operator=FilterOperator.EQUALS, value="3M"))
        elif "diablo" in q_lower:
            filters.append(QueryFilter(field="brand", operator=FilterOperator.EQUALS, value="Diablo"))
        elif "freud" in q_lower:
            filters.append(QueryFilter(field="brand", operator=FilterOperator.EQUALS, value="Freud"))

        # 2. Check Manufacturer Filters
        m_match = re.search(r"manufactured by\s+([a-zA-Z0-9\s]+)", query, re.IGNORECASE)
        if m_match:
            manuf_name = m_match.group(1).strip()
            filters.append(QueryFilter(field="manufacturer", operator=FilterOperator.CONTAINS, value=manuf_name))

        # 3. Check Category / Type Filters
        if "sanding" in q_lower:
            filters.append(QueryFilter(field="product_type", operator=FilterOperator.CONTAINS, value="Sanding"))
        elif "abrasive" in q_lower:
            filters.append(QueryFilter(field="product_type", operator=FilterOperator.CONTAINS, value="Abrasive"))
        elif "belt" in q_lower:
            filters.append(QueryFilter(field="product_type", operator=FilterOperator.CONTAINS, value="Belt"))
        elif "disc" in q_lower:
            filters.append(QueryFilter(field="product_type", operator=FilterOperator.CONTAINS, value="Disc"))

        # 4. Check MPN / Contains Pattern (e.g. 'containing 775L')
        c_match = re.search(r"containing\s+([a-zA-Z0-9\-]+)", q_lower)
        if c_match:
            token = c_match.group(1).strip()
            filters.append(QueryFilter(field="product_name", operator=FilterOperator.CONTAINS, value=token))

        # 5. Check Requested Field Groups
        if "dimension" in q_lower:
            requested_fields.update(FIELD_GROUPS["dimensions"])
        if "packaging" in q_lower or "package" in q_lower:
            requested_fields.update(FIELD_GROUPS["packaging"])
        if "packaging quantity" in q_lower or "pack quantity" in q_lower:
            requested_fields.add("pack_quantity")
        if "brand" in q_lower:
            requested_fields.add("brand")
        if "manufacturer" in q_lower:
            requested_fields.add("manufacturer")
        if "part number" in q_lower or "mpn" in q_lower:
            requested_fields.add("manufacturer_part_number")
        if "width" in q_lower:
            requested_fields.add("width")
        if "length" in q_lower:
            requested_fields.add("length")
        if "grit" in q_lower:
            requested_fields.add("grit")

        # Default requested fields if none explicitly requested
        if not requested_fields:
            requested_fields = {"product_name", "brand", "manufacturer", "manufacturer_part_number", "product_type"}

        return QueryPlan(
            filters=filters,
            requested_fields=sorted(list(requested_fields)),
            explanation=f"Interpreted {len(filters)} filter(s) and {len(requested_fields)} field(s) from query.",
        )

    async def create_query_plan(self, query: str) -> Tuple[QueryPlan, List[str], List[str]]:
        """
        Creates a validated QueryPlan from user natural language query.
        Returns (validated_plan, available_fields, unavailable_fields).
        """
        # First attempt deterministic pattern recognition
        plan = self.plan_deterministically(query)

        # If deterministic pattern found filters or fields, or if AI provider not configured, use it
        if plan.filters or not self.ai_provider.is_configured():
            avail, unavail = self._validate_and_sanitize_fields(plan.requested_fields)
            plan.requested_fields = avail
            return plan, avail, unavail

        # Use Gemini for complex natural language queries
        try:
            prompt = self._build_planner_prompt(query)
            response = await self.ai_provider.generate(
                prompt=prompt,
                system_instruction=(
                    "You are the Deadlock Product Query Planner. Output strict JSON matching the QueryPlan schema."
                    "NEVER output SQL. Map user requests only to allowed canonical field names."
                ),
                temperature=0.0,
            )
            # Parse JSON from LLM
            clean_json = response.strip()
            if "```json" in clean_json:
                clean_json = clean_json.split("```json")[1].split("```")[0].strip()
            elif "```" in clean_json:
                clean_json = clean_json.split("```")[1].split("```")[0].strip()

            data = json.loads(clean_json)
            raw_filters = data.get("filters", [])
            raw_requested = data.get("requested_fields", [])

            validated_filters: List[QueryFilter] = []
            for f in raw_filters:
                canon_field = self.resolve_field_name(f.get("field", ""))
                if canon_field:
                    op = f.get("operator", "contains")
                    try:
                        valid_op = FilterOperator(op)
                    except ValueError:
                        valid_op = FilterOperator.CONTAINS
                    validated_filters.append(
                        QueryFilter(
                            field=canon_field,
                            operator=valid_op,
                            value=str(f.get("value", "")).strip(),
                        )
                    )

            avail, unavail = self._validate_and_sanitize_fields(raw_requested)
            ai_plan = QueryPlan(
                filters=validated_filters,
                requested_fields=avail,
                explanation=data.get("explanation", "Parsed via AI query planner"),
            )
            return ai_plan, avail, unavail
        except Exception as err:
            logger.warning(f"AI query planning failed, falling back to deterministic plan: {err}")
            avail, unavail = self._validate_and_sanitize_fields(plan.requested_fields)
            plan.requested_fields = avail
            return plan, avail, unavail

    def _validate_and_sanitize_fields(self, requested: List[str]) -> Tuple[List[str], List[str]]:
        """Splits requested fields into strictly allowed and unavailable."""
        available: Set[str] = set()
        unavailable: Set[str] = set()

        for field_name in requested:
            # Check groups first
            f_clean = field_name.lower().strip()
            if f_clean in FIELD_GROUPS:
                for sub in FIELD_GROUPS[f_clean]:
                    available.add(sub)
                continue

            canon = self.resolve_field_name(field_name)
            if canon:
                available.add(canon)
            else:
                unavailable.add(field_name)

        return sorted(list(available)), sorted(list(unavailable))

    def _build_planner_prompt(self, query: str) -> str:
        allowed_list = [f"- {k}: {v['description']}" for k, v in ALLOWED_FIELDS_WHITELIST.items()]
        return f"""
Translate this user product catalog search query into a structured QueryPlan JSON:

User Query: "{query}"

Allowed Fields Whitelist:
{chr(10).join(allowed_list)}

Allowed Operators: equals, contains, starts_with, is_not_empty

Output Format (strictly valid JSON):
{{
  "filters": [
    {{"field": "allowed_field_name", "operator": "equals|contains|starts_with|is_not_empty", "value": "search term"}}
  ],
  "requested_fields": ["field1", "field2"],
  "explanation": "Human friendly interpretation summary"
}}
"""
