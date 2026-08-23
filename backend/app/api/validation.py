"""
API Router for Deadlock Product Validation Engine.
Provides endpoints for executing and retrieving deterministic quality assessments.
"""
import uuid
import logging
from typing import Any, Dict, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.validation_service import ValidationService
from app.api.deps import get_optional_auth
from app.models.user import User, Workspace
from app.models.product import ProcessingJob, Product

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/validation", tags=["validation"])


@router.post(
    "/product/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Execute deterministic validation and quality audit over a product record",
)
def validate_product(
    product_id: uuid.UUID,
    auth: Optional[Tuple[User, Workspace]] = Depends(get_optional_auth),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Evaluates canonical product intelligence against identity completeness, evidence anchors,
    unit correctness, measurement sanity, and conflicting attribute values with IDOR protection.
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
        report = ValidationService.validate_and_save_product(db=db, product_id=product_id)
        return report.model_dump()
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        )
    except Exception as exc:
        logger.exception(f"Validation failed for product {product_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during product validation: {str(exc)}",
        )


@router.get(
    "/product/{product_id}",
    summary="Retrieve validation results and quality score for a product",
)
def get_product_validation(
    product_id: uuid.UUID,
    auth: Optional[Tuple[User, Workspace]] = Depends(get_optional_auth),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns stored validation issues, quality score, severity breakdown with IDOR check.
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

    report = ValidationService.get_product_validation_report(db=db, product_id=product_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation report for product '{product_id}' not found.",
        )
    return report.model_dump()
