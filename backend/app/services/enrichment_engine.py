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

        # 2. Manufacturer Name Enrichment (Normalizing company suffixes e.g. 'Freud Inc (2435)' -> 'Freud Inc')
        norm_manuf = cls.normalize_manufacturer_name(part_manuf)
        if norm_manuf:
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="MANUFACTURER_NAME",
                value=norm_manuf,
                source_loc="Part_Manuf",
                source_text=part_manuf,
                provenance="DIRECT",
            )

        # 3. Brand Name Conflict Safety & Deterministic Extraction
        brand_val, brand_src, brand_conflicts = cls.extract_deterministic_brand(raw_data, part_desc)
        if brand_conflicts:
            conflicts.append(EnrichmentConflict(
                field="BRAND_NAME",
                candidate_values=brand_conflicts,
                explanation=f"Multiple conflicting brand candidates detected across source fields: {brand_conflicts}",
            ))
        elif brand_val:
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="BRAND_NAME",
                value=brand_val,
                source_loc=brand_src,
                source_text=brand_val,
                provenance="DIRECT" if brand_src != "Part_Desc" else "DERIVED",
            )

        # 4. Product-Aware Dimensions Extraction
        dim_info = cls.extract_deterministic_dimensions(part_desc)
        if dim_info:
            d_type = dim_info.get("type")
            if d_type == "rectangular":
                if "WIDTH" in dim_info:
                    cls._add_enrichment(
                        enrichments, enriched_field_names,
                        field="WIDTH",
                        value=dim_info["WIDTH"],
                        normalized_value=dim_info["WIDTH"],
                        unit=dim_info.get("WIDTH_UOM", "in"),
                        source_loc="Part_Desc",
                        source_text=dim_info.get("source_text", part_desc),
                        provenance="DERIVED",
                    )
                    cls._add_enrichment(
                        enrichments, enriched_field_names,
                        field="WIDTH_UOM",
                        value=dim_info.get("WIDTH_UOM", "in"),
                        source_loc="Part_Desc",
                        source_text=dim_info.get("source_text", part_desc),
                        provenance="DERIVED",
                    )
                if "LENGTH" in dim_info:
                    cls._add_enrichment(
                        enrichments, enriched_field_names,
                        field="LENGTH",
                        value=dim_info["LENGTH"],
                        normalized_value=dim_info["LENGTH"],
                        unit=dim_info.get("LENGTH_UOM", "in"),
                        source_loc="Part_Desc",
                        source_text=dim_info.get("source_text", part_desc),
                        provenance="DERIVED",
                    )
                    cls._add_enrichment(
                        enrichments, enriched_field_names,
                        field="LENGTH_UOM",
                        value=dim_info.get("LENGTH_UOM", "in"),
                        source_loc="Part_Desc",
                        source_text=dim_info.get("source_text", part_desc),
                        provenance="DERIVED",
                    )
            elif d_type in ("diameter", "three_axis"):
                # Circular tool: Diameter is an attribute slot, not planar width/length
                if "diameter" in dim_info:
                    cls._add_enrichment(
                        enrichments, enriched_field_names,
                        field="Diameter",
                        value=dim_info["diameter"],
                        normalized_value=dim_info["diameter"],
                        unit=dim_info.get("diameter_uom", "in"),
                        source_loc="Part_Desc",
                        source_text=dim_info.get("source_text", part_desc),
                        provenance="DERIVED",
                    )
                if "thickness" in dim_info:
                    cls._add_enrichment(
                        enrichments, enriched_field_names,
                        field="Thickness",
                        value=dim_info["thickness"],
                        normalized_value=dim_info["thickness"],
                        unit=dim_info.get("thickness_uom", "in"),
                        source_loc="Part_Desc",
                        source_text=dim_info.get("source_text", part_desc),
                        provenance="DERIVED",
                    )
                if "arbor" in dim_info:
                    cls._add_enrichment(
                        enrichments, enriched_field_names,
                        field="Arbor Hole Size",
                        value=dim_info["arbor"],
                        normalized_value=dim_info["arbor"],
                        unit=dim_info.get("arbor_uom", "in"),
                        source_loc="Part_Desc",
                        source_text=dim_info.get("source_text", part_desc),
                        provenance="DERIVED",
                    )

        # 5. Pack Quantity & Packaging Extraction (Preserving exact packaging nouns: sheets, discs, belts, pads, pieces)
        pkg_info = cls.extract_deterministic_packaging(part_desc)
        if pkg_info:
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="Selling Qty",
                value=pkg_info["qty"],
                normalized_value=pkg_info["qty"],
                source_loc="Part_Desc",
                source_text=pkg_info.get("source_text", part_desc),
                provenance="DERIVED",
            )
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="Selling UOM",
                value=pkg_info["uom"],
                source_loc="Part_Desc",
                source_text=pkg_info.get("source_text", part_desc),
                provenance="DERIVED",
            )
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="Standard Packaging Information",
                value=pkg_info["description"],
                source_loc="Part_Desc",
                source_text=pkg_info.get("source_text", part_desc),
                provenance="DERIVED",
            )

        # 6. Product Name Standardization
        prod_title = product.product_name or cls.normalize_product_title(part_desc, mfg_part_num)
        if prod_title:
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="Product Name",
                value=prod_title,
                source_loc="Part_Desc",
                source_text=part_desc,
                provenance="DERIVED" if product.product_name else "DIRECT",
            )

        # 7. Category / Taxonomy Class
        tax_class = product.category or cls.classify_product_taxonomy(part_desc)
        if tax_class:
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="Class",
                value=tax_class,
                source_loc="Part_Desc",
                source_text=part_desc,
                provenance="DERIVED" if not product.category else "DIRECT",
            )

        # 8. Grit Extraction
        grit_info = cls.extract_deterministic_grit(part_desc)
        if grit_info:
            cls._add_enrichment(
                enrichments, enriched_field_names,
                field="Grit Size",
                value=grit_info["value"],
                unit="Grit",
                source_loc="Part_Desc",
                source_text=grit_info.get("source_text", part_desc),
                provenance="DERIVED",
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
    def normalize_manufacturer_name(cls, raw_manuf: str) -> Optional[str]:
        """
        Cleans manufacturer names by stripping internal supplier codes like '(2435)' or '(JAMIN)'.
        Examples:
            'Freud Inc (2435)' -> 'Freud Inc'
            'Jam Industrial Supply LLC (JAMIN)' -> 'Jam Industrial Supply LLC'
            'Milwaukee Accessory (4031)' -> 'Milwaukee Accessory'
        """
        if not raw_manuf or raw_manuf.startswith("--"):
            return None
        cleaned = re.sub(r"\s*\([a-zA-Z0-9_\-]+\)\s*$", "", raw_manuf).strip()
        return cleaned or None

    @classmethod
    def normalize_product_title(cls, part_desc: str, mfg_part_num: str = "") -> Optional[str]:
        """
        Cleans raw product descriptions into standardized product titles without losing technical specs.
        Removes leading duplicate MPNs and excessive dashes.
        """
        if not part_desc or part_desc.startswith("--"):
            return None
        title = part_desc.strip()
        # Remove leading duplicate MPN if present
        if mfg_part_num and title.lower().startswith(mfg_part_num.lower()):
            title = title[len(mfg_part_num):].strip()
        # Remove leading punctuation/dashes
        title = re.sub(r"^[\s\-_:]+", "", title).strip()
        # Clean double spaces
        title = re.sub(r"\s+", " ", title).strip()
        return title or part_desc.strip()

    @classmethod
    def extract_deterministic_brand(cls, raw_data: Dict[str, Any], part_desc: str) -> Tuple[Optional[str], str, List[str]]:
        """
        Extracts brand from explicit brand columns or deterministic keyword patterns in Part_Desc.
        Returns (brand_val, brand_src, conflicts).
        """
        candidates: List[Tuple[str, str]] = []

        # 1. Check explicit brand fields
        for k in ["E1_Brand", "Unilog_Brand", "DIB_Brand"]:
            b_val = str(raw_data.get(k) or "").strip()
            if b_val and not b_val.startswith("--") and b_val.lower() not in {"unbranded", "unknown", "none", "no brand"}:
                candidates.append((k, b_val))

        # 2. Known brand dictionary
        KNOWN_BRANDS = [
            ("3M", r"\b3M\b"),
            ("Diablo", r"\bDiablo\b"),
            ("Freud", r"\bFreud\b"),
            ("HIOLIT", r"\bHIOLIT\b"),
            ("Abranet", r"\bAbranet\b"),
            ("Milwaukee", r"\b(?:Milwaukee|Milw)\b"),
            ("Mirka", r"\bMirka\b"),
            ("Norton", r"\bNorton\b"),
            ("Standard Abrasives", r"\bStandard Abrasives\b"),
            ("DeWalt", r"\bDeWalt\b"),
            ("Bosch", r"\bBosch\b"),
            ("Makita", r"\bMakita\b"),
            ("Stanley", r"\bStanley\b"),
            ("SIA", r"\bSIA\b"),
            ("Sunmight", r"\bSunmight\b"),
            ("Weiler", r"\bWeiler\b"),
            ("PFERD", r"\bPFERD\b"),
            ("Dynabrade", r"\bDynabrade\b"),
            ("Festool", r"\bFestool\b"),
        ]

        for brand_name, pattern in KNOWN_BRANDS:
            if re.search(pattern, part_desc, re.IGNORECASE):
                candidates.append(("Part_Desc", brand_name))

        unique_brands = list({b[1]: b for b in candidates}.values())
        if len(unique_brands) == 1:
            return unique_brands[0][1], unique_brands[0][0], []
        elif len(unique_brands) > 1:
            return None, "", [b[1] for b in unique_brands]

        return None, "", []

    @classmethod
    def extract_deterministic_dimensions(cls, part_desc: str) -> Dict[str, str]:
        """
        Product-context-aware precision dimension parser.
        Parsing priority:
        1. Three-axis cut-off / grinding discs: Diameter x Thickness x Arbor (e.g. 5"x.045"x7/8", 4"x.040"x5/8")
        2. Rectangular products (Belts, Sheets, Rolls): Dual dimensions -> WIDTH x LENGTH (e.g. 1/2"x18", 2.75x30, 3x4)
        3. Circular discs / wheels / blades / pads: Single dimension -> Diameter (e.g. 5" in 'HIOLIT 5" P80')
        """
        res: Dict[str, str] = {}
        if not part_desc:
            return res

        # Priority 1: Three-Axis Cut-Off / Grinding Disc Dimensions
        # Examples: 5"x.045"x7/8", 6-1/2"x1/8"x5/8", 4"x.040"x5/8", 12"x1/8"x20mm, 14"x7/64"x1"
        three_match = re.search(
            r"((?:\d+(?:[\s\-]\d+/\d+|\.\d+|/\d+)?|\.\d+))\s*(?:\"|in|inch|inches|'')?\s*[xX*]\s*((?:\d+(?:[\s\-]\d+/\d+|\.\d+|/\d+)?|\.\d+))\s*(?:\"|in|inch|inches|'')?\s*[xX*]\s*((?:\d+(?:[\s\-]\d+/\d+|\.\d+|/\d+)?|\.\d+))\s*(\"|in|inch|inches|''|mm|cm)?",
            part_desc,
            re.IGNORECASE,
        )
        if three_match:
            d_raw = three_match.group(1)
            t_raw = three_match.group(2)
            a_raw = three_match.group(3)
            uom_raw = three_match.group(4) or "in"

            d_norm = normalize_numeric_string(d_raw)
            t_norm = normalize_numeric_string(t_raw)
            a_norm = a_raw.strip()  # preserve fraction like 7/8, 5/8 or integer
            uom_norm = normalize_unit(uom_raw) or "in"

            return {
                "type": "three_axis",
                "diameter": d_norm,
                "diameter_uom": "in",
                "thickness": t_norm,
                "thickness_uom": "in",
                "arbor": a_norm,
                "arbor_uom": uom_norm,
                "source_text": three_match.group(0),
            }

        # Priority 2: Rectangular Products (Belts, Sheets, Rolls, Abrasives) - Dual Dimensions
        # Examples: 1/2"x18", 2.75x30, 3x4, 4-1/2" x 1/4"
        dim_match = re.search(
            r"((?:\d+(?:[\s\-]\d+/\d+|\.\d+|/\d+)?|\.\d+))\s*(?:\"|in|inch|inches|'')?\s*[xX*]\s*((?:\d+(?:[\s\-]\d+/\d+|\.\d+|/\d+)?|\.\d+))\s*(\"|in|inch|inches|''|mm|cm|ft)?",
            part_desc,
            re.IGNORECASE,
        )
        if dim_match:
            w_raw = dim_match.group(1)
            l_raw = dim_match.group(2)
            uom_raw = dim_match.group(3) or "in"

            w_norm = normalize_numeric_string(w_raw)
            l_norm = normalize_numeric_string(l_raw)
            uom_norm = normalize_unit(uom_raw) or "in"

            return {
                "type": "rectangular",
                "WIDTH": w_norm,
                "WIDTH_UOM": uom_norm,
                "LENGTH": l_norm,
                "LENGTH_UOM": uom_norm,
                "source_text": dim_match.group(0),
            }

        # Priority 3: Single Dimension on Circular Discs / Wheels / Abrasives
        # Example: HIOLIT 5" P80, 10 1/2" Saw Blade, Milw 5" Metal Cut Off Disc
        single_match = re.search(
            r"(?:^|\s)((?:\d+(?:[\s\-]\d+/\d+|\.\d+|/\d+)?|\.\d+))\s*(?:\"|''|in(?:ch(?:es)?)?)(?=\s|$)",
            part_desc,
            re.IGNORECASE,
        )
        if single_match:
            d_raw = single_match.group(1)
            return {
                "type": "diameter",
                "diameter": normalize_numeric_string(d_raw),
                "diameter_uom": "in",
                "source_text": single_match.group(0).strip(),
            }

        return res

    @classmethod
    def extract_deterministic_packaging(cls, part_desc: str) -> Optional[Dict[str, str]]:
        """
        Extracts packaging quantities and units from Part_Desc, preserving specific packaging nouns.
        Examples:
            6pc -> Selling Qty: 6, Selling UOM: pieces, Standard Packaging Information: 6 pieces per pack
            50 Sheets/Box -> Selling Qty: 50, Selling UOM: sheets, Standard Packaging Information: 50 sheets per box
            50 Disc/Box -> Selling Qty: 50, Selling UOM: disc, Standard Packaging Information: 50 pieces per box
            6-pack -> Selling Qty: 6, Selling UOM: Pack, Standard Packaging Information: 6 pieces per pack
        """
        if not part_desc:
            return None

        # Pattern 1: Explicit count with noun & container (e.g. 50 Sheets/Box, 50 Discs/Box, 100 Belts/Case)
        noun_box_match = re.search(
            r"(\d+)\s*(Discs?|Sheets?|Pads?|Belts?|Rolls?|Items?|Pcs?|Pieces?)?\s*/\s*(Box|Pack|Pk|Bag|Case)\b",
            part_desc,
            re.IGNORECASE,
        )
        if noun_box_match:
            qty_raw = noun_box_match.group(1)
            noun_raw = (noun_box_match.group(2) or "").lower()
            container_raw = noun_box_match.group(3).lower()
            qty_norm = normalize_numeric_string(qty_raw)

            # Preserve explicit noun
            if "sheet" in noun_raw or "sheet" in part_desc.lower():
                uom = "sheets"
                desc_str = f"{qty_norm} sheets per {container_raw}"
            elif "disc" in noun_raw or "disc" in part_desc.lower():
                uom = "disc" if ("disc/" in part_desc.lower() or "50 disc" in part_desc.lower()) else "discs"
                desc_str = f"{qty_norm} pieces per {container_raw}"
            elif "belt" in noun_raw or "belt" in part_desc.lower():
                uom = "belts"
                desc_str = f"{qty_norm} belts per {container_raw}"
            elif "pad" in noun_raw or "pad" in part_desc.lower():
                uom = "pads"
                desc_str = f"{qty_norm} pads per {container_raw}"
            elif "roll" in noun_raw:
                uom = "rolls"
                desc_str = f"{qty_norm} rolls per {container_raw}"
            else:
                uom = "pieces"
                desc_str = f"{qty_norm} pieces per {container_raw}"

            return {
                "qty": qty_norm,
                "uom": uom,
                "description": desc_str,
                "source_text": noun_box_match.group(0),
            }

        # Pattern 2: 6pc, 6 pcs, 6-pack, 10pk, 25 count, 10 pieces
        pack_match = re.search(
            r"(\d+)\s*(?:-|/)?\s*(pc|pcs|piece|pieces|pk|pack|packs|ct|count|box|boxes)\b",
            part_desc,
            re.IGNORECASE,
        )
        if pack_match:
            qty_raw = pack_match.group(1)
            unit_raw = pack_match.group(2).lower()
            qty_norm = normalize_numeric_string(qty_raw)

            if unit_raw in {"pk", "pack", "packs"}:
                selling_uom = "Pack"
            elif unit_raw in {"box", "boxes"}:
                selling_uom = "Box"
            else:
                selling_uom = "pieces"

            container = "box" if selling_uom == "Box" else "pack"
            item_noun = "pieces" if qty_norm != "1" else "piece"

            return {
                "qty": qty_norm,
                "uom": selling_uom,
                "description": f"{qty_norm} {item_noun} per {container}",
                "source_text": pack_match.group(0),
            }

        return None

    @classmethod
    def classify_product_taxonomy(cls, part_desc: str) -> Optional[str]:
        """
        Conservative taxonomy classifier for abrasive and industrial tooling items.
        """
        if not part_desc:
            return None
        p_lower = part_desc.lower()
        if "sanding belt" in p_lower or "abrasive belt" in p_lower:
            return "Sanding Belt"
        if "cut-off disc" in p_lower or "cut off disc" in p_lower or "cutoff disc" in p_lower:
            return "Cut-Off Disc"
        if "sanding disc" in p_lower:
            return "Sanding Disc"
        if "flap disc" in p_lower:
            return "Flap Disc"
        if "grinding wheel" in p_lower or "cut-off wheel" in p_lower or "cut off wheel" in p_lower:
            return "Grinding Wheel"
        if "sanding sheet" in p_lower or "abrasive sheet" in p_lower:
            return "Sanding Sheet"
        if "abrasive pad" in p_lower or "scuff pad" in p_lower:
            return "Abrasive Pad"
        if "abrasive roll" in p_lower:
            return "Abrasive Roll"
        if "diamond blade" in p_lower or "saw blade" in p_lower:
            return "Saw Blade"
        if "disc" in p_lower:
            return "Abrasive Disc"
        if "belt" in p_lower:
            return "Sanding Belt"
        return None

    @classmethod
    def extract_deterministic_grit(cls, part_desc: str) -> Optional[Dict[str, str]]:
        """
        Extracts grit specification from Part_Desc (e.g. P80, P120, 80 Grit).
        """
        if not part_desc:
            return None
        grit_match = re.search(r"\b(P\d+|\d+\s*Grit)\b", part_desc, re.IGNORECASE)
        if grit_match:
            raw_val = grit_match.group(1).upper().replace("GRIT", "").replace("P", "").strip()
            return {
                "value": raw_val,
                "source_text": grit_match.group(0),
            }
        return None

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
