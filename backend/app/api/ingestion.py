"""
API router for Data Ingestion, dynamic schema inspection, and product preview endpoints.
"""
import uuid
import logging
from typing import Optional, Tuple
from fastapi import APIRouter, Depends, File, UploadFile, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.ingestion import IngestionService
from app.api.deps import get_optional_auth, get_current_workspace
from app.models.user import User, Workspace
from app.models.product import ProcessingJob
from app.schemas.ingestion import (
    IngestionUploadResponse,
    ProcessingJobResponse,
    SchemaAnalysisSummary,
    PaginatedProductRecordsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post(
    "/upload",
    response_model=IngestionUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and dynamically ingest CSV or XLSX dataset",
)
async def upload_dataset(
    file: UploadFile = File(..., description="CSV or XLSX dataset file to ingest"),
    auth: Optional[Tuple[User, Workspace]] = Depends(get_optional_auth),
    db: Session = Depends(get_db),
):
    """
    Accepts arbitrary industrial product datasets (CSV or XLSX) via multipart/form-data.
    Associates job with the authenticated workspace if present.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    try:
        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes).",
            )

        saved_path, sanitized_name, file_type = IngestionService.save_upload_file(
            file_bytes=content,
            raw_filename=file.filename,
        )

        workspace_id = auth[1].id if auth else None

        response = IngestionService.ingest_dataset(
            db=db,
            file_path=saved_path,
            filename=sanitized_name,
            file_type=file_type,
            workspace_id=workspace_id,
        )
        return response

    except HTTPException:
        raise
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.exception(f"Unhandled error during file ingestion: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the dataset: {str(exc)}",
        )


@router.get(
    "/jobs",
    response_model=list[ProcessingJobResponse],
    summary="List all dataset ingestion and processing jobs",
)
def list_all_jobs(
    auth: Optional[Tuple[User, Workspace]] = Depends(get_optional_auth),
    db: Session = Depends(get_db),
):
    """
    Returns jobs filtered by current authenticated workspace (or all development jobs if unauthenticated demo).
    """
    query = db.query(ProcessingJob)
    if auth:
        workspace_id = auth[1].id
        query = query.filter((ProcessingJob.workspace_id == workspace_id) | (ProcessingJob.workspace_id.is_(None)))
    jobs = query.order_by(ProcessingJob.created_at.desc()).all()
    return jobs


@router.get(
    "/{job_id}",
    response_model=ProcessingJobResponse,
    summary="Get processing job status and statistics",
)
def get_job_status(
    job_id: uuid.UUID,
    auth: Optional[Tuple[User, Workspace]] = Depends(get_optional_auth),
    db: Session = Depends(get_db),
):
    """
    Retrieves job status with strict IDOR verification.
    """
    job = IngestionService.get_job(db=db, job_id=job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Processing job '{job_id}' not found.",
        )
    if auth and job.workspace_id and job.workspace_id != auth[1].id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )
    return job


@router.get(
    "/{job_id}/schema",
    response_model=SchemaAnalysisSummary,
    summary="Get dynamically detected dataset schema",
)
def get_job_schema(
    job_id: uuid.UUID,
    auth: Optional[Tuple[User, Workspace]] = Depends(get_optional_auth),
    db: Session = Depends(get_db),
):
    """
    Returns the detected schema with strict IDOR verification.
    """
    job = IngestionService.get_job(db=db, job_id=job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Processing job '{job_id}' not found.",
        )
    if auth and job.workspace_id and job.workspace_id != auth[1].id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )
    schema = IngestionService.get_job_schema(db=db, job_id=job_id)
    return schema


@router.get(
    "/{job_id}/records",
    response_model=PaginatedProductRecordsResponse,
    summary="Get paginated preview of ingested product records",
)
def get_job_records(
    job_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number starting at 1"),
    page_size: int = Query(20, ge=1, le=100, description="Records per page (max 100)"),
    auth: Optional[Tuple[User, Workspace]] = Depends(get_optional_auth),
    db: Session = Depends(get_db),
):
    """
    Returns product records with IDOR ownership validation.
    """
    job = IngestionService.get_job(db=db, job_id=job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Processing job '{job_id}' not found.",
        )
    if auth and job.workspace_id and job.workspace_id != auth[1].id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource.",
        )
    return IngestionService.get_job_records(
        db=db,
        job_id=job_id,
        page=page,
        page_size=page_size,
    )
