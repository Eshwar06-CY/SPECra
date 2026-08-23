"""
SQLAlchemy models for Deadlock Industrial Product Intelligence Engine.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Product(Base):
    """
    Industrial Product master record.
    Dynamic attributes are stored in related ProductAttribute records.
    """
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("processing_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    external_product_id = Column(String(255), nullable=True, index=True)
    product_name = Column(String(512), nullable=True, index=True)
    category = Column(String(255), nullable=True, index=True)
    raw_data = Column(JSONB, nullable=True, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    attributes = relationship(
        "ProductAttribute",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    evidences = relationship(
        "Evidence",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    validation_results = relationship(
        "ValidationResult",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    enrichments = relationship(
        "ProductEnrichment",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_products_category_name", "category", "product_name"),
    )

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.product_name}', category='{self.category}')>"


class ProductAttribute(Base):
    """
    Dynamic attribute store for industrial products (e.g., pressure, voltage, tolerance).
    Enables schema flexibility across diverse product categories.
    """
    __tablename__ = "product_attributes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attribute_name = Column(String(255), nullable=False, index=True)
    attribute_value = Column(Text, nullable=True)
    normalized_value = Column(Text, nullable=True)
    unit = Column(String(64), nullable=True)
    confidence_score = Column(Float, nullable=True, default=1.0)
    status = Column(String(64), nullable=True, default="raw", index=True)  # raw, extracted, enriched, validated, reviewed
    extraction_method = Column(String(128), nullable=True)  # regex, ocr, llm_extraction, manual_entry

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    product = relationship("Product", back_populates="attributes")
    evidences = relationship(
        "Evidence",
        back_populates="attribute",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    validation_results = relationship(
        "ValidationResult",
        back_populates="attribute",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_product_attributes_prod_attr", "product_id", "attribute_name"),
    )

    def __repr__(self):
        return f"<ProductAttribute(id={self.id}, name='{self.attribute_name}', value='{self.attribute_value}')>"


class Evidence(Base):
    """
    Provenance and audit trail connecting extracted product attributes
    back to source documents (PDF pages, CSV rows, image bounding boxes).
    """
    __tablename__ = "evidences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attribute_id = Column(
        UUID(as_uuid=True),
        ForeignKey("product_attributes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    source_name = Column(String(512), nullable=False)  # file name or URI
    source_type = Column(String(64), nullable=False)  # pdf, image, csv, xlsx, web
    source_location = Column(String(512), nullable=False)  # page, row, bbox, coordinate
    page_number = Column(Integer, nullable=True)
    source_text = Column(Text, nullable=True)
    evidence_metadata = Column(JSONB, nullable=True, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    product = relationship("Product", back_populates="evidences")
    attribute = relationship("ProductAttribute", back_populates="evidences")

    def __repr__(self):
        return f"<Evidence(id={self.id}, source='{self.source_name}', type='{self.source_type}')>"


class ValidationResult(Base):
    """
    Validation and quality assessment outcomes for product specifications.
    """
    __tablename__ = "validation_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attribute_id = Column(
        UUID(as_uuid=True),
        ForeignKey("product_attributes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    validation_type = Column(String(128), nullable=False)  # schema, range, physical_consistency, cross_source
    status = Column(String(64), nullable=False, index=True)  # pass, fail, warning, pending_review
    confidence_score = Column(Float, nullable=True)
    message = Column(Text, nullable=True)
    details = Column(JSONB, nullable=True, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    product = relationship("Product", back_populates="validation_results")
    attribute = relationship("ProductAttribute", back_populates="validation_results")

    def __repr__(self):
        return f"<ValidationResult(id={self.id}, type='{self.validation_type}', status='{self.status}')>"


class ProcessingJob(Base):
    """
    Tracks bulk file ingestion, extraction, and batch pipeline jobs.
    Associated with a Workspace for strict multi-tenant isolation.
    """
    __tablename__ = "processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workspace_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    filename = Column(String(512), nullable=False)
    file_type = Column(String(64), nullable=False)  # csv, xlsx, pdf, image_zip
    status = Column(String(64), nullable=False, default="pending", index=True)  # pending, processing, completed, failed
    total_records = Column(Integer, nullable=False, default=0)
    processed_records = Column(Integer, nullable=False, default=0)
    failed_records = Column(Integer, nullable=False, default=0)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    workspace = relationship("Workspace", back_populates="jobs")

    def __repr__(self):
        return f"<ProcessingJob(id={self.id}, filename='{self.filename}', workspace_id={self.workspace_id}, status='{self.status}')>"


class ProductEnrichment(Base):
    """
    Persisted deterministic and verified cross-field enrichments.
    Maintains strict source provenance, normalization, and confidence tracking.
    """
    __tablename__ = "product_enrichments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    product_id = Column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field_name = Column(String(255), nullable=False, index=True)
    value = Column(Text, nullable=False)
    normalized_value = Column(Text, nullable=True)
    unit = Column(String(64), nullable=True)
    source_name = Column(String(512), nullable=True)
    source_type = Column(String(64), nullable=False, default="input_dataset")
    source_location = Column(String(512), nullable=True)
    source_text = Column(Text, nullable=True)
    provenance = Column(String(64), nullable=False, default="DERIVED")  # DIRECT, DERIVED, DETERMINISTIC
    extraction_method = Column(String(128), nullable=False, default="DETERMINISTIC")
    confidence_score = Column(Float, nullable=False, default=1.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    product = relationship("Product", back_populates="enrichments")

    __table_args__ = (
        Index("ix_product_enrichments_prod_field", "product_id", "field_name"),
    )

    def __repr__(self):
        return f"<ProductEnrichment(id={self.id}, field='{self.field_name}', value='{self.value}')>"
