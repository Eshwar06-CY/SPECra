"""
Deterministic Product Reconciliation and Provenance Engine for Deadlock.
Executes AFTER Gemini AI extraction and BEFORE PostgreSQL persistence.

Guarantees:
1. Brand reconciliation: Prioritizes explicit valid brands in Part_Desc over placeholder values
   (-- Unbranded --, -- No Unilog Brand --, -- No DIB Brand --, N/A, unknown, etc.).
2. Deterministic Manufacturer preservation: Maps Part_Manuf with DIRECT provenance without requiring LLM inference.
3. Deterministic MPN preservation: Maps Mfg_Part_Num with DIRECT provenance.
4. Deterministic Quantity and Dimension provenance: Verifies tokens like '6pc', '18in', '1/2in'
   directly in the raw dataset and guarantees DIRECT provenance.
5. Strict ground-truth validation: Verifies all claimed DIRECT attributes exist in raw fields;
   downgrades unsupported claims to INFERRED or UNKNOWN to prevent false provenance.
"""
from typing import Any, Dict, List, Optional, Tuple
import re

from app.ai.schemas import (
    Provenance,
    Evidence,
    ProductIdentity,
    ProductAttribute,
    ProductFeature,
    CanonicalProduct,
)

# Standard catalog placeholder values to ignore
PLACEHOLDER_VALUES = {
    "-- unbranded --",
    "-- no unilog brand --",
    "-- no dib brand --",
    "-- unassigned --",
    "unbranded",
    "no brand",
    "no unilog brand",
    "no dib brand",
    "unknown",
    "none",
    "n/a",
    "na",
    "null",
    "",
}


def is_placeholder(val: Any) -> bool:
    """Returns True if the value is empty, null, or a known catalog placeholder token."""
    if val is None:
        return True
    cleaned = str(val).strip().lower()
    return cleaned in PLACEHOLDER_VALUES


def find_token_in_raw_fields(
    token: Optional[str],
    raw_data: Dict[str, Any],
    preferred_fields: Optional[List[str]] = None,
) -> Optional[Tuple[str, str]]:
    """
    Searches for a verbatim substring or token inside raw_data fields.
    Returns (matched_field_name, matched_raw_text) if found, else None.
    """
    if not token or is_placeholder(token):
        return None

    token_str = str(token).strip()
    if not token_str:
        return None

    # Build field search order
    search_fields: List[str] = []
    if preferred_fields:
        for f in preferred_fields:
            if f in raw_data and f not in search_fields:
                search_fields.append(f)
    for f in raw_data.keys():
        if f not in search_fields:
            search_fields.append(f)

    token_lower = token_str.lower()

    for field_name in search_fields:
        field_val = raw_data.get(field_name)
        if field_val is None:
            continue
        field_str = str(field_val).strip()
        if is_placeholder(field_str):
            continue

        # 1. Exact match / substring
        if token_str in field_str:
            return field_name, token_str
        
        # 2. Case-insensitive substring match
        if token_lower in field_str.lower():
            idx = field_str.lower().find(token_lower)
            actual_text = field_str[idx : idx + len(token_str)]
            return field_name, actual_text

    return None


def reconcile_product_intelligence(
    canonical: CanonicalProduct,
    raw_data: Dict[str, Any],
    source_filename: str = "input_dataset",
) -> CanonicalProduct:
    """
    Deterministically reconciles and validates the CanonicalProduct against raw_data.
    Must be called AFTER Gemini extraction and BEFORE database persistence.
    """
    if not raw_data:
        return canonical

    # 1. Reconcile Brand
    _reconcile_brand(canonical.identity, raw_data, source_filename)

    # 2. Reconcile Manufacturer
    _reconcile_manufacturer(canonical.identity, raw_data, source_filename)

    # 3. Reconcile Manufacturer Part Number & SKUs
    _reconcile_part_numbers(canonical.identity, raw_data, source_filename)

    # 4. Reconcile Product Name & Title
    _reconcile_product_name(canonical.identity, raw_data, source_filename)

    # 5. Reconcile Product Type / Category
    _reconcile_product_type(canonical.identity, raw_data, source_filename)

    # 5. Reconcile & Validate Dynamic Attributes (dimensions, quantities, specs)
    _reconcile_attributes(canonical.attributes, raw_data, source_filename)

    # 6. Reconcile Features & Deduplicate against structured attributes
    _reconcile_features(canonical.features, raw_data, source_filename)
    _deduplicate_features_against_attributes(canonical.features, canonical.attributes)

    return canonical


