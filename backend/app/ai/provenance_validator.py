"""
Deterministic Provenance and Evidence Validator for Deadlock.
Validates LLM-proposed attributes, identity fields, and features against
the raw ingested dataset columns to guarantee mathematically sound, verifiable provenance
(DIRECT vs INFERRED vs UNKNOWN) and prevent hallucinated DIRECT claims.
"""
from typing import Any, Dict, List, Optional, Tuple
from app.ai.schemas import (
    Provenance,
    Evidence,
    ProductIdentity,
    ProductAttribute,
    ProductFeature,
    CanonicalProduct,
)

# Generic placeholder tokens across industrial catalogs
PLACEHOLDER_TOKENS = {
    "-- unbranded --",
    "-- no unilog brand --",
    "-- no dib brand --",
    "-- unassigned --",
    "unbranded",
    "no brand",
    "unknown",
    "none",
    "n/a",
    "na",
    "null",
    "",
}


def is_placeholder(val: Optional[str]) -> bool:
    """Checks if a string value is empty, null, or a known placeholder token."""
    if val is None:
        return True
    cleaned = str(val).strip().lower()
    return cleaned in PLACEHOLDER_TOKENS


def find_token_in_raw_data(
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

    # 1. Search in preferred fields first if specified
    ordered_fields = []
    if preferred_fields:
        for f in preferred_fields:
            if f in raw_data and f not in ordered_fields:
                ordered_fields.append(f)
    for f in raw_data.keys():
        if f not in ordered_fields:
            ordered_fields.append(f)

    token_lower = token_str.lower()

    for field_name in ordered_fields:
        field_val = raw_data.get(field_name)
        if field_val is None:
            continue
        field_str = str(field_val).strip()
        if is_placeholder(field_str):
            continue

        # Check exact or case-insensitive substring
        if token_str in field_str:
            return field_name, token_str
        elif token_lower in field_str.lower():
            # Find the actual case slice in field_str
            idx = field_str.lower().find(token_lower)
            actual_text = field_str[idx : idx + len(token_str)]
            return field_name, actual_text

    return None


class ProvenanceValidator:
    """
    Deterministic validator and reconciler for product intelligence.
    Ensures:
    1. Brand is reconciled correctly prioritizing explicit valid text in Part_Desc over catalog placeholders.
    2. Manufacturer is deterministically captured from Part_Manuf or verified.
    3. Every DIRECT attribute or identity claim is verified to exist in the raw input fields.
    4. Explicit tokens (like '6pc', '18in', '1/2in') are elevated to DIRECT.
    5. False DIRECT claims without input evidence are downgraded to INFERRED.
    """

    @classmethod
    def validate_and_enrich_canonical_product(
        cls,
        canonical: CanonicalProduct,
        raw_data: Dict[str, Any],
        filename: str = "input_dataset",
    ) -> CanonicalProduct:
        """
        Validates and refines a CanonicalProduct instance deterministically using raw_data.
        """
        # 1. Reconcile Brand
        cls._reconcile_brand(canonical.identity, raw_data, filename)

        # 2. Reconcile Manufacturer
        cls._reconcile_manufacturer(canonical.identity, raw_data, filename)

        # 3. Reconcile Part Numbers
        cls._reconcile_part_numbers(canonical.identity, raw_data, filename)

        # 4. Reconcile Product Type
        cls._reconcile_product_type(canonical.identity, raw_data, filename)

        # 5. Validate and Reconcile Dynamic Attributes
        cls._validate_attributes(canonical.attributes, raw_data, filename)

        # 6. Validate Features
        cls._validate_features(canonical.features, raw_data, filename)

        return canonical

    @classmethod
    def _reconcile_brand(
        cls,
        identity: ProductIdentity,
        raw_data: Dict[str, Any],
        filename: str,
    ):
        """
        Reconciles brand:
        1. If brand is proposed by LLM or present, verify against Part_Desc or raw fields.
        2. If candidate brand exists in Part_Desc, it is DIRECT evidence.
        3. Ignores placeholder brand fields like '-- Unbranded --', '-- No Unilog Brand --'.
        """
        candidate_brand = identity.brand_name
        brand_match = None

        if candidate_brand and not is_placeholder(candidate_brand):
            brand_match = find_token_in_raw_data(
                candidate_brand, raw_data, preferred_fields=["Part_Desc", "E1_Brand", "Unilog_Brand", "DIB_Brand"]
            )

        # Fallback: check if any valid catalog brand column has non-placeholder value
        if not brand_match:
            for bf in ["E1_Brand", "Unilog_Brand", "DIB_Brand", "Brand"]:
                val = raw_data.get(bf)
                if val and not is_placeholder(str(val)):
                    candidate_brand = str(val).strip()
                    brand_match = (bf, candidate_brand)
                    break

        if brand_match:
            field_name, exact_text = brand_match
            identity.brand_name = candidate_brand or exact_text
            identity.brand_evidence = Evidence(
                source_type="input_dataset",
                source_name=filename,
                source_location=field_name,
                source_text=exact_text,
                provenance=Provenance.DIRECT,
                confidence=1.0 if field_name in ["Part_Desc", "Part_Manuf"] else 0.98,
                notes=f"Deterministically verified from input column '{field_name}'",
            )
        elif candidate_brand and not is_placeholder(candidate_brand):
            # Candidate exists from LLM reasoning but not found verbatim
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

    @classmethod
    def _reconcile_manufacturer(
        cls,
        identity: ProductIdentity,
        raw_data: Dict[str, Any],
        filename: str,
    ):
        """
        Reconciles manufacturer:
        Part_Manuf takes top priority if present and non-empty.
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
                notes="Deterministically extracted from explicit manufacturer input column",
            )
        elif identity.manufacturer_name and not is_placeholder(identity.manufacturer_name):
            match = find_token_in_raw_data(identity.manufacturer_name, raw_data)
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

    @classmethod
    def _reconcile_part_numbers(
        cls,
        identity: ProductIdentity,
        raw_data: Dict[str, Any],
        filename: str,
    ):
        """
        Reconciles part numbers and MPN deterministically.
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
            )

    @classmethod
    def _reconcile_product_type(
        cls,
        identity: ProductIdentity,
        raw_data: Dict[str, Any],
        filename: str,
    ):
        """
        Reconciles product type and checks for DIRECT verbatim presence.
        """
        if not identity.product_type:
            return

        match = find_token_in_raw_data(identity.product_type, raw_data, preferred_fields=["Part_Desc"])
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
                notes="Classified semantically from description text",
            )

    @classmethod
    def _validate_attributes(
        cls,
        attributes: List[ProductAttribute],
        raw_data: Dict[str, Any],
        filename: str,
    ):
        """
        Validates every attribute:
        - If original_value or value or evidence_text is found verbatim in raw input -> DIRECT
        - If claimed DIRECT but cannot be verified anywhere -> downgraded to INFERRED
        """
        for attr in attributes:
            # Candidates tokens to search in raw text
            candidate_tokens = [
                attr.original_value,
                attr.evidence_text,
                attr.value,
                (attr.evidence.source_text if attr.evidence else None),
            ]
            
            # For pack quantity special cases (e.g. '6' with unit 'pc'/'pieces', check '6pc', '6 pc', '6-pack', '6pk')
            if attr.name in ["pack_quantity", "quantity", "selling_quantity"] and attr.normalized_value:
                qty = attr.normalized_value
                candidate_tokens.extend([f"{qty}pc", f"{qty} pc", f"{qty}pk", f"{qty} pk", f"{qty}-pack", f"{qty} pack", f"{qty} pieces", f"{qty}pcs"])

            matched = None
            for tok in candidate_tokens:
                if tok and not is_placeholder(tok):
                    matched = find_token_in_raw_data(tok, raw_data, preferred_fields=["Part_Desc"])
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
                    notes=f"Verified verbatim from input field '{field_name}'",
                )
            else:
                # If LLM claimed DIRECT but token is absent from all columns, downgrade to INFERRED
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
                        notes="Derived semantically; no exact verbatim token in raw text",
                    )
                else:
                    attr.evidence.provenance = attr.provenance

    @classmethod
    def _validate_features(
        cls,
        features: List[ProductFeature],
        raw_data: Dict[str, Any],
        filename: str,
    ):
        for feat in features:
            match = find_token_in_raw_data(feat.value, raw_data, preferred_fields=["Part_Desc"])
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
