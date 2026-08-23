import { apiClient } from './client';

export interface QueryFilter {
  field: string;
  operator: string;
  value: string;
}

export interface QueryPlan {
  filters: QueryFilter[];
  requested_fields: string[];
  explanation?: string;
}

export interface QueryPreviewResponse {
  job_id: string;
  query: string;
  query_plan: QueryPlan;
  available_fields: string[];
  unavailable_fields: string[];
  can_execute: boolean;
  message?: string;
}

export interface ProductEvidenceSummary {
  source_location: string;
  source_text: string;
  provenance: string;
}

export interface QueryResultItem {
  product_id: string;
  part_number?: string;
  product_name?: string;
  brand?: string;
  manufacturer?: string;
  product_type?: string;
  fields: Record<string, any>;
  evidence: Record<string, ProductEvidenceSummary>;
}

export interface QueryResponse {
  job_id: string;
  query: string;
  interpreted_request: QueryPlan;
  total_results: number;
  results: QueryResultItem[];
  available_fields: string[];
  unavailable_fields: string[];
  status: string;
  message?: string;
}

/**
 * Previews the interpreted QueryPlan without executing.
 */
export const previewProductQuery = async (
  jobId: string,
  query: string
): Promise<QueryPreviewResponse> => {
  const response = await apiClient.post<QueryPreviewResponse>(
    `/query/${jobId}/preview`,
    { query }
  );
  return response.data;
};

/**
 * Executes the natural language query against PostgreSQL product data.
 */
export const executeProductQuery = async (
  jobId: string,
  query: string,
  limit: number = 100
): Promise<QueryResponse> => {
  const response = await apiClient.post<QueryResponse>(
    `/query/${jobId}`,
    { query, limit }
  );
  return response.data;
};
