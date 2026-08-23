"""
Canonical Product Intelligence Schema for Deadlock.
Structured strictly for compatibility with Google Gemini Developer API mode
(no free-form dict[str, Any] or open-ended maps that trigger additionalProperties errors).

Designed to faithfully capture all intelligence necessary to cleanly map into
the 252 static UniHack output headers across identity, features, dynamic attributes,
specifications, commerce, digital assets, compliance, and provenance.
"""
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator


class Provenance(str, Enum):
    DIRECT = "DIRECT"        # Explicitly stated in the input raw fields
    INFERRED = "INFERRED"    # Reasonably derived through logic/semantic clues from description
    ENRICHED = "ENRICHED"    # Acquired from downstream secondary/RAG sources
    UNKNOWN = "UNKNOWN"      # Insufficient evidence


class ExtractionMethod(str, Enum):
    LLM = "LLM"
    DETERMINISTIC = "DETERMINISTIC"
    RAG = "RAG"
    HUMAN = "HUMAN"


class Evidence(BaseModel):
    """
    Complete provenance anchor connecting an identity, attribute, or specification back to source fields.
    """
    source_type: str = Field(default="input_dataset", description="Source data type, e.g. input_dataset, web_enrichment, catalog_pdf")
    source_name: Optional[str] = Field(None, description="Filename or source document name")
    source_location: Optional[str] = Field(None, description="Original column or field name (e.g. Part_Desc, Part_Manuf)")
    source_text: Optional[str] = Field(None, description="Exact relevant text excerpt from the input")
    source_url: Optional[str] = Field(None, description="Verified URL if retrieved from external sources")
    provenance: Provenance = Field(default=Provenance.DIRECT, description="DIRECT, INFERRED, ENRICHED, UNKNOWN")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    notes: Optional[str] = Field(None, description="Reasoning or notes on how evidence was established")

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 1.0


# Backward compatibility alias
EvidenceCandidate = Evidence


class SourceFieldValue(BaseModel):
    """
    Explicit key-value pair representation to avoid free-form map schemas.
    """
    source_field: str = Field(..., description="Source field name, e.g. 'E1_Brand', 'Part_Desc'")
    value: Optional[str] = Field(None, description="Value from that source field")


class ProductConflict(BaseModel):
    """
    Records conflicting values between various source fields using explicit typed models.
    """
    field: str = Field(..., description="The conflicting attribute name, e.g. brand, manufacturer")
    conflicting_values: List[SourceFieldValue] = Field(
        default_factory=list,
        description="List of conflicting source fields and their respective values"
    )
    sources: List[str] = Field(default_factory=list, description="Names of the conflicting sources/columns")
    explanation: str = Field(..., description="Reason for conflict and rationale for chosen value or ambiguity")
    resolution: Optional[str] = Field(None, description="Selected value if justified by evidence, or 'ambiguous'")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)


class ProductAttribute(BaseModel):
    """
    Single structured industrial product attribute with provenance and confidence.
    Supports unlimited discovered technical specifications internally.
    """
    name: str = Field(..., description="Attribute name, e.g. grit, power, pressure_rating, voltage, dimensions, length, width, pack_quantity")
    value: Optional[str] = Field(None, description="Extracted attribute value, e.g. '18 in', '1/2 in', '6 pieces'")
    normalized_value: Optional[str] = Field(None, description="Standardized value, e.g. '18.0', '0.5', '6'")
    unit: Optional[str] = Field(None, description="Standard engineering unit / UOM, e.g. 'in', 'kW', 'PSI', 'V', 'RPM', 'pc', 'pieces'")
    original_value: Optional[str] = Field(None, description="Verbatim token as seen in text, e.g. '18\"', '1/2\"', '6pc'")
    provenance: Provenance = Field(default=Provenance.DIRECT, description="DIRECT if verbatim in input, INFERRED if derived")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score clamped between 0.0 and 1.0")
    evidence: Optional[Evidence] = Field(None, description="Evidence anchor connecting attribute to source")
    evidence_text: Optional[str] = Field(None, description="Original text excerpt supporting this attribute")
    source_field: Optional[str] = Field(None, description="Source field name where value was found, e.g. 'Part_Desc'")
    extraction_method: ExtractionMethod = Field(default=ExtractionMethod.LLM)

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 0.5


