"""
Validation Service for Deadlock.
Coordinates product validation execution, database persistence in validation_results,
and retrieval of historical validation audit records.
"""
import uuid
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.product import Product, ProductAttribute, ValidationResult
from app.services.validation_engine import ProductValidationEngine, ProductValidationReport, ValidationIssue

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Service coordinating product quality assessment and database persistence.
    """

    @staticmethod
    def validate_and_save_product(
        db: Session,
        product_id: uuid.UUID,
    ) -> ProductValidationReport:
        """
        Executes complete deterministic validation over a product,
        persists the validation records in PostgreSQL (validation_results), and returns the summary report.
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product '{product_id}' not found.")

        # 1. Execute deterministic validation suite
        report = ProductValidationEngine.validate_product(product)

        # 2. Clean prior validation results for this product
        db.query(ValidationResult).filter(ValidationResult.product_id == product.id).delete()
        db.flush()

        # 3. Persist new validation issues into validation_results table
        for issue in report.results:
            attr_uuid = uuid.UUID(issue.attribute_id) if issue.attribute_id else None
            db_val = ValidationResult(
                product_id=product.id,
                attribute_id=attr_uuid,
                validation_type=issue.validation_type,
                status=issue.severity.value,  # ERROR, WARNING, INFO
                confidence_score=issue.confidence,
                message=issue.message,
                details={
                    "field": issue.field,
                    "current_value": issue.current_value,
                    "expected_condition": issue.expected_condition,
                    "validation_method": issue.validation_method,
                    **issue.details,
                },
            )
            db.add(db_val)

        db.commit()

        return report

    @staticmethod
    def get_product_validation_report(
        db: Session,
        product_id: uuid.UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves the persisted validation results for a product, formatting them into a standard report.
        If no validation has been executed yet, runs a live on-demand assessment.
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None

        val_records = db.query(ValidationResult).filter(ValidationResult.product_id == product.id).all()

        if not val_records:
            # Generate and persist on-demand
            report = ValidationService.validate_and_save_product(db, product_id)
            return report.model_dump()

        # Format from database records
        issues: List[ValidationIssue] = []
        for r in val_records:
            details = r.details or {}
            sev_str = r.status.upper() if r.status else "WARNING"
            issues.append(ValidationIssue(
                validation_type=r.validation_type,
                severity=sev_str,
                field=details.get("field", "unknown"),
                current_value=details.get("current_value"),
                expected_condition=details.get("expected_condition"),
                message=r.message or "",
                validation_method=details.get("validation_method", "DETERMINISTIC"),
                confidence=r.confidence_score if r.confidence_score is not None else 1.0,
                attribute_id=str(r.attribute_id) if r.attribute_id else None,
                details=details,
            ))

        score, status, errs, warns, infos = ProductValidationEngine.calculate_quality_score(issues)

        return {
            "product_id": str(product.id),
            "status": status.value,
            "score": score,
            "errors": errs,
            "warnings": warns,
            "info": infos,
            "results": [i.model_dump() for i in issues],
        }