def _reconcile_brand(
    identity: ProductIdentity,
    raw_data: Dict[str, Any],
    filename: str,
) -> None:
    """
    Reconciles brand:
    - If brand is proposed by Gemini or present in identity, check if it exists verbatim in Part_Desc.
    - If valid brand exists in Part_Desc, it takes priority and gets DIRECT provenance.
    - Placeholders in E1_Brand, Unilog_Brand, DIB_Brand are rejected.
    - If no brand in Part_Desc, check for any non-placeholder brand column.
    """
    candidate_brand = identity.brand_name
    match = None

    # Priority 1: Check proposed brand in Part_Desc or raw fields
    if candidate_brand and not is_placeholder(candidate_brand):
        match = find_token_in_raw_fields(
            candidate_brand,
            raw_data,
            preferred_fields=["Part_Desc", "E1_Brand", "Unilog_Brand", "DIB_Brand", "Brand"],
        )

    # Priority 2: If no match, check if any non-placeholder brand column exists
    if not match:
        for bf in ["Brand", "E1_Brand", "Unilog_Brand", "DIB_Brand"]:
            val = raw_data.get(bf)
            if val and not is_placeholder(str(val)):
                candidate_brand = str(val).strip()
                match = (bf, candidate_brand)
                break

    # Priority 3: Fallback check if description starts with/contains a known brand token extracted by LLM
    if not match and candidate_brand and not is_placeholder(candidate_brand):
        match = find_token_in_raw_fields(candidate_brand, raw_data)

    if match:
        field_name, exact_text = match
        identity.brand_name = candidate_brand or exact_text
        identity.brand_evidence = Evidence(
            source_type="input_dataset",
            source_name=filename,
            source_location=field_name,
            source_text=exact_text,
            provenance=Provenance.DIRECT,
            confidence=1.0 if field_name in ["Part_Desc", "Part_Manuf"] else 0.98,
            notes=f"Deterministically reconciled from input field '{field_name}'",
        )
    elif candidate_brand and not is_placeholder(candidate_brand):
        identity.brand_name = candidate_brand
        identity.brand_evidence = Evidence(
            source_type="input_dataset",
            source_name=filename,
            source_location="Part_Desc",
            source_text=candidate_brand,
            provenance=Provenance.INFERRED,
            confidence=0.8,
            notes="Inferred from product context; not matched verbatim in raw input",
        )
    else:
        identity.brand_name = None
        identity.brand_evidence = None


def _reconcile_manufacturer(
    identity: ProductIdentity,
    raw_data: Dict[str, Any],
    filename: str,
) -> None:
    """
    Reconciles manufacturer:
    Part_Manuf takes deterministic precedence as DIRECT evidence.
    """
    manuf_raw = raw_data.get("Part_Manuf") or raw_data.get("Manufacturer")
    if manuf_raw and not is_placeholder(str(manuf_raw)):
        manuf_str = str(manuf_raw).strip()
        identity.manufacturer_name = manuf_str
        identity.manufacturer_evidence = Evidence(
            source_type="input_dataset",
            source_name=filename,
            source_location="Part_Manuf" if "Part_Manuf" in raw_data else "Manufacturer",
            source_text=manuf_str,
            provenance=Provenance.DIRECT,
            confidence=1.0,
            notes="Deterministically extracted from raw manufacturer field",
        )
    elif identity.manufacturer_name and not is_placeholder(identity.manufacturer_name):
        match = find_token_in_raw_fields(identity.manufacturer_name, raw_data)
        if match:
            field_name, exact_text = match
            identity.manufacturer_evidence = Evidence(
                source_type="input_dataset",
                source_name=filename,
                source_location=field_name,
                source_text=exact_text,
                provenance=Provenance.DIRECT,
                confidence=0.98,
            )
        else:
            identity.manufacturer_evidence = Evidence(
                source_type="input_dataset",
                source_name=filename,
                source_location="Part_Desc",
                source_text=identity.manufacturer_name,
                provenance=Provenance.INFERRED,
                confidence=0.75,
            )


