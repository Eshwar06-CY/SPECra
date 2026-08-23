"""
Query Plan models and schemas for Natural-Language Product Query Engine.
"""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from enum import Enum


class FilterOperator(str, Enum):
    EQUALS = "equals"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    IS_NOT_EMPTY = "is_not_empty"


class QueryFilter(BaseModel):
    field: str = Field(..., description="Allowed canonical product field name")
    operator: FilterOperator = Field(default=FilterOperator.CONTAINS, description="Comparison operator")
    value: Optional[str] = Field(default="", description="Value to match")


class QueryPlan(BaseModel):
    filters: List[QueryFilter] = Field(default_factory=list, description="List of validated filter criteria")
    requested_fields: List[str] = Field(default_factory=list, description="List of validated canonical field names")
    explanation: Optional[str] = Field(default=None, description="Human-friendly interpretation summary")


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language search query")
    limit: Optional[int] = Field(default=100, ge=1, le=1000, description="Max records to return")


class ProductEvidenceSummary(BaseModel):
    source_location: str
    source_text: str
    provenance: str


class QueryResultItem(BaseModel):
    product_id: str
    part_number: Optional[str] = None
    product_name: Optional[str] = None
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    product_type: Optional[str] = None
    fields: Dict[str, Any] = Field(default_factory=dict, description="Requested field key-value pairs")
    evidence: Dict[str, ProductEvidenceSummary] = Field(default_factory=dict, description="Source evidence per field")


class QueryResponse(BaseModel):
    job_id: str
    query: str
    interpreted_request: QueryPlan
    total_results: int
    results: List[QueryResultItem]
    available_fields: List[str]
    unavailable_fields: List[str]
    status: str = "completed"
    message: Optional[str] = None


class QueryPreviewResponse(BaseModel):
    job_id: str
    query: str
    query_plan: QueryPlan
    available_fields: List[str]
    unavailable_fields: List[str]
    can_execute: bool = True
    message: Optional[str] = None
