export interface ColumnSchemaInfo {
  column_name: string;
  inferred_type: string;
  pandas_dtype: string;
  total_count: number;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  uniqueness_ratio: number;
  sample_values: any[];
  is_numeric: boolean;
  is_text: boolean;
  is_likely_identifier: boolean;
  is_likely_product_name: boolean;
  is_likely_category: boolean;
}

export interface SchemaAnalysisSummary {
  filename: string;
  file_type: string;
  row_count: number;
  column_count: number;
  columns: string[];
  column_details: Record<string, ColumnSchemaInfo>;
  numeric_columns: string[];
  text_columns: string[];
  likely_identifier_columns: string[];
  likely_product_name_columns: string[];
  likely_category_columns: string[];
}

export interface IngestionUploadResponse {
  job_id: string;
  filename: string;
  file_type: string;
  row_count: number;
  column_count: number;
  schema_summary: SchemaAnalysisSummary;
  status: string;
  processed_records: number;
  failed_records: number;
  message: string;
}

export interface ProcessingJobResponse {
  id: string;
  filename: string;
  file_type: string;
  status: string;
  total_records: number;
  processed_records: number;
  failed_records: number;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  created_at: string;
}

export interface ProductRecordResponse {
  id: string;
  job_id?: string;
  external_product_id?: string;
  product_name?: string;
  category?: string;
  raw_data: Record<string, any>;
  created_at: string;
}

export interface PaginatedProductRecordsResponse {
  job_id: string;
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  records: ProductRecordResponse[];
}

export interface ProductIdentity {
  product_name?: string;
  product_type?: string;
  brand?: string;
  manufacturer?: string;
  manufacturer_part_number?: string;
}

export interface EvidenceItem {
  id: string;
  attribute_id?: string;
  attribute_name?: string;
  source_name: string;
  source_type: string;
  source_location?: string;
  source_text?: string;
  provenance: string;
  metadata?: {
    notes?: string;
    original_value?: string;
    [key: string]: any;
  };
}

export interface AttributeItem {
  id: string;
  name: string;
  value: string;
  normalized_value?: string;
  unit?: string;
  confidence_score: number;
  status: string;
  extraction_method: string;
  evidences?: EvidenceItem[];
}

export interface FeatureItem {
  id: string;
  name: string;
  value: string;
  confidence_score: number;
  status: string;
  extraction_method: string;
  evidences?: EvidenceItem[];
}

export interface ProductDetailResponse {
  product: {
    id: string;
    external_product_id?: string;
    product_name?: string;
    category?: string;
    raw_data?: Record<string, any>;
    created_at: string;
    updated_at: string;
  };
  identity: ProductIdentity;
  attributes: AttributeItem[];
  features: FeatureItem[];
  evidence: EvidenceItem[];
  conflicts: any[];
  confidence: number;
  total_attributes: number;
}

export interface AnalyzeJobResponse {
  job_id: string;
  provider?: string;
  model?: string;
  total?: number;
  total_requested?: number;
  processed: number;
  failed: number;
  status: 'completed' | 'partial' | 'failed';
  message?: string;
  errors?: {
    product_id?: string;
    error_type?: string;
    raw_type?: string;
    message: string;
  }[];
  results?: {
    product_id: string;
    status: string;
    product_name?: string;
    confidence_score?: number;
    error?: string;
  }[];
}

export interface ValidationIssue {
  validation_type: string;
  severity: 'ERROR' | 'WARNING' | 'INFO';
  field: string;
  current_value?: string;
  expected_condition?: string;
  message: string;
  validation_method: string;
  confidence: number;
  attribute_id?: string;
}

export interface ValidationReportResponse {
  product_id: string;
  status: 'passed' | 'warning' | 'failed';
  score: number;
  errors: number;
  warnings: number;
  info: number;
  results: ValidationIssue[];
}

export interface EnrichedFieldItem {
  field: string;
  value: string;
  normalized_value?: string;
  unit?: string;
  method: string;
  provenance: 'DIRECT' | 'DERIVED' | 'INFERRED' | 'UNVERIFIED';
  confidence: number;
  source: string;
  source_type: string;
  source_location?: string;
  source_text: string;
}

export interface EnrichmentConflict {
  field: string;
  candidate_values: string[];
  reason: string;
}

export interface EnrichmentReportResponse {
  product_id: string;
  status: string;
  enriched_fields: number;
  skipped_fields: number;
  conflicts: EnrichmentConflict[];
  enrichments: EnrichedFieldItem[];
}

export interface ExportSummary {
  job_id: string;
  filename: string;
  total_products: number;
  total_headers: number;
  successfully_mapped_products: number;
  products_with_validation_errors: number;
  products_with_validation_warnings: number;
  fill_rate_percent: number;
  fields_populated_count: number;
  fields_blank_count: number;
  populated_field_counts: Record<string, number>;
}

export interface ExportPreviewResponse {
  job_id: string;
  filename: string;
  total_products: number;
  total_headers: number;
  headers: string[];
  summary: ExportSummary;
  sample_rows: Record<string, string>[];
}

export interface AIHealthResponse {
  status: string;
  model: string;
  provider: string;
  api_key_configured: boolean;
  latency_ms?: number;
}