class ProductFeature(BaseModel):
    """
    Product feature bullet or highlights (maps downstream to ITEM_FEATURES_1..20).
    """
    name: str = Field(..., description="Feature title or summary, e.g. 'Durable Backing', 'Industrial Grade'")
    value: str = Field(..., description="Feature statement / detailed description")
    evidence: Optional[Evidence] = Field(None, description="Traceable evidence for this feature")
    provenance: Provenance = Field(default=Provenance.DIRECT, description="DIRECT, INFERRED, ENRICHED")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ProductIdentity(BaseModel):
    """
    Core master product identity fields matching UniHack taxonomy.
    """
    product_name: Optional[str] = Field(None, description="Cleaned, standardized, normalized product title")
    product_type: Optional[str] = Field(None, description="Classified product category/type, e.g. Sanding Belt, Ball Valve")
    manufacturer_name: Optional[str] = Field(None, description="Explicit manufacturer name (e.g. 'Freud Inc (2435)')")
    brand_name: Optional[str] = Field(None, description="Reconciled brand name (e.g. 'Diablo')")
    trade_name: Optional[str] = Field(None, description="Trade name or sub-brand if applicable")
    manufacturer_part_number: Optional[str] = Field(None, description="Mfg Part Number / MPN (e.g. 'DCB518ASTS06G')")
    alternate_part_number: Optional[str] = Field(None, description="Alternate or distributor part number")
    sku: Optional[str] = Field(None, description="Internal SKU or part identifier")
    part_number: Optional[str] = Field(None, description="Primary Part Number / MY_PART_NUMBER")

    # Evidence anchors for core identity elements
    brand_evidence: Optional[Evidence] = Field(None, description="Evidence for brand")
    manufacturer_evidence: Optional[Evidence] = Field(None, description="Evidence for manufacturer")
    part_number_evidence: Optional[Evidence] = Field(None, description="Evidence for part number")
    product_type_evidence: Optional[Evidence] = Field(None, description="Evidence for product type")


class ProductDescriptions(BaseModel):
    """
    Multi-channel commercial and technical product descriptions.
    """
    mobile_description: Optional[str] = Field(None, description="Ultra-concise mobile catalog description")
    invoice_description: Optional[str] = Field(None, description="Standard line-item invoice description")
    short_description: Optional[str] = Field(None, description="1-2 sentence concise product summary")
    long_description: Optional[str] = Field(None, description="Comprehensive technical product description")
    retail_description: Optional[str] = Field(None, description="Customer-facing retail product copy")
    marketing_description: Optional[str] = Field(None, description="Value-proposition and marketing bullet copy")


class ProductClassification(BaseModel):
    """
    Taxonomic and category hierarchy classification.
    """
    department: Optional[str] = Field(None, description="Top-level commercial department, e.g. 'Abrasives & Cutting Tools'")
    class_name: Optional[str] = Field(None, description="Intermediate product class, e.g. 'Belts'")
    fine: Optional[str] = Field(None, description="Fine-grained category classification, e.g. 'Narrow Sanding Belts'")
    classpath: Optional[str] = Field(None, description="Full category taxonomy path")
    unspsc: Optional[str] = Field(None, description="UNSPSC code if verifiable")


class PhysicalSpecifications(BaseModel):
    """
    Normalized physical dimensions and weights with units.
    """
    length: Optional[str] = Field(None, description="Item length, e.g. '18'")
    length_uom: Optional[str] = Field(None, description="Unit of measure for length, e.g. 'in'")
    height: Optional[str] = Field(None, description="Item height")
    height_uom: Optional[str] = Field(None, description="Unit of measure for height")
    width: Optional[str] = Field(None, description="Item width, e.g. '0.5' or '1/2'")
    width_uom: Optional[str] = Field(None, description="Unit of measure for width, e.g. 'in'")
    weight: Optional[str] = Field(None, description="Item weight")
    weight_uom: Optional[str] = Field(None, description="Unit of measure for weight, e.g. 'lbs'")
    volume: Optional[str] = Field(None, description="Item volume")
    volume_uom: Optional[str] = Field(None, description="Unit of measure for volume")


class CommerceInfo(BaseModel):
    """
    Pricing, packaging, barcodes, and ordering parameters.
    """
    upc: Optional[str] = Field(None, description="Universal Product Code (UPC)")
    ean: Optional[str] = Field(None, description="European Article Number (EAN)")
    gtin: Optional[str] = Field(None, description="Global Trade Item Number (GTIN)")
    list_price: Optional[str] = Field(None, description="Manufacturer list price")
    selling_quantity: Optional[str] = Field(None, description="Selling packaging quantity, e.g. '6'")
    selling_uom: Optional[str] = Field(None, description="Selling unit of measure, e.g. 'Pack', 'Box', 'EA'")
    standard_packaging_information: Optional[str] = Field(None, description="Packaging breakdown, e.g. '6 Belts per Pack'")
    warranty: Optional[str] = Field(None, description="Warranty terms")


