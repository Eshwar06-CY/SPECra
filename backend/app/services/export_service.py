"""
Export Service for Deadlock.
Coordinates job retrieval, validation verification, UniHack 252 output mapping,
preview generation, and CSV/XLSX delivery downloads.
"""
import uuid
import logging
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.product import Product, ProcessingJob, ValidationResult
from app.services.export_engine import UNIHACK_STATIC_HEADERS, UniHackOutputMapper, UniHackExportEngine
from app.services.validation_service import ValidationService

logger = logging.getLogger(__name__)


class ExportService:
    """
    Coordinates product export generation and quality summaries.
    """

    @staticmethod
    def get_job_export_data(
        db: Session,
        job_id: uuid.UUID,
    ) -> Tuple[ProcessingJob, List[Product], List[Dict[str, str]], Dict[str, Any]]:
        """
        Retrieves all products for a job, maps them to the 252 UniHack headers,
        and aggregates quality validation metrics.
        """
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            raise ValueError(f"Processing job '{job_id}' not found.")

        products: List[Product] = (
            db.query(Product)
            .filter(Product.job_id == job_id)
            .order_by(Product.created_at.asc())
            .all()
        )

        mapped_rows: List[Dict[str, str]] = []
        warning_products = 0
        error_products = 0
        populated_field_counts: Dict[str, int] = {h: 0 for h in UNIHACK_STATIC_HEADERS}

        for product in products:
            # 1. Map to 252 static headers
            row = UniHackOutputMapper.map_product_to_row(product)
            mapped_rows.append(row)

            # Count populated fields
            for k, v in row.items():
                if v and str(v).strip():
                    populated_field_counts[k] += 1

            # 2. Check validation status if available
            val_results = db.query(ValidationResult).filter(ValidationResult.product_id == product.id).all()
            if val_results:
                has_err = any(r.status == "ERROR" or (r.status and r.status.upper() == "ERROR") for r in val_results)
                has_warn = any(r.status == "WARNING" or (r.status and r.status.upper() == "WARNING") for r in val_results)
                if has_err:
                    error_products += 1
                elif has_warn:
                    warning_products += 1

        total_populated_cells = sum(populated_field_counts.values())
        total_possible_cells = len(products) * len(UNIHACK_STATIC_HEADERS) if products else 0
        fill_rate_pct = round((total_populated_cells / max(1, total_possible_cells)) * 100, 2)

        summary = {
            "job_id": str(job.id),
            "filename": job.filename,
            "total_products": len(products),
            "total_headers": len(UNIHACK_STATIC_HEADERS),
            "successfully_mapped_products": len(mapped_rows),
            "products_with_validation_errors": error_products,
            "products_with_validation_warnings": warning_products,
            "fill_rate_percent": fill_rate_pct,
            "fields_populated_count": sum(1 for c in populated_field_counts.values() if c > 0),
            "fields_blank_count": sum(1 for c in populated_field_counts.values() if c == 0),
            "populated_field_counts": populated_field_counts,
        }

        return job, products, mapped_rows, summary

    @staticmethod
    def generate_export_file(
        db: Session,
        job_id: uuid.UUID,
        file_format: str = "csv",
    ) -> Tuple[bytes, str, str]:
        """
        Generates and returns (file_bytes, media_type, download_filename) for a job.
        Supports 'csv' and 'xlsx'.
        """
        job, products, mapped_rows, _ = ExportService.get_job_export_data(db, job_id)
        fmt = file_format.lower().strip()

        base_name = job.filename.rsplit(".", 1)[0] if "." in job.filename else job.filename
        safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in base_name)

        if fmt in ("xlsx", "excel"):
            file_bytes = UniHackExportEngine.generate_xlsx_bytes(mapped_rows)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            download_name = f"UniHack_Export_{safe_name}.xlsx"
        else:
            file_bytes = UniHackExportEngine.generate_csv_bytes(mapped_rows)
            media_type = "text/csv; charset=utf-8"
            download_name = f"UniHack_Export_{safe_name}.csv"

        return file_bytes, media_type, download_name

    @staticmethod
    def get_export_preview(
        db: Session,
        job_id: uuid.UUID,
        sample_limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Returns a JSON preview of the 252-column export dataset with summary quality statistics.
        """
        job, products, mapped_rows, summary = ExportService.get_job_export_data(db, job_id)

        sample_rows = mapped_rows[:sample_limit]

        return {
            "job_id": str(job.id),
            "filename": job.filename,
            "total_products": len(products),
            "total_headers": len(UNIHACK_STATIC_HEADERS),
            "headers": UNIHACK_STATIC_HEADERS,
            "summary": summary,
            "sample_rows": sample_rows,
        }

    @staticmethod
    def preview_export(
        db: Session,
        job_id: uuid.UUID,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Alias for get_export_preview matching the API preview_export signature.
        """
        return ExportService.get_export_preview(db=db, job_id=job_id, sample_limit=limit)
