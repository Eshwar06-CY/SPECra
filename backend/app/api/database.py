"""
Database health and status inspection API endpoints.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text, inspect
from sqlalchemy.orm import Session

from app.core.database import get_db, engine, Base
import app.models  # Ensure models are loaded

router = APIRouter(prefix="/database", tags=["database"])


@router.get("/status")
def get_database_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Test database connection and return current PostgreSQL database name and status.
    """
    try:
        result = db.execute(text("SELECT current_database();")).scalar()
        return {
            "database": "postgresql",
            "database_name": result or "deadlock",
            "status": "connected",
        }
    except Exception as e:
        # Return structured error response without exposing credentials
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "database": "postgresql",
                "status": "disconnected",
                "error": "Failed to connect to the database server. Please verify configuration.",
            },
        )


@router.get("/tables")
def get_database_tables() -> Dict[str, List[str]]:
    """
    Return the names of the Deadlock application database tables.
    """
    # Return defined model tables from Base metadata
    model_tables = list(Base.metadata.tables.keys())
    return {
        "tables": model_tables,
    }
