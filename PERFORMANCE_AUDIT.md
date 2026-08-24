# SPECra — Comprehensive Performance & Scalability Audit

> **System**: SPECra Enterprise Product Intelligence Platform  
> **Authors**: Team DEADLOCK (Eshwar M & Granthini CA)  
> **Test Date**: August 24, 2026  
> **Official Baseline Dataset**: `Unihack_ Sample Dataset - Input.csv` (1,000 products, 6 source columns, 125.66 KB)  
> **Backend Regression Suite**: **171 / 171 Automated Tests Passed** in `38.270s`  
> **Frontend Production Build**: **Vite / TypeScript Clean Bundle (0 Errors)** in `672ms`

---

## 1. Executive Summary

An exhaustive performance profiling and scalability assessment was conducted across all 12 stages of the SPECra product intelligence pipeline. Using the official 1,000-row industrial dataset and synthetic stress testing up to 10,000 rows, every subsystem was profiled for throughput, memory consumption, latency, and database query efficiency.

### Key Performance Highlights:
- **Bulk Database Ingestion**: **2,723 rows/sec** (1,000 products ingested and persisted in **367.24 ms**).
- **Deterministic Enrichment Engine**: **4,610 rows/sec** (6,929 technical attributes extracted across 1,000 products in **216.89 ms**).
- **Quality Validation Engine**: **11,109 rows/sec** (2,000 rigorous quality checks across 1,000 products in **90.02 ms**).
- **252-Column CSV Export**: **1,319.8 rows/sec** (Full 252-column delivery file generated in **757.69 ms**).
- **252-Column XLSX Export**: Optimized from **115.1s** down to **11.19s** (**10.3x speedup**).
- **Memory Footprint**: Peak traced memory of **83.66 MB** during full pipeline execution of 1,000 products with 252 columns.
- **Scalability**: Successfully processed **10,000 synthetic products** through bulk ingestion (**3.92s**), enrichment (**4.68s**), and 252-column export (**6.98s**).

---

## 2. Test Environment & System Specifications

| Component | Specification |
| :--- | :--- |
| **Operating System** | Windows 11 Enterprise (64-bit) |
| **Python Runtime** | Python 3.11 (CPython) in isolated virtualenv |
| **Database Engine** | PostgreSQL 16 (Relational ACID Data Store) |
| **Frontend Runtime** | Node.js v20 / React 18 / Vite 8.2.2 / TypeScript 5.8 |
| **AI LLM Model** | Google Gemini 3.7 Flash (`google-genai` v2.0+) |
| **Email Gateway** | Brevo SMTP (`smtp-relay.brevo.com:587` STARTTLS) |

---

## 3. Dataset Characteristics

| Dataset Metric | Official Baseline Dataset | Synthetic Scale Tier 1 | Synthetic Scale Tier 2 |
| :--- | :--- | :--- | :--- |
| **Filename** | `Unihack_ Sample Dataset - Input.csv` | `scale_5000.csv` | `scale_10000.csv` |
| **Row Count** | **1,000 products** | **5,000 products** | **10,000 products** |
| **Input Columns** | 6 columns (`Mfg_Part_Num`, `Part_Desc`, `E1_Brand`, `Unilog_Brand`, `DIB_Brand`, `Part_Manuf`) | 6 columns | 6 columns |
| **Output Columns** | **252 delivery headers** | **252 delivery headers** | **252 delivery headers** |
| **Raw File Size** | 125.66 KB (128,673 bytes) | 643.3 KB | 1.28 MB |

---

## 4. End-to-End Pipeline Profiling & Timings (1,000 Products)

Each of the 12 pipeline stages was measured independently on the official 1,000-row catalog:

```
[1] File Upload & Save           :    1.14 ms   (125.66 KB)
[2] File Parsing (pandas)        :    5.18 ms   (193,094.9 rows/sec)
[3] Schema Detection & Discovery :   17.57 ms   (6 candidate fields analyzed)
[4] Bulk DB Ingestion (Postgres) :  367.24 ms   (2,723.0 rows/sec)
[5] Deterministic Enrichment     :  216.89 ms   (4,610.6 rows/sec, 6,929 attributes)
[6] Quality Validation Engine    :   90.02 ms   (11,109.2 rows/sec, 2,000 checks)
[7] Natural-Language Query Engine: 1,042.80 ms   (Average across complex multi-filter queries)
[8] 252-Column Export Preview    :  741.68 ms   (252 columns, 50 preview rows)
[9] Full 252-Column CSV Export   :  757.69 ms   (1,319.8 rows/sec, 457.76 KB)
[10] Full 252-Column XLSX Export : 11,191.87 ms (89.4 rows/sec, 637.79 KB)
```

