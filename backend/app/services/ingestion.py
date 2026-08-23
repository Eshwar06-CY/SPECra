"""
Data Ingestion Service for Deadlock.
Orchestrates file reading, schema analysis, ProcessingJob lifecycle, and atomic database persistence.
"""
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.config import settings
from app.models.product import Product, ProcessingJob
from app.utils.file_parser import (
    sanitize_filename,
    validate_file_format,
    load_dataset,
)
from app.utils.schema_analyzer import (
    analyze_schema,
    pick_best_candidate_column,
)
from app.schemas.ingestion import (
    SchemaAnalysisSummary,
    IngestionUploadResponse,
    ProcessingJobResponse,
    ProductRecordResponse,
    PaginatedProductRecordsResponse,
)

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Handles file ingestion workflows, dataset validation, dynamic schema discovery,
    and PostgreSQL persistence without hardcoded schema constraints.
    """

    @staticmethod
    def save_upload_file(file_bytes: bytes, raw_filename: str) -> Tuple[str, str, str]:
        """
        Saves uploaded file content to disk inside configured UPLOAD_DIR safely.
        Returns (saved_file_path, sanitized_filename, file_type).
        """
        is_valid, file_type, err_msg = validate_file_format(raw_filename)
        if not is_valid:
            raise ValueError(err_msg)

        # Enforce max size check
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(file_bytes) > max_bytes:
            raise ValueError(f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB.")

        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        sanitized = sanitize_filename(raw_filename)
        unique_name = f"{uuid.uuid4().hex[:8]}_{sanitized}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        return file_path, sanitized, file_type

    @staticmethod
    def ingest_dataset(
        db: Session,
        file_path: str,
        filename: str,
        file_type: str,
        workspace_id: Optional[uuid.UUID] = None,
    ) -> IngestionUploadResponse:
        """
        Processes dataset:
        1. Creates ProcessingJob with status 'processing' and workspace ownership
        2. Loads DataFrame and analyzes dynamic schema
        3. Persists Product records with complete original row in raw_data
        4. Updates ProcessingJob to 'completed' or 'failed'
        """
        job = ProcessingJob(
            workspace_id=workspace_id,
            filename=filename,
            file_type=file_type,
            status="processing",
            started_at=datetime.now(timezone.utc),
            total_records=0,
            processed_records=0,
            failed_records=0,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        try:
            # 1. Parse dataset into DataFrame
            df = load_dataset(file_path, file_type)
            row_count, col_count = df.shape
            job.total_records = row_count
            db.commit()

            # 2. Dynamic Schema Analysis
            schema_data = analyze_schema(df, filename=filename, file_type=file_type)
            schema_summary = SchemaAnalysisSummary(**schema_data)

            # Heuristics for master product columns (without forcing them)
            col_details = schema_data["column_details"]
            id_col = pick_best_candidate_column(schema_data["likely_identifier_columns"], col_details, "identifier")
            name_col = pick_best_candidate_column(schema_data["likely_product_name_columns"], col_details, "name")
            cat_col = pick_best_candidate_column(schema_data["likely_category_columns"], col_details, "category")

            # 3. Process and persist records
            products_to_create: List[Product] = []
            processed_count = 0
            failed_count = 0

            # Convert DF to records with NaN converted to None
            records_dict = df.to_dict(orient="records")

            for row in records_dict:
                try:
                    # Clean values for JSONB storage (convert NaN/NaT to None)
                    cleaned_raw_data = {
                        str(k): (None if pd.isna(v) else v) for k, v in row.items()
                    }

                    ext_id = None
                    if id_col and id_col in cleaned_raw_data and cleaned_raw_data[id_col] is not None:
                        ext_id = str(cleaned_raw_data[id_col]).strip()

                    prod_name = None
                    if name_col and name_col in cleaned_raw_data and cleaned_raw_data[name_col] is not None:
                        prod_name = str(cleaned_raw_data[name_col]).strip()

                    cat_val = None
                    if cat_col and cat_col in cleaned_raw_data and cleaned_raw_data[cat_col] is not None:
                        cat_val = str(cleaned_raw_data[cat_col]).strip()

                    product = Product(
                        job_id=job.id,
                        external_product_id=ext_id,
                        product_name=prod_name,
                        category=cat_val,
                        raw_data=cleaned_raw_data,
                    )
                    products_to_create.append(product)
                    processed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to prepare row for ingestion: {e}")
                    failed_count += 1

            # Bulk insert in chunks for performance
            if products_to_create:
                db.bulk_save_objects(products_to_create)
                db.commit()

            # Mark job complete
            job.status = "completed"
            job.processed_records = processed_count
            job.failed_records = failed_count
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(job)

            return IngestionUploadResponse(
                job_id=job.id,
                filename=filename,
                file_type=file_type,
                row_count=row_count,
                column_count=col_count,
                schema_summary=schema_summary,
                status="completed",
                processed_records=processed_count,
                failed_records=failed_count,
                message=f"Successfully ingested {processed_count} product records.",
            )

        except Exception as exc:
            db.rollback()
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.now(timezone.utc)
            db.commit()
            logger.exception(f"Ingestion failed for job {job.id}: {exc}")
            raise exc

    @staticmethod
    def get_job(db: Session, job_id: uuid.UUID) -> Optional[ProcessingJobResponse]:
        """
        Retrieves job status and statistics.
        """
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            return None
        return ProcessingJobResponse(
            id=job.id,
            workspace_id=job.workspace_id,
            filename=job.filename,
            file_type=job.file_type,
            status=job.status,
            total_records=job.total_records,
            processed_records=job.processed_records,
            failed_records=job.failed_records,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
            created_at=job.created_at,
        )

    @staticmethod
    def get_job_schema(db: Session, job_id: uuid.UUID) -> Optional[SchemaAnalysisSummary]:
        """
        Derives or reconstructs schema analysis from ingested raw_data of the job.
        """
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            return None

        # Fetch sample products from this job to analyze schema
        products = (
            db.query(Product)
            .filter(Product.job_id == job_id)
            .limit(1000)
            .all()
        )
        if not products:
            return SchemaAnalysisSummary(
                filename=job.filename,
                file_type=job.file_type,
                row_count=job.total_records,
                column_count=0,
                columns=[],
                column_details={},
                numeric_columns=[],
                text_columns=[],
                likely_identifier_columns=[],
                likely_product_name_columns=[],
                likely_category_columns=[],
            )

        raw_rows = [p.raw_data for p in products if p.raw_data]
        df = pd.DataFrame(raw_rows)
        schema_dict = analyze_schema(df, filename=job.filename, file_type=job.file_type)
        return SchemaAnalysisSummary(**schema_dict)

    @staticmethod
    def get_job_records(
        db: Session,
        job_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedProductRecordsResponse:
        """
        Returns paginated product records associated with a processing job.
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        page_size = min(page_size, 100)  # max limit to prevent memory spikes

        query = db.query(Product).filter(Product.job_id == job_id)
        total = query.count()
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        offset = (page - 1) * page_size
        products = query.order_by(Product.created_at.asc()).offset(offset).limit(page_size).all()

        record_responses = [
            ProductRecordResponse(
                id=p.id,
                job_id=p.job_id,
                external_product_id=p.external_product_id,
                product_name=p.product_name,
                category=p.category,
                raw_data=p.raw_data or {},
                created_at=p.created_at,
            )
            for p in products
        ]

        return PaginatedProductRecordsResponse(
            job_id=job_id,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            records=record_responses,
        )
