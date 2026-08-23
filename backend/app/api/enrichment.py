"""
API Router for Deadlock Product Enrichment Engine.
Provides endpoints for triggering and retrieving deterministic enrichment over product records.
"""
import uuid
import logging
from typing import Any, Dict, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.enrichment_service import EnrichmentService
from app.api.deps import get_optional_auth
from app.models.user import User, Workspace
from app.models.product import ProcessingJob, Product

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enrichment", tags=["enrichment"])


@router.post(
    "/product/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Execute deterministic product enrichment over a product record",
)
def enrich_product(
    product_id: uuid.UUID,
    auth: Optional[Tuple[User, Workspace]] = Depends(get_optional_auth),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Analyzes raw product data and structured intelligence to deterministically enrich
    additional UniHack output fields with traceable evidence anchors and normalization with IDOR protection.
    """
    if auth:
        prod = db.query(Product).filter(Product.id == product_id).first()
        if prod and prod.job_id:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == prod.job_id).first()
            if job and job.workspace_id and job.workspace_id != auth[1].id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access this resource.",
                )

    try:
        report = EnrichmentService.enrich_and_save_product(db=db, product_id=product_id)
        return report.model_dump()
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        )
    except Exception as exc:
        logger.exception(f"Product enrichment failed for product {product_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during product enrichment: {str(exc)}",
        )


@router.get(
    "/product/{product_id}",
    summary="Retrieve stored product enrichment results and provenance",
)
def get_product_enrichment(
    product_id: uuid.UUID,
    auth: Optional[Tuple[User, Workspace]] = Depends(get_optional_auth),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns the list of enriched fields, values, units, sources, and provenance methods for a product with IDOR check.
    """
    if auth:
        prod = db.query(Product).filter(Product.id == product_id).first()
        if prod and prod.job_id:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == prod.job_id).first()
            if job and job.workspace_id and job.workspace_id != auth[1].id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access this resource.",
                )

    report = EnrichmentService.get_product_enrichment_report(db=db, product_id=product_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Enrichment report for product '{product_id}' not found.",
        )
    return report.model_dump()
