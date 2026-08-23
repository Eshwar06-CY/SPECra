"""
Deterministic Product Validation and Quality Assessment Engine for Deadlock.
Evaluates canonical product intelligence against industrial engineering rules,
data completeness checks, unit validation, conflict detection, and evidence auditing.

Never invents or hallucinates values.
"""
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
from pydantic import BaseModel, Field
import re

from app.models.product import Product, ProductAttribute, Evidence, ValidationResult


class ValidationSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class ValidationStatus(str, Enum):
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


# Standard catalog sentinel/placeholder values
SENTINEL_VALUES = {
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

# Standard recognized engineering units
KNOWN_UNITS = {
    # Length / dimensions
    "in", "inch", "inches", "\"", "ft", "feet", "foot", "'", "yd", "yard",
    "mm", "cm", "m", "meter", "meters",
    # Weight / mass
    "lbs", "lb", "pound", "pounds", "oz", "ounce", "ounces", "g", "gram", "grams", "kg", "kilogram", "ton",
    # Quantity / Packaging
    "pc", "pcs", "piece", "pieces", "pk", "pack", "packs", "box", "boxes", "ct", "count", "ea", "each", "set", "sets", "pair", "pairs", "roll", "rolls", "disc", "discs", "sheet", "sheets", "belt", "belts", "pad", "pads",
    # Pressure
    "psi", "bar", "kpa", "mpa", "atm",
    # Electrical
    "v", "volt", "volts", "a", "amp", "amps", "w", "watt", "watts", "kw", "kilowatt", "hp", "horsepower", "hz", "hertz", "rpm",
    # Temperature
    "deg f", "deg c", "f", "c", "k",
    # Volume
    "gal", "gallon", "gallons", "qt", "quart", "pt", "pint", "fl oz", "l", "liter", "liters", "ml",
    # Grit / Abrasives
    "grit", "p-grade", "grade",
}


def is_sentinel(val: Optional[str]) -> bool:
    """Returns True if the string is empty or a known catalog placeholder sentinel."""
    if val is None:
        return True
    return str(val).strip().lower() in SENTINEL_VALUES


class ValidationIssue(BaseModel):
    """
    Structured, fully explainable validation finding.
    """
    validation_type: str = Field(..., description="E.g. MISSING_REQUIRED_FIELD, INVALID_UNIT, DUPLICATE_ATTRIBUTE")
    severity: ValidationSeverity = Field(..., description="ERROR, WARNING, INFO")
    field: str = Field(..., description="Field or attribute name being validated")
    current_value: Optional[str] = Field(None, description="Current value found in product representation")
    expected_condition: Optional[str] = Field(None, description="Rule requirement or expected state")
    message: str = Field(..., description="Human-readable explanation of the issue")
    validation_method: str = Field(default="DETERMINISTIC", description="DETERMINISTIC or RULE_BASED")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    attribute_id: Optional[str] = Field(None, description="Associated ProductAttribute UUID if applicable")
    details: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic payload")


class ProductValidationReport(BaseModel):
    """
    Complete summary report of deterministic product validation.
    """
    product_id: str
    status: ValidationStatus
    score: float = Field(..., ge=0.0, le=100.0, description="Quality score between 0 and 100")
    errors: int = 0
    warnings: int = 0
    info: int = 0
    results: List[ValidationIssue] = Field(default_factory=list)


class ProductValidationEngine:
    """
    Rule-based, deterministic validation engine for canonical product intelligence.
    """

    @staticmethod
    def calculate_quality_score(issues: List[ValidationIssue]) -> Tuple[float, ValidationStatus, int, int, int]:
        """
        Calculates deterministic quality score from validation issues:
        - Initial baseline: 100.0
        - Deductions: ERROR = -20, WARNING = -7, INFO = -2
        - Score clamped: [0.0, 100.0]
        - Status threshold: >= 90: 'passed', >= 70: 'warning', < 70: 'failed'
        """
        score = 100.0
        error_count = 0
        warning_count = 0
        info_count = 0

        for issue in issues:
            if issue.severity == ValidationSeverity.ERROR:
                score -= 20.0
                error_count += 1
            elif issue.severity == ValidationSeverity.WARNING:
                score -= 7.0
                warning_count += 1
            elif issue.severity == ValidationSeverity.INFO:
                score -= 2.0
                info_count += 1

        score = max(0.0, min(100.0, round(score, 1)))

        if score >= 90.0:
            status = ValidationStatus.PASSED
        elif score >= 70.0:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.FAILED

        return score, status, error_count, warning_count, info_count

    @classmethod
    def validate_product(
        cls,
        product: Product,
    ) -> ProductValidationReport:
        """
        Executes complete deterministic validation suite over a product and its attributes.
        """
        issues: List[ValidationIssue] = []

        raw_data = product.raw_data or {}
        attributes: List[ProductAttribute] = list(product.attributes)

        # Build attribute lookups
        attr_by_name: Dict[str, List[ProductAttribute]] = {}
        for a in attributes:
            name_key = a.attribute_name.lower().strip()
            attr_by_name.setdefault(name_key, []).append(a)

        # 1. Identity Completeness Validation
        cls._validate_identity(product, raw_data, attr_by_name, issues)

        # 2. Attribute Quality & Confidence Validation
        cls._validate_attributes(attributes, issues)

        # 3. Duplicate & Conflicting Attributes Validation
        cls._validate_duplicates_and_conflicts(attr_by_name, issues)

        # 4. Deterministic Physical Measurement & Unit Validation
        cls._validate_physical_measurements(attr_by_name, issues)

        # 5. Calculate Score & Aggregate
        score, status, errs, warns, infos = cls.calculate_quality_score(issues)

        return ProductValidationReport(
            product_id=str(product.id),
            status=status,
            score=score,
            errors=errs,
            warnings=warns,
            info=infos,
            results=issues,
        )

    @classmethod
    def _validate_identity(
        cls,
        product: Product,
        raw_data: Dict[str, Any],
        attr_by_name: Dict[str, List[ProductAttribute]],
        issues: List[ValidationIssue],
    ) -> None:
        """Validates canonical identity fields: title, product_type, brand, manufacturer, MPN."""
        # Case-insensitive map of raw fields and persisted enrichments
        raw_lower = {k.lower(): v for k, v in raw_data.items()} if raw_data else {}
        enrichments_by_field: Dict[str, str] = {}
        if hasattr(product, "enrichments") and product.enrichments:
            for e in product.enrichments:
                enrichments_by_field[e.field_name.lower().strip()] = e.value

        # 1. Product Name
        prod_name = product.product_name
        if not prod_name or is_sentinel(prod_name):
            prod_name = enrichments_by_field.get("product name") or enrichments_by_field.get("product_name") or raw_lower.get("part_desc") or raw_lower.get("description")

        if not prod_name or is_sentinel(prod_name):
            issues.append(ValidationIssue(
                validation_type="MISSING_REQUIRED_FIELD",
                severity=ValidationSeverity.ERROR,
                field="product_name",
                current_value=prod_name,
                expected_condition="Non-empty standardized product title",
                message="Product name is missing or empty.",
            ))

        # 2. Product Type / Category
        prod_type = product.category
        if not prod_type and "product_type" in attr_by_name:
            prod_type = attr_by_name["product_type"][0].attribute_value
        elif not prod_type:
            prod_type = enrichments_by_field.get("class") or enrichments_by_field.get("product_type")

        if not prod_type or is_sentinel(prod_type):
            issues.append(ValidationIssue(
                validation_type="INCOMPLETE_IDENTITY",
                severity=ValidationSeverity.WARNING,
                field="product_type",
                current_value=prod_type,
                expected_condition="Classified product type/category",
                message="Product type / category classification is missing.",
            ))

        # 3. Manufacturer Part Number (MPN)
        mpn = product.external_product_id
        if not mpn and "manufacturer_part_number" in attr_by_name:
            mpn = attr_by_name["manufacturer_part_number"][0].attribute_value
        elif not mpn and "part_number" in attr_by_name:
            mpn = attr_by_name["part_number"][0].attribute_value
        elif not mpn:
            mpn = enrichments_by_field.get("manufacturer_part_number") or enrichments_by_field.get("part_number") or raw_lower.get("mfg_part_num") or raw_lower.get("part_number")

        if not mpn or is_sentinel(mpn):
            issues.append(ValidationIssue(
                validation_type="MISSING_REQUIRED_FIELD",
                severity=ValidationSeverity.ERROR,
                field="manufacturer_part_number",
                current_value=mpn,
                expected_condition="Valid manufacturer part number (MPN / SKU)",
                message="Manufacturer part number is missing.",
            ))

        # 4. Manufacturer Name
        manuf = None
        if "manufacturer" in attr_by_name:
            manuf = attr_by_name["manufacturer"][0].attribute_value
        elif "manufacturer_name" in attr_by_name:
            manuf = attr_by_name["manufacturer_name"][0].attribute_value
        elif "manufacturer_name" in enrichments_by_field:
            manuf = enrichments_by_field.get("manufacturer_name")
        elif "part_manuf" in raw_lower:
            manuf = raw_lower.get("part_manuf")
        elif "manufacturer" in raw_lower:
            manuf = raw_lower.get("manufacturer")

        if not manuf or is_sentinel(manuf):
            issues.append(ValidationIssue(
                validation_type="INCOMPLETE_IDENTITY",
                severity=ValidationSeverity.WARNING,
                field="manufacturer",
                current_value=manuf,
                expected_condition="Identified manufacturer name",
                message="Manufacturer name is missing or unspecified in dataset.",
            ))

        # 5. Brand (Sentinel Aware)
        brand = None
        if "brand" in attr_by_name:
            brand = attr_by_name["brand"][0].attribute_value
        elif "brand_name" in attr_by_name:
            brand = attr_by_name["brand_name"][0].attribute_value
        elif "brand_name" in enrichments_by_field:
            brand = enrichments_by_field.get("brand_name")
        elif "brand" in enrichments_by_field:
            brand = enrichments_by_field.get("brand")

        # Check if raw data explicitly contains sentinel indicating unbranded catalog item
        is_explicit_unbranded = any(
            is_sentinel(str(raw_lower.get(k.lower(), "")))
            for k in ["E1_Brand", "Unilog_Brand", "DIB_Brand", "Brand"]
            if k.lower() in raw_lower and str(raw_lower.get(k.lower(), "")).strip().lower() in {"-- unbranded --", "unbranded", "no brand"}
        )

        if not brand or is_sentinel(brand):
            if is_explicit_unbranded:
                issues.append(ValidationIssue(
                    validation_type="UNBRANDED_CATALOG_ITEM",
                    severity=ValidationSeverity.INFO,
                    field="brand",
                    current_value=brand or "-- Unbranded --",
                    expected_condition="Explicit catalog brand or unbranded declaration",
                    message="Product is explicitly designated as unbranded by source catalog.",
                ))
            else:
                issues.append(ValidationIssue(
                    validation_type="INCOMPLETE_IDENTITY",
                    severity=ValidationSeverity.WARNING,
                    field="brand",
                    current_value=brand,
                    expected_condition="Identified brand name",
                    message="Brand name is missing.",
                ))

    @classmethod
    def _validate_attributes(
        cls,
        attributes: List[ProductAttribute],
        issues: List[ValidationIssue],
    ) -> None:
        """Validates attribute structures, evidence links, and confidence ranges."""
        for attr in attributes:
            attr_id_str = str(attr.id)

            # 1. Attribute Value Check
            if attr.attribute_value is None or str(attr.attribute_value).strip() == "":
                issues.append(ValidationIssue(
                    validation_type="EMPTY_ATTRIBUTE_VALUE",
                    severity=ValidationSeverity.ERROR,
                    field=attr.attribute_name,
                    current_value=attr.attribute_value,
                    expected_condition="Non-empty attribute value",
                    message=f"Attribute '{attr.attribute_name}' has an empty value.",
                    attribute_id=attr_id_str,
                ))

            # 2. Confidence Score Validation
            conf = attr.confidence_score
            if conf is None or conf < 0.0 or conf > 1.0:
                issues.append(ValidationIssue(
                    validation_type="INVALID_CONFIDENCE_RANGE",
                    severity=ValidationSeverity.ERROR,
                    field=attr.attribute_name,
                    current_value=str(conf),
                    expected_condition="Confidence score between 0.0 and 1.0",
                    message=f"Attribute '{attr.attribute_name}' has an invalid confidence score ({conf}).",
                    attribute_id=attr_id_str,
                ))
            elif conf < 0.50:
                issues.append(ValidationIssue(
                    validation_type="LOW_CONFIDENCE",
                    severity=ValidationSeverity.ERROR,
                    field=attr.attribute_name,
                    current_value=f"{conf:.2f}",
                    expected_condition="Confidence score >= 0.50",
                    message=f"Attribute '{attr.attribute_name}' has critically low confidence ({conf:.2f}).",
                    attribute_id=attr_id_str,
                ))
            elif conf < 0.70:
                issues.append(ValidationIssue(
                    validation_type="LOW_CONFIDENCE",
                    severity=ValidationSeverity.WARNING,
                    field=attr.attribute_name,
                    current_value=f"{conf:.2f}",
                    expected_condition="Confidence score >= 0.70",
                    message=f"Attribute '{attr.attribute_name}' has marginal confidence ({conf:.2f}).",
                    attribute_id=attr_id_str,
                ))

            # 3. Evidence Audit
            evidences = attr.evidences
            if not evidences:
                issues.append(ValidationIssue(
                    validation_type="MISSING_EVIDENCE",
                    severity=ValidationSeverity.ERROR,
                    field=attr.attribute_name,
                    current_value=attr.attribute_value,
                    expected_condition="Traceable evidence link in evidences table",
                    message=f"Attribute '{attr.attribute_name}' lacks supporting evidence anchor.",
                    attribute_id=attr_id_str,
                ))
            else:
                for ev in evidences:
                    # Check source_text
                    if not ev.source_text or str(ev.source_text).strip() == "":
                        issues.append(ValidationIssue(
                            validation_type="INVALID_EVIDENCE",
                            severity=ValidationSeverity.ERROR,
                            field=attr.attribute_name,
                            current_value="",
                            expected_condition="Non-empty source_text in evidence record",
                            message=f"Evidence for '{attr.attribute_name}' has empty source_text.",
                            attribute_id=attr_id_str,
                        ))

                    # Check provenance presence
                    prov = None
                    if ev.evidence_metadata and isinstance(ev.evidence_metadata, dict):
                        prov = ev.evidence_metadata.get("provenance")
                    if not prov:
                        issues.append(ValidationIssue(
                            validation_type="MISSING_PROVENANCE",
                            severity=ValidationSeverity.WARNING,
                            field=attr.attribute_name,
                            current_value=None,
                            expected_condition="Declared provenance (DIRECT, INFERRED, ENRICHED)",
                            message=f"Evidence for '{attr.attribute_name}' is missing provenance metadata.",
                            attribute_id=attr_id_str,
                        ))

    @classmethod
    def _validate_duplicates_and_conflicts(
        cls,
        attr_by_name: Dict[str, List[ProductAttribute]],
        issues: List[ValidationIssue],
    ) -> None:
        """Detects duplicate attribute definitions and conflicting values."""
        for name, attr_list in attr_by_name.items():
            if len(attr_list) > 1:
                values = [str(a.attribute_value).strip() for a in attr_list if a.attribute_value is not None]
                unique_values = set(values)

                if len(unique_values) > 1:
                    issues.append(ValidationIssue(
                        validation_type="CONFLICTING_VALUE",
                        severity=ValidationSeverity.ERROR,
                        field=name,
                        current_value=", ".join(unique_values),
                        expected_condition="Single consistent authoritative value",
                        message=f"Multiple conflicting values detected for attribute '{name}': {list(unique_values)}.",
                        details={"conflicting_ids": [str(a.id) for a in attr_list]},
                    ))
                else:
                    issues.append(ValidationIssue(
                        validation_type="DUPLICATE_ATTRIBUTE",
                        severity=ValidationSeverity.WARNING,
                        field=name,
                        current_value=values[0] if values else None,
                        expected_condition="Single attribute record per semantic property",
                        message=f"Duplicate attribute entries found for '{name}'.",
                        details={"duplicate_ids": [str(a.id) for a in attr_list]},
                    ))

    @classmethod
    def _validate_physical_measurements(
        cls,
        attr_by_name: Dict[str, List[ProductAttribute]],
        issues: List[ValidationIssue],
    ) -> None:
        """Validates common industrial measurements: units, normalized numeric values, and ranges."""
        numeric_attributes = {
            "length", "width", "height", "thickness", "diameter",
            "pack_quantity", "weight", "voltage", "amperage", "power", "pressure_rating"
        }

        for attr_name in numeric_attributes:
            if attr_name in attr_by_name:
                for attr in attr_by_name[attr_name]:
                    attr_id_str = str(attr.id)

                    # 1. Unit Validation
                    if attr.unit:
                        unit_clean = str(attr.unit).strip().lower()
                        # Match exact known unit or compound units like "ft/min", "in/sec"
                        is_valid_unit = (
                            unit_clean in KNOWN_UNITS
                            or any(part in KNOWN_UNITS for part in re.split(r"[\s/\-_]+", unit_clean) if part)
                        )
                        if not is_valid_unit:
                            issues.append(ValidationIssue(
                                validation_type="INVALID_UNIT",
                                severity=ValidationSeverity.ERROR,
                                field=attr.attribute_name,
                                current_value=attr.unit,
                                expected_condition="Standard engineering unit of measure",
                                message=f"Unrecognized or invalid unit '{attr.unit}' for attribute '{attr.attribute_name}'.",
                                attribute_id=attr_id_str,
                            ))

                    # 2. Normalization Validation
                    if attr.normalized_value:
                        try:
                            # Verify normalized string is convertible to float
                            norm_float = float(str(attr.normalized_value).strip())
                            if norm_float <= 0 and attr_name in {"length", "width", "height", "pack_quantity", "diameter"}:
                                issues.append(ValidationIssue(
                                    validation_type="INVALID_NORMALIZATION",
                                    severity=ValidationSeverity.ERROR,
                                    field=attr.attribute_name,
                                    current_value=str(attr.normalized_value),
                                    expected_condition="Positive non-zero numeric value",
                                    message=f"Non-positive measurement value '{attr.normalized_value}' for '{attr.attribute_name}'.",
                                    attribute_id=attr_id_str,
                                ))
                        except ValueError:
                            issues.append(ValidationIssue(
                                validation_type="INVALID_NORMALIZATION",
                                severity=ValidationSeverity.ERROR,
                                field=attr.attribute_name,
                                current_value=str(attr.normalized_value),
                                expected_condition="Valid floating-point or integer string",
                                message=f"Normalized value '{attr.normalized_value}' cannot be parsed as a numeric measurement.",
                                attribute_id=attr_id_str,
                            ))
