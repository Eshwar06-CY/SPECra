"""
Pydantic schemas for data ingestion, schema inspection, and paginated product retrieval.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ColumnSchemaInfo(BaseModel):
    """
    Detailed statistical and inferred metadata for a single dataset column.
    """
    column_name: str
    inferred_type: str  # numeric, text, boolean, datetime, empty
    pandas_dtype: str
    total_count: int
    null_count: int
    null_percentage: float
    unique_count: int
    uniqueness_ratio: float
    sample_values: List[Any]
    is_numeric: bool
    is_text: bool
    is_likely_identifier: bool
    is_likely_product_name: bool
    is_likely_category: bool


class SchemaAnalysisSummary(BaseModel):
    """
    Dataset-wide schema analysis summary with generic heuristics.
    """
    filename: str
    file_type: str
    row_count: int
    column_count: int
    columns: List[str]
    column_details: Dict[str, ColumnSchemaInfo]
    numeric_columns: List[str]
    text_columns: List[str]
    likely_identifier_columns: List[str]
    likely_product_name_columns: List[str]
    likely_category_columns: List[str]


class IngestionUploadResponse(BaseModel):
    """
    Response returned immediately after file upload and ingestion.
    """
    job_id: uuid.UUID
    filename: str
    file_type: str
    row_count: int
    column_count: int
    schema_summary: SchemaAnalysisSummary
    status: str
    processed_records: int
    failed_records: int
    message: str


class ProcessingJobResponse(BaseModel):
    """
    Response schema for querying processing job state.
    """
    id: uuid.UUID
    workspace_id: Optional[uuid.UUID] = None
    filename: str
    file_type: str
    status: str
    total_records: int
    processed_records: int
    failed_records: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime


class ProductRecordResponse(BaseModel):
    """
    Representation of an ingested product preserving raw data and detected master attributes.
    """
    id: uuid.UUID
    job_id: Optional[uuid.UUID] = None
    external_product_id: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    raw_data: Dict[str, Any]
    created_at: datetime


class PaginatedProductRecordsResponse(BaseModel):
    """
    Paginated container for ingested product records.
    """
    job_id: uuid.UUID
    total: int
    page: int
    page_size: int
    total_pages: int
    records: List[ProductRecordResponse]
