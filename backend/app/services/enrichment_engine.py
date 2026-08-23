"""
Deterministic Product Enrichment Engine for Deadlock.
Performs cross-field analysis, semantic normalization, physical specification extraction,
and packaging inference strictly supported by source evidence.

Never invents or hallucinates values without evidence anchors.
"""
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from app.models.product import Product, ProductAttribute, Evidence
from app.ai.normalizer import normalize_numeric_string, normalize_unit, parse_measurement


class EnrichedField(BaseModel):
    """
    Structured representation of a deterministically enriched field.
    """
    field: str
    value: str
    normalized_value: Optional[str] = None
    unit: Optional[str] = None
    method: str = "DETERMINISTIC"
    provenance: str = "DERIVED"  # DIRECT, DERIVED, DETERMINISTIC
    confidence: float = 1.0
    source: str = "Part_Desc"
    source_type: str = "input_dataset"
    source_location: Optional[str] = None
    source_text: str


class EnrichmentConflict(BaseModel):
    """
    Records conflicting values detected across source fields.
    """
    field: str
    candidate_values: List[str]
    status: str = "CONFLICT"
    explanation: str


class ProductEnrichmentReport(BaseModel):
    """
    Report returned by the enrichment engine.
    """
    product_id: str
    status: str = "completed"
    enriched_fields: int = 0
    skipped_fields: int = 0
    conflicts: List[EnrichmentConflict] = Field(default_factory=list)
    enrichments: List[EnrichedField] = Field(default_factory=list)