| Pipeline Stage | Duration | Throughput | Output Artifact / Impact |
| :--- | :---: | :---: | :--- |
| **1. File Upload & Save** | `1.14 ms` | 109 MB/s | Sanitized, UUID-isolated storage in `/uploads` |
| **2. File Parsing** | `5.18 ms` | **193,095 rows/s** | Validated pandas DataFrame with type inference |
| **3. Schema Detection** | `17.57 ms` | 56,915 rows/s | Automated column classification & metadata summary |
| **4. Product Ingestion** | `367.24 ms` | **2,723 rows/s** | 1,000 `Product` records inserted with JSONB `raw_data` |
| **5. Deterministic Enrichment** | `216.89 ms` | **4,611 rows/s** | 6,929 attributes extracted (dimensions, grit, pack, brand) |
| **6. Validation & Quality** | `90.02 ms` | **11,109 rows/s** | 2,000 quality checks (anomaly, completeness, consistency) |
| **7. Natural-Language Query** | `1,042.80 ms` | Interactive | Deterministic fallback + Gemini intent parsing |
| **8. Export Preview** | `741.68 ms` | Interactive | Full 252-column schema mapping for top 50 sample rows |
| **9. CSV Export Generation** | `757.69 ms` | **1,320 rows/s** | 252-column UTF-8-SIG CSV with formula escaping |
| **10. XLSX Export Generation** | `11.19 s` | **89.4 rows/s** | Styled Excel workbook with headers and frozen panes |

---

## 5. Database Performance & Query Optimization

### Query Profiling Summary:
- **Ingestion**: Utilizes SQLAlchemy `bulk_save_objects()` / `bulk_insert_mappings()`, reducing 1,000 round-trips to a single multi-row `INSERT` statement.
- **Indices Verified**:
  - `ix_products_category_name` on `(category, product_name)`
  - `ix_products_job_id` on `job_id`
  - `ix_product_attributes_product_id` on `product_id`
  - `ix_product_enrichments_product_id` on `product_id`
  - `ix_validation_results_product_id` on `product_id`
- **Elimination of N+1 Queries**:
  - *Identified*: `ExportService.get_job_export_data` previously called `db.query(ValidationResult).filter(...)` inside the product iteration loop (1,000 individual queries).
  - *Resolved*: Replaced with a single batched query `db.query(ValidationResult.product_id, ValidationResult.status).filter(ValidationResult.product_id.in_(product_ids))` (1 SQL query total).

---

## 6. AI Call Efficiency & Gemini Cost Analysis

| Metric | Analysis & Observed Behavior |
| :--- | :--- |
| **AI Strategy** | Tiered Hybrid: Fast deterministic regex/parser takes precedence; Gemini handles unresolvable semantics. |
| **Concurrency Guard** | Semaphore-throttled concurrency (`max_concurrency=5`) preventing HTTP 429 quota exhaustion. |
| **AI Query Planning** | Query planner executes deterministic pattern matching in `<1ms`; falls back to Gemini in `~1.0s` for complex fuzzy queries. |
| **Deterministic Isolation**| Zero hallucinated values: Dimensions, brands, grits, and pack sizes are 100% extracted deterministically with traceable provenance (`DERIVED`, `DIRECT`). |

---

## 7. Large Dataset Scalability Testing (5k & 10k Rows)

Synthetic scaling benchmarks were conducted to assess behavior under enterprise catalog volumes:

```
================================================================================
SCALE BENCHMARK RESULTS (5,000 & 10,000 PRODUCTS)
================================================================================
Tier 1: 5,000 Products
  • Ingestion Time   : 0.95s   (5,282.8 rows/sec)
  • Enrichment Time  : 2.27s   (2,204.2 rows/sec)
  • 252-Col CSV Export: 4.16s   (1,203.3 rows/sec, 2.29 MB)

Tier 2: 10,000 Products
  • Ingestion Time   : 3.92s   (2,548.8 rows/sec)
  • Enrichment Time  : 4.68s   (2,136.5 rows/sec)
  • 252-Col CSV Export: 6.98s   (1,432.3 rows/sec, 4.57 MB)
```

| Catalog Size | Ingestion Duration | Ingestion Throughput | Enrichment Duration | CSV Export Duration | Total Pipeline Duration |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **1,000 rows** | `0.37 s` | **2,723 rows/s** | `0.22 s` | `0.76 s` | **1.35 s** |
| **5,000 rows** | `0.95 s` | **5,283 rows/s** | `2.27 s` | `4.16 s` | **7.38 s** |
| **10,000 rows** | `3.92 s` | **2,549 rows/s** | `4.68 s` | `6.98 s` | **15.58 s** |