class DigitalAssets(BaseModel):
    """
    Traceable media URLs and documentation references.
    """
    product_image: Optional[str] = Field(None, description="Primary product image URL")
    alternate_images: List[str] = Field(default_factory=list, description="Additional image URLs")
    sds: Optional[str] = Field(None, description="Safety Data Sheet URL")
    warranty_information: Optional[str] = Field(None, description="Warranty document URL")
    catalog: Optional[str] = Field(None, description="Catalog page URL")
    specification_sheet: Optional[str] = Field(None, description="Specification sheet PDF URL")
    instruction_installation_manual: Optional[str] = Field(None, description="Instruction manual URL")
    service_manual: Optional[str] = Field(None, description="Service manual URL")
    owners_user_manual: Optional[str] = Field(None, description="User manual URL")
    line_drawing: Optional[str] = Field(None, description="Line drawing / schematic URL")
    mtr: Optional[str] = Field(None, description="Material Test Report URL")
    rohs: Optional[str] = Field(None, description="RoHS compliance certificate URL")
    full_engineering_drawing: Optional[str] = Field(None, description="Engineering CAD drawing URL")
    energy_star_guide: Optional[str] = Field(None, description="Energy Star guide URL")
    technical_bulletin: Optional[str] = Field(None, description="Technical bulletin URL")
    submittal: Optional[str] = Field(None, description="Submittal sheet URL")
    compatibility_chart: Optional[str] = Field(None, description="Compatibility chart URL")
    size_chart: Optional[str] = Field(None, description="Size chart URL")
    product_label_insert: Optional[str] = Field(None, description="Product label URL")
    video_links: List[str] = Field(default_factory=list, description="Product video links")


class ProductMetadata(BaseModel):
    """
    Compliance and status metadata.
    """
    country_of_origin: Optional[str] = Field(None, description="Country of origin")
    discontinued: Optional[str] = Field(None, description="'Yes' or 'No'")
    actual_image: Optional[str] = Field(None, description="'Yes' or 'No'")
    standards_approvals: Optional[str] = Field(None, description="Standard / Approvals (e.g. UL, CE, ANSI, ISO)")
    prop_65: Optional[str] = Field(None, description="California Proposition 65 warning statement")
    application: Optional[str] = Field(None, description="Recommended applications")
    includes: Optional[str] = Field(None, description="Included components / items in the box")


class CanonicalProduct(BaseModel):
    """
    Canonical Internal Product Intelligence Representation.
    Serves as the single source of truth across LLM extraction, RAG enrichment,
    human review, and final mapping to the 252 static UniHack output headers.
    """
    identity: ProductIdentity = Field(default_factory=ProductIdentity, description="Identity & classification headers")
    classification: ProductClassification = Field(default_factory=ProductClassification, description="Taxonomy fields")
    descriptions: ProductDescriptions = Field(default_factory=ProductDescriptions, description="Multi-tier product copy")
    features: List[ProductFeature] = Field(default_factory=list, description="Dynamic list of product features")
    attributes: List[ProductAttribute] = Field(default_factory=list, description="Dynamic list of discovered attributes")
    physical_specifications: PhysicalSpecifications = Field(default_factory=PhysicalSpecifications, description="Dimensions & weights")
    commerce: CommerceInfo = Field(default_factory=CommerceInfo, description="Barcodes, pricing, packaging")
    digital_assets: DigitalAssets = Field(default_factory=DigitalAssets, description="Media, manuals, drawings")
    metadata: ProductMetadata = Field(default_factory=ProductMetadata, description="Compliance and regulatory metadata")
    missing_attributes: List[str] = Field(default_factory=list, description="Expected attributes not found in input")
    conflicts: List[ProductConflict] = Field(default_factory=list, description="Field conflicts and reconciliations")
    summary: Optional[str] = Field(None, description="Concise technical summary")
    reasoning: Optional[str] = Field(None, description="Extraction reasoning")
    overall_confidence: float = Field(default=0.9, ge=0.0, le=1.0)

    @field_validator("overall_confidence", mode="before")
    @classmethod
    def clamp_overall_confidence(cls, v: Any) -> float:
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 0.5


# CanonicalProduct is the primary intelligence structure
ProductIntelligence = CanonicalProduct
