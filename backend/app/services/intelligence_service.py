"""
Intelligence Service for Deadlock.
Coordinates batch product intelligence extraction over ingested datasets,
asynchronous concurrency throttling, error isolation, and PostgreSQL persistence using Google Gemini.
"""
import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.product import Product, ProductAttribute, Evidence, ProcessingJob
from app.ai.product_intelligence import ProductIntelligenceEngine, get_ai_provider
from app.ai.schemas import ProductIntelligence, Provenance, ExtractionMethod

logger = logging.getLogger(__name__)


def classify_ai_exception(exc: Exception) -> Tuple[str, str]:
    """
    Classifies exceptions from AI provider calls into clear, standard diagnostic categories:
    - rate_limit (429)
    - provider_unavailable (503)
    - timeout (TimeoutError)
    - provider_error (generic API or connection failure)
    """
    err_str = str(exc).lower()
    err_type = type(exc).__name__

    if "429" in err_str or "quota" in err_str or "rate limit" in err_str or "resource_exhausted" in err_str:
        return "rate_limit", f"Gemini API rate/quota limit exceeded (429): {str(exc)}"
    elif "503" in err_str or "unavailable" in err_str or "high demand" in err_str:
        return "provider_unavailable", f"Gemini model is temporarily experiencing high demand (503): {str(exc)}"
    elif "timeout" in err_type.lower() or "timeouterror" in err_type.lower() or "deadline" in err_str:
        return "timeout", f"Gemini API request timed out: {str(exc)}"
    else:
        return "provider_error", f"Gemini provider error ({err_type}): {str(exc)}"