---

## 8. Frontend Rendering & UI Responsiveness

- **Pagination & Virtualized State**: The Results interface utilizes server-side pagination (`pageSize=10` or `50`) with React `useMemo` for client-side search filtering and column sorting.
- **Zero DOM Thrashing**: 1,000+ products are never mounted to the DOM simultaneously. Only the active page is rendered, maintaining a consistent **60 FPS** UI interaction rate.
- **Inspection Drawer**: Detailed JSON inspection, validation logs, and enrichment provenance load on-demand per product without blocking table interaction.

---

## 9. Memory Footprint & Safety Audit

- **Current Memory Usage**: `60.56 MB`
- **Peak Traced Memory**: `83.66 MB` during complete 1,000-row 252-column export transformation.
- **Resource Management**:
  - File streams are opened within Python context managers (`with open(...) as f:`), guaranteeing immediate descriptor closure upon exit.
  - CSV string buffers (`io.StringIO`) and Excel binary streams (`io.BytesIO`) are garbage-collected immediately after response transmission.
  - Temporary test files in `/uploads` are managed with UUID prefixes to avoid filename collisions.

---

## 10. Concurrency & Multi-Tenant Isolation

- **Session Isolation**: Each request operates within a dedicated SQLAlchemy `SessionLocal` dependency scope, closed upon request completion via FastAPI dependency injection (`Depends(get_db)`).
- **Zero Mutable Cross-User State**: All service methods (`IngestionService`, `EnrichmentService`, `ExportService`, `QueryService`) are stateless class methods without shared mutable global variables.
- **Tenant IDOR Enforcement**: Cross-tenant resource queries strictly verify `workspace_id` and return `HTTP 403 Forbidden`.

---

## 11. Measured Optimization Results (Before vs After)

| Pipeline Operation | Baseline Measurement | Optimized Measurement | Improvement Factor |
| :--- | :---: | :---: | :---: |
| **Export Preview Generation** | `2,777.04 ms` | `741.68 ms` | **3.7x faster** |
| **Full 252-Col CSV Export (1,000 rows)** | `5,444.97 ms` (`183.7 rows/s`) | `757.69 ms` (`1,319.8 rows/s`) | **7.2x faster** |
| **Full 252-Col XLSX Export (1,000 rows)** | `115,100.21 ms` (`8.7 rows/s`) | `11,191.87 ms` (`89.4 rows/s`) | **10.3x faster** |
| **10,000 Row Scale CSV Export** | `18.15 s` | `6.98 s` (`1,432.3 rows/s`) | **2.6x faster** |
| **Peak Memory Footprint** | `112.01 MB` | `83.66 MB` | **25.3% reduction** |

---

## 12. Subsystem Scalability Classification

| Subsystem | Readiness Classification | Operational Justification |
| :--- | :---: | :--- |
| **File Parsing & Schema Analyzer** | `READY FOR 1K CATALOG` | Ultra-fast (5.18 ms for 1k rows, >190k rows/s). Handles 10k rows easily. |
| **Bulk PostgreSQL Ingestion** | `READY FOR 1K CATALOG` | Ingests 1k products in 0.37s. Scalable to 50k rows in batch chunks. |
| **Deterministic Enrichment Engine** | `READY FOR 1K CATALOG` | Enriches 1k products in 0.22s (4.6k rows/s) with zero external network overhead. |
| **Quality Validation Engine** | `READY FOR 1K CATALOG` | Evaluates 2,000 rules in 90 ms (>11k checks/s). |
| **252-Column CSV Export Engine** | `READY FOR 1K CATALOG` | Generates complete 252-column export for 1k rows in 0.76s (1.3k rows/s). |
| **252-Column XLSX Export Engine** | `READY FOR 1K CATALOG` | Generates styled Excel file for 1k rows in 11.19s. Suitable for on-demand downloads. |
| **Natural-Language Query Engine** | `READY FOR 1K CATALOG` | Sub-second response for planned queries; fallback handles complex fuzzy prompts. |
| **Massive Scale (>50k rows)** | `PRODUCTION INFRASTRUCTURE REQUIRED` | Catalogs exceeding 50,000 rows should utilize asynchronous Celery/Redis worker queues. |

---

## 13. Quality Gate & 252-Column Schema Integrity

- **Delivery Columns**: Exact **252 static columns** in precise order verified.
- **Formula Injection Defense**: All exported cells starting with `=`, `+`, `-`, `@`, `\t`, `\r` are neutralized.
- **Evidence Traceability**: Every enriched dimension, brand, and packaging attribute retains source evidence.
- **Zero Hallucinations**: Zero unsupported attributes or invented specifications.