class ProductEnrichmentEngine:
    """
    Deterministic rule-based enrichment engine.
    """

    @classmethod
    def enrich_product(
        cls,
        product: Product,
    ) -> ProductEnrichmentReport:
        """
        Extracts all deterministically derivable fields from raw catalog data and structured attributes.
        """
        raw_data: Dict[str, Any] = product.raw_data or {}
        enrichments: List[EnrichedField] = []
        conflicts: List[EnrichmentConflict] = []
        enriched_field_names: Set[str] = set()

        part_desc = str(raw_data.get("Part_Desc") or "").strip()
        part_manuf = str(raw_data.get("Part_Manuf") or "").strip()
        mfg_part_num = str(raw_data.get("Mfg_Part_Num") or "").strip()

        # 1. MPN / Part Number Enrichment
        if mfg_part_num:
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="MANUFACTURER_PART_NUMBER",
                value=mfg_part_num,
                source_loc="Mfg_Part_Num",
                source_text=mfg_part_num,
                provenance="DIRECT",
            )
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="PART_NUMBER",
                value=mfg_part_num,
                source_loc="Mfg_Part_Num",
                source_text=mfg_part_num,
                provenance="DIRECT",
            )
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="SKU - MY_PART_NUMBER",
                value=mfg_part_num,
                source_loc="Mfg_Part_Num",
                source_text=mfg_part_num,
                provenance="DIRECT",
            )

        # 2. Manufacturer Name Enrichment
        if part_manuf and not part_manuf.startswith("--"):
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="MANUFACTURER_NAME",
                value=part_manuf,
                source_loc="Part_Manuf",
                source_text=part_manuf,
                provenance="DIRECT",
            )

        # 3. Brand Name Conflict Safety & Reconciliation
        brand_candidates = []
        for k in ["E1_Brand", "Unilog_Brand", "DIB_Brand"]:
            b_val = str(raw_data.get(k) or "").strip()
            if b_val and not b_val.startswith("--") and b_val.lower() not in {"unbranded", "unknown", "none"}:
                brand_candidates.append((k, b_val))

        # Check description for brand tokens
        desc_brand_match = re.search(r"\b(Diablo|Freud|DeWalt|Milwaukee|Bosch|Makita|Norton|3M|Stanley)\b", part_desc, re.IGNORECASE)
        if desc_brand_match:
            brand_token = desc_brand_match.group(1).title()
            brand_candidates.append(("Part_Desc", brand_token))

        unique_brands = set(b[1] for b in brand_candidates)
        if len(unique_brands) == 1:
            chosen_loc, chosen_val = brand_candidates[0]
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="BRAND_NAME",
                value=chosen_val,
                source_loc=chosen_loc,
                source_text=chosen_val,
                provenance="DIRECT",
            )
        elif len(unique_brands) > 1:
            conflicts.append(EnrichmentConflict(
                field="BRAND_NAME",
                candidate_values=list(unique_brands),
                explanation=f"Multiple conflicting brand candidates detected across source fields: {list(unique_brands)}",
            ))

        # 4. Dimensions Extraction (Width x Length)
        # Handles patterns like 1/2"x18", 1/2in x 18in, 4-1/2" x 1/4"
        dim_match = re.search(
            r"(\d+(?:[\s\-]\d+/\d+|\.\d+|/\d+)?)\s*(?:\"|in|inch|inches|'')?\s*[xX*]\s*(\d+(?:[\s\-]\d+/\d+|\.\d+|/\d+)?)\s*(\"|in|inch|inches|''|mm|cm|ft)",
            part_desc,
            re.IGNORECASE,
        )
        if dim_match:
            w_raw = dim_match.group(1)
            l_raw = dim_match.group(2)
            uom_raw = dim_match.group(3)

            w_norm = normalize_numeric_string(w_raw)
            l_norm = normalize_numeric_string(l_raw)
            uom_norm = normalize_unit(uom_raw) or "in"
            matched_str = dim_match.group(0)

            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="WIDTH",
                value=w_norm,
                normalized_value=w_norm,
                unit=uom_norm,
                source_loc="Part_Desc",
                source_text=matched_str,
                provenance="DERIVED",
            )
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="WIDTH_UOM",
                value=uom_norm,
                source_loc="Part_Desc",
                source_text=matched_str,
                provenance="DERIVED",
            )
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="LENGTH",
                value=l_norm,
                normalized_value=l_norm,
                unit=uom_norm,
                source_loc="Part_Desc",
                source_text=matched_str,
                provenance="DERIVED",
            )
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="LENGTH_UOM",
                value=uom_norm,
                source_loc="Part_Desc",
                source_text=matched_str,
                provenance="DERIVED",
            )

        # 5. Pack Quantity & Packaging Extraction
        # Handles 6pc, 6 pcs, 6-pack, 6 pack, 10 count, 100/box
        pack_match = re.search(
            r"(\d+)\s*(?:-|/)?\s*(pc|pcs|piece|pieces|pk|pack|packs|ct|count|box|boxes)\b",
            part_desc,
            re.IGNORECASE,
        )
        if pack_match:
            qty_raw = pack_match.group(1)
            unit_raw = pack_match.group(2).lower()
            qty_norm = normalize_numeric_string(qty_raw)
            matched_str = pack_match.group(0)

            # Distinguish container packaging (pack, box) vs item piece count
            is_container = unit_raw in {"pk", "pack", "packs", "box", "boxes", "set", "sets"}
            selling_uom = "Pack" if unit_raw in {"pk", "pack", "packs"} else ("Box" if unit_raw in {"box", "boxes"} else "pieces")
            item_noun = "pieces" if qty_norm != "1" else "piece"
            pkg_container = "pack" if selling_uom in {"Pack", "pieces"} else selling_uom.lower()

            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="Selling Qty",
                value=qty_norm,
                normalized_value=qty_norm,
                source_loc="Part_Desc",
                source_text=matched_str,
                provenance="DERIVED",
            )
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="Selling UOM",
                value=selling_uom,
                source_loc="Part_Desc",
                source_text=matched_str,
                provenance="DERIVED",
            )
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="Standard Packaging Information",
                value=f"{qty_norm} {item_noun} per {pkg_container}",
                source_loc="Part_Desc",
                source_text=matched_str,
                provenance="DERIVED",
            )

        # 6. Product Name Standardization
        prod_title = product.product_name or (part_desc if part_desc and not part_desc.startswith("--") else None)
        if prod_title:
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="Product Name",
                value=prod_title,
                source_loc="Part_Desc",
                source_text=part_desc,
                provenance="DERIVED" if product.product_name else "DIRECT",
            )

        # 7. Category / Class
        if product.category:
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="Class",
                value=product.category,
                source_loc="Part_Desc",
                source_text=product.category,
                provenance="DIRECT",
            )

        return ProductEnrichmentReport(
            product_id=str(product.id),
            status="completed",
            enriched_fields=len(enrichments),
            skipped_fields=252 - len(enrichments),
            conflicts=conflicts,
            enrichments=enrichments,
        )

    @classmethod
    def _add_enrichment(
        cls,
        enrichment_list: List[EnrichedField],
        field_set: Set[str],
        field: str,
        value: str,
        source_loc: str,
        source_text: str,
        provenance: str = "DERIVED",
        normalized_value: Optional[str] = None,
        unit: Optional[str] = None,
    ) -> None:
        """Helper adding an enriched field if not already present."""
        if field not in field_set and value:
            field_set.add(field)
            enrichment_list.append(EnrichedField(
                field=field,
                value=value,
                normalized_value=normalized_value or value,
                unit=unit,
                method="DETERMINISTIC",
                provenance=provenance,
                confidence=1.0,
                source=source_loc,
                source_location=source_loc,
                source_text=source_text,
            ))