class IntelligenceService:
    """
    Business service executing Gemini product intelligence across database records.
    """

    @staticmethod
    async def get_health() -> Dict[str, Any]:
        """Returns health and connection status of the Google Gemini provider."""
        provider = get_ai_provider()
        return await provider.health_check()

    @staticmethod
    async def analyze_job_products(
        db: Session,
        job_id: uuid.UUID,
        limit: Optional[int] = None,
        product_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        """
        Runs batch Gemini AI intelligence analysis over all or limited products belonging to a ProcessingJob.
        Applies concurrency rate limits and isolates individual record failures.
        """
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job:
            raise ValueError(f"Processing job '{job_id}' not found.")

        query = db.query(Product).filter(Product.job_id == job_id)
        if product_id:
            query = query.filter(Product.id == product_id)
        else:
            query = query.order_by(Product.created_at.asc())
            if limit and limit > 0:
                query = query.limit(limit)

        products: List[Product] = query.all()
        if not products:
            return {
                "job_id": str(job_id),
                "provider": "gemini",
                "model": settings.GEMINI_MODEL,
                "total": 0,
                "processed": 0,
                "failed": 0,
                "status": "completed",
                "message": "No products found for this job.",
            }

        engine = ProductIntelligenceEngine()
        semaphore = asyncio.Semaphore(settings.GEMINI_MAX_CONCURRENCY)

        processed_count = 0
        failed_count = 0
        errors_list: List[Dict[str, str]] = []

        async def _process_single(product: Product):
            nonlocal processed_count, failed_count
            async with semaphore:
                try:
                    raw_data = product.raw_data or {}
                    # 1. Run AI semantic analysis
                    intel: ProductIntelligence = await engine.analyze_product(raw_data=raw_data)

                    # 2. Run Deterministic Reconciliation Engine
                    from app.ai.reconciliation import reconcile_product_intelligence
                    intel = reconcile_product_intelligence(
                        canonical=intel,
                        raw_data=raw_data,
                        source_filename=job.filename,
                    )

                    # 3. Clean any existing attributes/evidences if re-analyzing product
                    db.query(ProductAttribute).filter(ProductAttribute.product_id == product.id).delete()
                    db.flush()

                    # 4. Update Master Product information non-destructively
                    identity = intel.identity
                    if identity.product_name:
                        product.product_name = identity.product_name
                    if identity.product_type:
                        product.category = identity.product_type
                    part_num = identity.manufacturer_part_number or identity.part_number or identity.sku
                    if part_num and not product.external_product_id:
                        product.external_product_id = part_num

                    # 5. Persist explicit identity elements as searchable ProductAttributes
                    identity_attributes = []
                    brand = identity.brand_name
                    if brand:
                        identity_attributes.append(
                            ("brand", brand, identity.brand_evidence)
                        )
                    manufacturer = identity.manufacturer_name
                    if manufacturer:
                        identity_attributes.append(
                            ("manufacturer", manufacturer, identity.manufacturer_evidence)
                        )
                    if identity.product_type:
                        identity_attributes.append(
                            ("product_type", identity.product_type, identity.product_type_evidence)
                        )
                    if identity.manufacturer_part_number:
                        identity_attributes.append(
                            ("manufacturer_part_number", identity.manufacturer_part_number, identity.part_number_evidence)
                        )
                    elif identity.part_number:
                        identity_attributes.append(
                            ("part_number", identity.part_number, identity.part_number_evidence)
                        )

                    for attr_name, attr_val, ev_candidate in identity_attributes:
                        ev_src_loc = (ev_candidate.source_location if ev_candidate and ev_candidate.source_location else ("Part_Manuf" if attr_name == "manufacturer" else "Part_Desc"))
                        ev_src_txt = (ev_candidate.source_text if ev_candidate and ev_candidate.source_text else str(attr_val))
                        ev_prov = (ev_candidate.provenance.value if ev_candidate and hasattr(ev_candidate.provenance, "value") else "DIRECT")
                        ident_method = "DETERMINISTIC" if ev_prov == "DIRECT" else "LLM"

                        db_attr = ProductAttribute(
                            product_id=product.id,
                            attribute_name=attr_name,
                            attribute_value=str(attr_val),
                            normalized_value=str(attr_val),
                            confidence_score=ev_candidate.confidence if ev_candidate else 0.98,
                            status="extracted",
                            extraction_method=ident_method,
                        )
                        db.add(db_attr)
                        db.flush()

                        db_evidence = Evidence(
                            product_id=product.id,
                            attribute_id=db_attr.id,
                            source_name=job.filename,
                            source_type="input_dataset",
                            source_location=ev_src_loc,
                            source_text=ev_src_txt,
                            evidence_metadata={
                                "provenance": ev_prov,
                                "original_value": ev_src_txt,
                                "notes": f"Identity element extracted via Gemini Intelligence Engine ({engine.provider.model_name})"
                            }
                        )
                        db.add(db_evidence)

                    # 6. Persist features as ProductAttributes if discovered
                    for feat in intel.features:
                        db_attr = ProductAttribute(
                            product_id=product.id,
                            attribute_name=f"feature_{feat.name.lower().replace(' ', '_')}",
                            attribute_value=feat.value,
                            normalized_value=feat.value,
                            confidence_score=feat.confidence,
                            status="extracted",
                            extraction_method="LLM",
                        )
                        db.add(db_attr)
                        db.flush()

                        ev = feat.evidence
                        db_evidence = Evidence(
                            product_id=product.id,
                            attribute_id=db_attr.id,
                            source_name=job.filename,
                            source_type=ev.source_type if ev else "input_dataset",
                            source_location=ev.source_location if ev and ev.source_location else "Part_Desc",
                            source_text=ev.source_text if ev and ev.source_text else feat.value,
                            evidence_metadata={
                                "provenance": feat.provenance.value if hasattr(feat.provenance, "value") else str(feat.provenance),
                                "notes": f"Feature extracted via Gemini Intelligence Engine ({engine.provider.model_name})"
                            }
                        )
                        db.add(db_evidence)

                    # 3. Persist dynamic product attributes and evidence
                    for attr in intel.attributes:
                        db_attr = ProductAttribute(
                            product_id=product.id,
                            attribute_name=attr.name,
                            attribute_value=attr.value,
                            normalized_value=attr.normalized_value,
                            unit=attr.unit,
                            confidence_score=attr.confidence,
                            status="enriched" if attr.provenance == Provenance.ENRICHED else "extracted",
                            extraction_method=attr.extraction_method.value if hasattr(attr.extraction_method, "value") else str(attr.extraction_method),
                        )
                        db.add(db_attr)
                        db.flush()  # to get db_attr.id

                        # Record evidence provenance
                        evidence_src_type = "input_dataset"
                        evidence_text = attr.evidence_text or attr.original_value or attr.value
                        evidence_loc = attr.source_field or "Part_Desc"
                        
                        db_evidence = Evidence(
                            product_id=product.id,
                            attribute_id=db_attr.id,
                            source_name=job.filename,
                            source_type=evidence_src_type,
                            source_location=evidence_loc,
                            source_text=evidence_text,
                            evidence_metadata={
                                "provenance": attr.provenance.value if hasattr(attr.provenance, "value") else str(attr.provenance),
                                "original_value": attr.original_value,
                                "notes": f"Extracted via Gemini Intelligence Engine ({engine.provider.model_name})"
                            }
                        )
                        db.add(db_evidence)

                    processed_count += 1
                except Exception as exc:
                    failed_count += 1
                    error_category, classified_msg = classify_ai_exception(exc)
                    raw_type = type(exc).__name__
                    logger.exception(
                        f"Product intelligence processing failed for product {product.id} in job {job_id}: [{error_category}] {classified_msg}",
                        exc_info=True,
                        extra={
                            "job_id": str(job_id),
                            "product_id": str(product.id),
                            "error_type": error_category,
                            "raw_exception": raw_type,
                            "error_message": classified_msg,
                        },
                    )
                    errors_list.append({
                        "product_id": str(product.id),
                        "error_type": error_category,
                        "raw_type": raw_type,
                        "message": classified_msg,
                    })

        # Execute concurrent tasks with error isolation
        tasks = [_process_single(p) for p in products]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Commit all successful database mutations
        db.commit()

        return {
            "job_id": str(job_id),
            "provider": engine.provider.provider_name,
            "model": engine.provider.model_name,
            "total": len(products),
            "processed": processed_count,
            "failed": failed_count,
            "status": "completed" if failed_count == 0 else ("partial" if processed_count > 0 else "failed"),
            "errors": errors_list,
        }

    @staticmethod
    async def analyze_single_product(
        db: Session,
        product_id: uuid.UUID,
    ) -> Dict[str, Any]:
        """
        Runs Gemini AI intelligence analysis and deterministic reconciliation for a single product record.
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product '{product_id}' not found.")

        job = db.query(ProcessingJob).filter(ProcessingJob.id == product.job_id).first() if product.job_id else None
        job_filename = job.filename if job else "input_dataset"

        engine = ProductIntelligenceEngine()
        raw_data = product.raw_data or {}

        # 1. Run AI semantic analysis
        intel: ProductIntelligence = await engine.analyze_product(raw_data=raw_data)

        # 2. Run Deterministic Reconciliation Engine
        from app.ai.reconciliation import reconcile_product_intelligence
        intel = reconcile_product_intelligence(
            canonical=intel,
            raw_data=raw_data,
            source_filename=job_filename,
        )

        # 3. Clean any existing attributes/evidences if re-analyzing product
        db.query(ProductAttribute).filter(ProductAttribute.product_id == product.id).delete()
        db.flush()

        # 4. Update Master Product information non-destructively
        identity = intel.identity
        if identity.product_name:
            product.product_name = identity.product_name
        if identity.product_type:
            product.category = identity.product_type
        part_num = identity.manufacturer_part_number or identity.part_number or identity.sku
        if part_num and not product.external_product_id:
            product.external_product_id = part_num

        # 5. Persist explicit identity elements as searchable ProductAttributes
        identity_attributes = []
        brand = identity.brand_name
        if brand:
            identity_attributes.append(
                ("brand", brand, identity.brand_evidence)
            )
        manufacturer = identity.manufacturer_name
        if manufacturer:
            identity_attributes.append(
                ("manufacturer", manufacturer, identity.manufacturer_evidence)
            )
        if identity.product_type:
            identity_attributes.append(
                ("product_type", identity.product_type, identity.product_type_evidence)
            )
        if identity.manufacturer_part_number:
            identity_attributes.append(
                ("manufacturer_part_number", identity.manufacturer_part_number, identity.part_number_evidence)
            )
        elif identity.part_number:
            identity_attributes.append(
                ("part_number", identity.part_number, identity.part_number_evidence)
            )

        for attr_name, attr_val, ev_candidate in identity_attributes:
            ev_src_loc = (ev_candidate.source_location if ev_candidate and ev_candidate.source_location else ("Part_Manuf" if attr_name == "manufacturer" else "Part_Desc"))
            ev_src_txt = (ev_candidate.source_text if ev_candidate and ev_candidate.source_text else str(attr_val))
            ev_prov = (ev_candidate.provenance.value if ev_candidate and hasattr(ev_candidate.provenance, "value") else "DIRECT")
            ident_method = "DETERMINISTIC" if ev_prov == "DIRECT" else "LLM"

            db_attr = ProductAttribute(
                product_id=product.id,
                attribute_name=attr_name,
                attribute_value=str(attr_val),
                normalized_value=str(attr_val),
                confidence_score=ev_candidate.confidence if ev_candidate else 0.98,
                status="extracted",
                extraction_method=ident_method,
            )
            db.add(db_attr)
            db.flush()

            db_evidence = Evidence(
                product_id=product.id,
                attribute_id=db_attr.id,
                source_name=job_filename,
                source_type="input_dataset",
                source_location=ev_src_loc,
                source_text=ev_src_txt,
                evidence_metadata={
                    "provenance": ev_prov,
                    "original_value": ev_src_txt,
                    "notes": f"Identity element extracted via Gemini Intelligence Engine ({engine.provider.model_name})"
                }
            )
            db.add(db_evidence)

        # 6. Persist features as ProductAttributes
        for feat in intel.features:
            db_attr = ProductAttribute(
                product_id=product.id,
                attribute_name=f"feature_{feat.name.lower().replace(' ', '_')}",
                attribute_value=feat.value,
                normalized_value=feat.value,
                confidence_score=feat.confidence,
                status="extracted",
                extraction_method="LLM",
            )
            db.add(db_attr)
            db.flush()

            ev = feat.evidence
            db_evidence = Evidence(
                product_id=product.id,
                attribute_id=db_attr.id,
                source_name=job_filename,
                source_type=ev.source_type if ev else "input_dataset",
                source_location=ev.source_location if ev and ev.source_location else "Part_Desc",
                source_text=ev.source_text if ev and ev.source_text else feat.value,
                evidence_metadata={
                    "provenance": feat.provenance.value if hasattr(feat.provenance, "value") else str(feat.provenance),
                    "notes": f"Feature extracted via Gemini Intelligence Engine ({engine.provider.model_name})"
                }
            )
            db.add(db_evidence)

        # 7. Persist dynamic product attributes and evidence
        for attr in intel.attributes:
            db_attr = ProductAttribute(
                product_id=product.id,
                attribute_name=attr.name,
                attribute_value=attr.value,
                normalized_value=attr.normalized_value,
                unit=attr.unit,
                confidence_score=attr.confidence,
                status="enriched" if attr.provenance == Provenance.ENRICHED else "extracted",
                extraction_method=attr.extraction_method.value if hasattr(attr.extraction_method, "value") else str(attr.extraction_method),
            )
            db.add(db_attr)
            db.flush()

            evidence_src_type = "input_dataset"
            evidence_text = attr.evidence_text or attr.original_value or attr.value
            evidence_loc = attr.source_field or "Part_Desc"

            db_evidence = Evidence(
                product_id=product.id,
                attribute_id=db_attr.id,
                source_name=job_filename,
                source_type=evidence_src_type,
                source_location=evidence_loc,
                source_text=evidence_text,
                evidence_metadata={
                    "provenance": attr.provenance.value if hasattr(attr.provenance, "value") else str(attr.provenance),
                    "original_value": attr.original_value,
                    "notes": f"Extracted via Gemini Intelligence Engine ({engine.provider.model_name})"
                }
            )
            db.add(db_evidence)

        db.commit()

        # Clean any redundant duplicate features
        IntelligenceService.normalize_and_clean_product(db, product.id)

        return {
            "product_id": str(product.id),
            "status": "completed",
            "provider": "gemini",
            "model": engine.provider.model_name,
            "total_attributes": len(identity_attributes) + len(intel.attributes),
        }

    @staticmethod
    def normalize_and_clean_product(db: Session, product_id: uuid.UUID) -> None:
        """
        Safely removes duplicate qualitative features that merely restate structured attributes
        and normalizes evidence metadata to use the active configured model name.
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return

        structured_attr_names = {
            a.attribute_name.lower().replace(" ", "_")
            for a in product.attributes
            if not a.attribute_name.startswith("feature_")
        }

        has_dimensions = bool(structured_attr_names.intersection({"width", "length", "height"}))
        has_quantity = bool(structured_attr_names.intersection({"pack_quantity", "quantity", "selling_quantity"}))

        dimension_keys = {"dimensions", "dimension", "size", "width", "length", "height"}
        quantity_keys = {"pack_quantity", "package_quantity", "quantity", "selling_quantity"}

        for a in list(product.attributes):
            # 1. Deduplicate redundant features
            if a.attribute_name.startswith("feature_"):
                feat_key = a.attribute_name.replace("feature_", "").lower().replace("-", "_")
                if has_dimensions and (feat_key in dimension_keys or any(k in feat_key for k in ["dimension", "width_by_length", "length_by_width"])):
                    db.delete(a)
                    continue
                if has_quantity and (feat_key in quantity_keys or "pack_quantity" in feat_key or "package_quantity" in feat_key):
                    db.delete(a)
                    continue

            # 2. Normalize evidence notes to reflect current configured model
            for ev in a.evidences:
                if ev.evidence_metadata and isinstance(ev.evidence_metadata, dict):
                    notes = ev.evidence_metadata.get("notes", "")
                    if "gemini-" in notes and f"({settings.GEMINI_MODEL})" not in notes:
                        import re
                        updated_notes = re.sub(r"gemini-[0-9\.]+-flash", settings.GEMINI_MODEL, notes)
                        ev.evidence_metadata = {**ev.evidence_metadata, "notes": updated_notes}

        db.commit()

    @staticmethod
    def get_product_intelligence_details(db: Session, product_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Retrieves complete detailed intelligence for a product, structured as:
        - product (core DB master record)
        - identity (canonical product_name, product_type, brand, manufacturer, part_number)
        - attributes (dynamically discovered specifications with normalized values, units, and evidence)
        - evidence (flattened list of all evidence items)
        - conflicts (conflicts detected or recorded)
        - confidence (overall confidence score)
        """
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None

        # Build lookup of attributes
        attr_by_name: Dict[str, ProductAttribute] = {}
        attributes_data = []
        all_evidences_data = []

        # Canonical identity keys to surface cleanly in identity sub-dictionary
        identity_keys = {
            "brand", "manufacturer", "product_type",
            "manufacturer_part_number", "part_number", "sku", "trade_name"
        }

        # Canonical identity dictionary populated from master product & identity attributes
        identity_dict = {
            "product_name": product.product_name,
            "product_type": product.category,
            "brand": None,
            "manufacturer": None,
            "manufacturer_part_number": product.external_product_id,
        }

        total_confidence = 0.0
        confidence_count = 0

        features_data = []

        for a in product.attributes:
            attr_by_name[a.attribute_name] = a
            evidences_data = []
            for e in a.evidences:
                prov = "DIRECT"
                if e.evidence_metadata and isinstance(e.evidence_metadata, dict):
                    prov = e.evidence_metadata.get("provenance", "DIRECT")
                ev_item = {
                    "id": str(e.id),
                    "attribute_id": str(a.id),
                    "attribute_name": a.attribute_name,
                    "source_name": e.source_name,
                    "source_type": e.source_type,
                    "source_location": e.source_location,
                    "source_text": e.source_text,
                    "provenance": prov,
                    "metadata": e.evidence_metadata,
                }
                evidences_data.append(ev_item)
                all_evidences_data.append(ev_item)

            # Separate features from canonical structured attributes
            if a.attribute_name.startswith("feature_"):
                features_data.append({
                    "id": str(a.id),
                    "name": a.attribute_name.replace("feature_", "").replace("_", " ").title(),
                    "value": a.attribute_value,
                    "confidence_score": a.confidence_score,
                    "status": a.status,
                    "extraction_method": a.extraction_method,
                    "evidences": evidences_data,
                })
                continue

            if a.confidence_score is not None:
                total_confidence += a.confidence_score
                confidence_count += 1

            # Populate identity fields if present
            if a.attribute_name == "brand":
                identity_dict["brand"] = a.attribute_value
            elif a.attribute_name == "manufacturer":
                identity_dict["manufacturer"] = a.attribute_value
            elif a.attribute_name in ("manufacturer_part_number", "part_number") and not identity_dict["manufacturer_part_number"]:
                identity_dict["manufacturer_part_number"] = a.attribute_value
            elif a.attribute_name == "product_type" and not identity_dict["product_type"]:
                identity_dict["product_type"] = a.attribute_value

            # Include authoritative structured attributes
            attributes_data.append({
                "id": str(a.id),
                "name": a.attribute_name,
                "value": a.attribute_value,
                "normalized_value": a.normalized_value,
                "unit": a.unit,
                "confidence_score": a.confidence_score,
                "status": a.status,
                "extraction_method": a.extraction_method,
                "evidences": evidences_data,
            })

        # Calculate average confidence from authoritative structured attributes
        overall_confidence = round(total_confidence / max(1, confidence_count), 2) if confidence_count > 0 else 0.95

        return {
            "product": {
                "id": str(product.id),
                "external_product_id": product.external_product_id,
                "product_name": product.product_name,
                "category": product.category,
                "raw_data": product.raw_data,
                "created_at": product.created_at,
                "updated_at": product.updated_at,
            },
            "identity": identity_dict,
            "attributes": attributes_data,
            "features": features_data,
            "evidence": all_evidences_data,
            "conflicts": [],
            "confidence": overall_confidence,
            "total_attributes": len(attributes_data),
        }
