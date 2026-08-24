import uuid
import logging
from typing import Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.query import QueryRequest, QueryResponse, QueryPreviewResponse
from app.services.query_service import QueryService
from app.api.deps import get_optional_auth
from app.models.user import User, Workspace
from app.models.product import ProcessingJob

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["Natural Language Query"])


@router.post(
    "/{job_id}/preview",
    response_model=QueryPreviewResponse,
    summary="Preview QueryPlan interpretation before executing",
)
async def preview_query(
    job_id: str,
    payload: QueryRequest,
    auth: Optional[Tuple[User, Workspace]] = Depends(get_optional_auth),
    db: Session = Depends(get_db),
):
    """
    Interprets natural language query and returns the structured QueryPlan,
    available fields, and unavailable fields before querying the database with IDOR check.
    """
    try:
        job_uuid = uuid.UUID(job_id)
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_uuid).first()
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
    except HTTPException:
        raise
    except ValueError:
        pass

    try:
        preview = await QueryService.preview_query_async(job_id=job_id, query=payload.query)
        return preview
    except Exception as exc:
        logger.error(f"Error previewing query for job {job_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview query interpretation: {str(exc)}",
        )


@router.post(
    "/{job_id}",
    response_model=QueryResponse,
    summary="Execute Natural Language Catalog Query against PostgreSQL",
)
async def execute_query(
    job_id: str,
    payload: QueryRequest,
    auth: Optional[Tuple[User, Workspace]] = Depends(get_optional_auth),
    db: Session = Depends(get_db),
):
    """
    Interprets user natural language request, queries PostgreSQL using safe
    whitelisted filters, and returns matching products with requested fields and evidence with IDOR check.
    """
    try:
        job_uuid = uuid.UUID(job_id)
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_uuid).first()
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
    except HTTPException:
        raise
    except ValueError:
        pass

    try:
        response = await QueryService.execute_query(
            db=db,
            job_id=job_id,
            query=payload.query,
            limit=payload.limit or 100,
        )
        return response
    except Exception as exc:
        logger.error(f"Error executing natural language query for job {job_id}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query execution failed: {str(exc)}",
        )
