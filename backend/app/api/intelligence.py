"""
API Router for Deadlock Product Intelligence Engine.
Provides endpoints for AI health checks, batch job analysis, and individual product intelligence inspection.
"""
import uuid
import logging
from typing import Any, Dict, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.intelligence_service import IntelligenceService
from app.api.deps import get_optional_auth
from app.models.user import User, Workspace
from app.models.product import ProcessingJob, Product

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get("/health", summary="Check AI Provider health and connection status")
async def get_intelligence_health() -> Dict[str, Any]:
    """
    Returns the status and health of the active AI provider (Google Gemini API by default).
    """
    return await IntelligenceService.get_health()


@router.post(
    "/analyze/product/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Run AI product intelligence extraction over a single product record by product_id",
)
async def analyze_single_product(
    product_id: uuid.UUID,
    auth: Optional[Tuple[User, Workspace]] = Depends(get_optional_auth),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Triggers structured Product Intelligence extraction for a single product by its UUID with IDOR check.
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
        result = await IntelligenceService.analyze_single_product(
            db=db,
            product_id=product_id,
        )
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        )
    except Exception as exc:
        logger.exception(f"Intelligence analysis failed for product {product_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during AI intelligence analysis: {str(exc)}",
        )


@router.post(
    "/analyze/{job_id}",
    status_code=status.HTTP_200_OK,
    summary="Run AI product intelligence extraction over ingested job records",
)
async def analyze_job_products(
    job_id: uuid.UUID,
    limit: Optional[int] = Query(None, ge=1, description="Optional limit of products to process (e.g. 1, 10, 100)"),
    product_id: Optional[uuid.UUID] = Query(None, description="Optional specific product_id to process under this job"),
    auth: Optional[Tuple[User, Workspace]] = Depends(get_optional_auth),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Triggers structured Product Intelligence extraction for ingested products with tenant IDOR protection.
    """
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found.",
        )
    if auth and job.workspace_id and job.workspace_id != auth[1].id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )

    try:
        result = await IntelligenceService.analyze_job_products(
            db=db,
            job_id=job_id,
            limit=limit,
            product_id=product_id,
        )
        return result
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        )
    except Exception as exc:
        logger.exception(f"Intelligence analysis failed for job {job_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during AI intelligence analysis: {str(exc)}",
        )


@router.get(
    "/product/{product_id}",
    summary="Retrieve detailed intelligence, attributes, features, and evidence for a product",
)
def get_product_intelligence(
    product_id: uuid.UUID,
    auth: Optional[Tuple[User, Workspace]] = Depends(get_optional_auth),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns the complete product record with tenant IDOR verification.
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

    details = IntelligenceService.get_product_intelligence_details(db=db, product_id=product_id)
    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{product_id}' not found.",
        )
    return details