def _reconcile_part_numbers(
    identity: ProductIdentity,
    raw_data: Dict[str, Any],
    filename: str,
) -> None:
    """
    Reconciles MPN / Part Number directly from Mfg_Part_Num.
    """
    mfg_pn = raw_data.get("Mfg_Part_Num") or raw_data.get("PART_NUMBER") or raw_data.get("Part_Number")
    if mfg_pn and not is_placeholder(str(mfg_pn)):
        pn_str = str(mfg_pn).strip()
        identity.manufacturer_part_number = pn_str
        identity.part_number = identity.part_number or pn_str
        identity.part_number_evidence = Evidence(
            source_type="input_dataset",
            source_name=filename,
            source_location="Mfg_Part_Num" if "Mfg_Part_Num" in raw_data else "PART_NUMBER",
            source_text=pn_str,
            provenance=Provenance.DIRECT,
            confidence=1.0,
            notes="Deterministically extracted from raw part number field",
        )


def _reconcile_product_name(
    identity: ProductIdentity,
    raw_data: Dict[str, Any],
    filename: str,
) -> None:
    """
    Reconciles product title:
    - If Gemini generated a valid product title, preserves it.
    - If missing or placeholder, deterministically falls back to Part_Desc / Description.
    """
    if identity.product_name and not is_placeholder(identity.product_name):
        return

    part_desc = raw_data.get("Part_Desc") or raw_data.get("description") or raw_data.get("Part_Description") or raw_data.get("Product_Name")
    if part_desc and not is_placeholder(str(part_desc)):
        desc_str = str(part_desc).strip()
        identity.product_name = desc_str


def _reconcile_product_type(
    identity: ProductIdentity,
    raw_data: Dict[str, Any],
    filename: str,
) -> None:
    """
    Reconciles product type and checks if present verbatim in Part_Desc.
    """
    if not identity.product_type or is_placeholder(identity.product_type):
        return

    match = find_token_in_raw_fields(identity.product_type, raw_data, preferred_fields=["Part_Desc"])
    if match:
        field_name, exact_text = match
        identity.product_type_evidence = Evidence(
            source_type="input_dataset",
            source_name=filename,
            source_location=field_name,
            source_text=exact_text,
            provenance=Provenance.DIRECT,
            confidence=0.98,
        )
    else:
        identity.product_type_evidence = Evidence(
            source_type="input_dataset",
            source_name=filename,
            source_location="Part_Desc",
            source_text=identity.product_type,
            provenance=Provenance.INFERRED,
            confidence=0.9,
            notes="Semantically classified from product description",
        )


def _reconcile_attributes(
    attributes: List[ProductAttribute],
    raw_data: Dict[str, Any],
    filename: str,
) -> None:
    """
    Reconciles and validates every attribute:
    - Tolerates unit & token variations ('18\"' ↔ '18 in', '6pc' ↔ '6', '1/2\"' ↔ '0.5 in')
    - If verbatim token exists in raw text -> DIRECT
    - If claimed DIRECT but cannot be found -> downgraded to INFERRED
    """
    for attr in attributes:
        candidate_tokens: List[str] = []

        # Quantity / pack variations prioritized first (e.g. '6pc', '6 pcs', '6-pack', 'pack of 6')
        if attr.name in ["pack_quantity", "quantity", "selling_quantity", "package_quantity"] and (attr.normalized_value or attr.value):
            q = str(attr.normalized_value or attr.value).strip()
            # If unit is pc/pieces, search for unit compounds first
            candidate_tokens.extend([
                f"{q}pc", f"{q} pc", f"{q}pcs", f"{q} pcs",
                f"{q}pk", f"{q} pk", f"{q}-pack", f"{q} pack",
                f"pack of {q}", f"box of {q}", f"{q} pieces", f"{q} piece"
            ])

        # Dimension variations prioritized (e.g. '1/2"', '1/2in', '18"', '18in')
        if attr.name in ["length", "width", "height", "thickness", "diameter"]:
            val = str(attr.value or "").strip()
            norm = str(attr.normalized_value or "").strip()
            orig = str(attr.original_value or "").strip()
            if norm == "0.5" or "1/2" in val or "1/2" in orig:
                candidate_tokens.extend(["1/2\"", "1/2in", "1/2 in", "1/2", "0.5in", "0.5 in", "0.5\""])
            if norm == "0.25" or "1/4" in val or "1/4" in orig:
                candidate_tokens.extend(["1/4\"", "1/4in", "1/4 in", "1/4"])
            if norm == "0.75" or "3/4" in val or "3/4" in orig:
                candidate_tokens.extend(["3/4\"", "3/4in", "3/4 in", "3/4"])
            for v in [val, norm, orig]:
                if v:
                    candidate_tokens.extend([
                        f"{v}\"", f"{v}in", f"{v} in", f"{v}mm", f"{v} mm", f"{v}'", f"{v}ft"
                    ])

        if attr.original_value and not is_placeholder(attr.original_value):
            candidate_tokens.append(str(attr.original_value))
        if attr.evidence_text and not is_placeholder(attr.evidence_text):
            candidate_tokens.append(str(attr.evidence_text))
        if attr.value and not is_placeholder(attr.value):
            candidate_tokens.append(str(attr.value))
        if attr.evidence and attr.evidence.source_text and not is_placeholder(attr.evidence.source_text):
            candidate_tokens.append(str(attr.evidence.source_text))

        matched = None
        for tok in candidate_tokens:
            if tok and not is_placeholder(tok):
                matched = find_token_in_raw_fields(tok, raw_data, preferred_fields=["Part_Desc"])
                if matched:
                    break

        if matched:
            field_name, exact_text = matched
            attr.provenance = Provenance.DIRECT
            attr.source_field = field_name
            attr.evidence_text = exact_text
            attr.confidence = max(attr.confidence, 0.95)
            attr.evidence = Evidence(
                source_type="input_dataset",
                source_name=filename,
                source_location=field_name,
                source_text=exact_text,
                provenance=Provenance.DIRECT,
                confidence=attr.confidence,
                notes=f"Deterministically verified from input field '{field_name}'",
            )
        else:
            # If claimed DIRECT but cannot be verified anywhere, downgrade
            if attr.provenance == Provenance.DIRECT:
                attr.provenance = Provenance.INFERRED
                attr.confidence = min(attr.confidence, 0.85)

            if not attr.evidence:
                attr.evidence = Evidence(
                    source_type="input_dataset",
                    source_name=filename,
                    source_location=attr.source_field or "Part_Desc",
                    source_text=attr.value or str(attr.normalized_value),
                    provenance=attr.provenance,
                    confidence=attr.confidence,
                    notes="Inferred from context; no verbatim token in input fields",
                )
            else:
                attr.evidence.provenance = attr.provenance


