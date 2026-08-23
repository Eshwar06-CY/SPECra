export interface ProcessingJob {
  id: string;
  filename: string;
  file_type: string;
  status: string;
  total_records: number;
  processed_records: number;
  failed_records: number;
  started_at?: string;
  completed_at?: string;
  created_at: string;
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

export interface ProductDetail {
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

export interface ValidationReport {
  product_id: string;
  status: 'passed' | 'warning' | 'failed';
  score: number;
  errors: number;
  warnings: number;
  info: number;
  results: ValidationIssue[];
}

export interface EnrichedField {
  field: string;
  value: string;
  normalized_value?: string;
  unit?: string;
  method: string;
  provenance: string;
  confidence: number;
  source: string;
  source_type: string;
  source_location?: string;
  source_text: string;
}

export interface EnrichmentReport {
  product_id: string;
  status: string;
  enriched_fields: number;
  skipped_fields: number;
  conflicts: any[];
  enrichments: EnrichedField[];
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

export interface ExportPreview {
  job_id: string;
  filename: string;
  total_products: number;
  total_headers: number;
  headers: string[];
  summary: ExportSummary;
  sample_rows: Record<string, string>[];
}
