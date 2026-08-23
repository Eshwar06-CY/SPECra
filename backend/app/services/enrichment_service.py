"""
Enrichment Service for Deadlock.
Coordinates product enrichment, persistence in product_enrichments table,
and on-demand enrichment retrieval.
"""
import uuid
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.product import Product, ProductEnrichment
from app.services.enrichment_engine import (
    ProductEnrichmentEngine,
    ProductEnrichmentReport,
    EnrichedField,
)

logger = logging.getLogger(__name__)


class EnrichmentService:
    """
    Coordinates execution and persistence of deterministic product enrichments.
    """

    @staticmethod
    def enrich_and_save_product(
        db: Session,
        product_id: uuid.UUID,
    ) -> ProductEnrichmentReport:
        """
        Runs deterministic enrichment, saves results into product_enrichments, and returns the report.
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product '{product_id}' not found.")

        # 1. Execute deterministic enrichment
        report = ProductEnrichmentEngine.enrich_product(product)

        # 2. Clean prior enrichments for this product
        db.query(ProductEnrichment).filter(ProductEnrichment.product_id == product.id).delete()
        db.flush()

        # 3. Persist new enrichments
        job_filename = product.raw_data.get("_source_file") if product.raw_data else "input_dataset"
        for item in report.enrichments:
            db_enrich = ProductEnrichment(
                product_id=product.id,
                field_name=item.field,
                value=item.value,
                normalized_value=item.normalized_value,
                unit=item.unit,
                source_name=job_filename,
                source_type=item.source_type,
                source_location=item.source_location or item.source,
                source_text=item.source_text,
                provenance=item.provenance,
                extraction_method=item.method,
                confidence_score=item.confidence,
            )
            db.add(db_enrich)

        db.commit()

        return report

    @staticmethod
    def get_product_enrichment_report(
        db: Session,
        product_id: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves stored enrichment records for a product. If none exist, runs an on-demand enrichment.
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None

        enrich_records = db.query(ProductEnrichment).filter(ProductEnrichment.product_id == product.id).all()

        if not enrich_records:
            report = EnrichmentService.enrich_and_save_product(db, product_id)
            return report.model_dump()

        enrichments = []
        for r in enrich_records:
            enrichments.append({
                "field": r.field_name,
                "value": r.value,
                "normalized_value": r.normalized_value,
                "unit": r.unit,
                "method": r.extraction_method,
                "provenance": r.provenance,
                "confidence": r.confidence_score,
                "source": r.source_location or r.source_type,
                "source_type": r.source_type,
                "source_location": r.source_location,
                "source_text": r.source_text,
            })

        return {
            "product_id": str(product.id),
            "status": "completed",
            "enriched_fields": len(enrichments),
            "skipped_fields": 252 - len(enrichments),
            "conflicts": [],
            "enrichments": enrichments,
        }