def _reconcile_features(
    features: List[ProductFeature],
    raw_data: Dict[str, Any],
    filename: str,
) -> None:
    for feat in features:
        match = find_token_in_raw_fields(feat.value, raw_data, preferred_fields=["Part_Desc"])
        if match:
            field_name, exact_text = match
            feat.provenance = Provenance.DIRECT
            feat.evidence = Evidence(
                source_type="input_dataset",
                source_name=filename,
                source_location=field_name,
                source_text=exact_text,
                provenance=Provenance.DIRECT,
                confidence=0.98,
            )
        else:
            feat.provenance = Provenance.INFERRED
            if not feat.evidence:
                feat.evidence = Evidence(
                    source_type="input_dataset",
                    source_name=filename,
                    source_location="Part_Desc",
                    source_text=feat.value,
                    provenance=Provenance.INFERRED,
                    confidence=0.85,
                )


def _deduplicate_features_against_attributes(
    features: List[ProductFeature],
    attributes: List[ProductAttribute],
) -> None:
    """
    Ensures human-readable features that merely restate structured attributes
    (e.g., dimensions, pack quantity) are removed or filtered from competing with
    authoritative structured attributes.
    """
    structured_attr_names = {a.name.lower().replace(" ", "_") for a in attributes}
    
    # Overlapping feature categories / keywords that duplicate structured specs
    dimension_keys = {"dimensions", "dimension", "size", "width", "length", "height"}
    quantity_keys = {"pack_quantity", "package_quantity", "quantity", "selling_quantity"}

    has_structured_dimensions = bool(structured_attr_names.intersection({"width", "length", "height"}))
    has_structured_quantity = bool(structured_attr_names.intersection({"pack_quantity", "quantity", "selling_quantity"}))

    filtered_features: List[ProductFeature] = []
    for feat in features:
        feat_name_norm = feat.name.lower().replace(" ", "_").replace("-", "_")
        
        # Check if feature is a dimension duplicate
        if has_structured_dimensions and (
            feat_name_norm in dimension_keys or any(k in feat_name_norm for k in ["dimension", "width_by_length", "length_by_width"])
        ):
            continue

        # Check if feature is a pack quantity duplicate
        if has_structured_quantity and (
            feat_name_norm in quantity_keys or "pack_quantity" in feat_name_norm or "package_quantity" in feat_name_norm
        ):
            continue

        filtered_features.append(feat)

    features.clear()
    features.extend(filtered_features)
