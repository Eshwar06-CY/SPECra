"""
API Router for UniHack Product Export and Delivery Engine.
Provides endpoints for downloading CSV/XLSX deliveries and inspecting live mapping previews.
"""
import uuid
import logging
from typing import Any, Dict, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.export_service import ExportService
from app.api.deps import get_optional_auth
from app.models.user import User, Workspace
from app.models.product import ProcessingJob

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["export"])


@router.post(
    "/{job_id}",
    summary="Generate and download standardized UniHack delivery dataset (CSV or XLSX)",
)
def export_job_dataset(
    job_id: uuid.UUID,
    format: str = Query("csv", pattern="^(csv|xlsx)$", description="File export format ('csv' or 'xlsx')"),
    auth: Optional[Tuple[User, Workspace]] = Depends(get_optional_auth),
    db: Session = Depends(get_db),
) -> Response:
    """
    Generates a full 252-column UniHack dataset conforming exactly to the authoritative
    delivery schema, headers, and ordering with strict IDOR verification.
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
        file_bytes, media_type, filename = ExportService.generate_export_file(
            db=db,
            job_id=job_id,
            file_format=format,
        )
        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        )
    except Exception as exc:
        logger.exception(f"Export generation failed for job {job_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during dataset export: {str(exc)}",
        )


@router.get(
    "/{job_id}/preview",
    summary="Preview mapped 252-column export dataset with quality and fill-rate metrics",
)
def preview_export_mapping(
    job_id: uuid.UUID,
    limit: int = Query(5, ge=1, le=50, description="Number of preview records to return"),
    auth: Optional[Tuple[User, Workspace]] = Depends(get_optional_auth),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns mapped column headers, coverage metrics, and sample preview rows.
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
        return ExportService.preview_export(
            db=db,
            job_id=job_id,
            limit=limit,
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        )
    except Exception as exc:
        logger.exception(f"Export preview failed for job {job_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during export preview: {str(exc)}",
        )
