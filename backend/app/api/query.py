"""
API endpoints for Phase 3 Natural-Language Product Query Engine.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.query import QueryRequest, QueryResponse, QueryPreviewResponse
from app.services.query_service import QueryService

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
):
    """
    Interprets natural language query and returns the structured QueryPlan,
    available fields, and unavailable fields before querying the database.
    """
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
    db: Session = Depends(get_db),
):
    """
    Interprets user natural language request, queries PostgreSQL using safe
    whitelisted filters, and returns matching products with requested fields and evidence.
    """
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
