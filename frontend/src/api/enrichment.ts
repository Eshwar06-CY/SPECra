import { apiClient } from './client';
import type { EnrichmentReportResponse } from '../types/api';

export const enrichProduct = async (
  productId: string
): Promise<EnrichmentReportResponse> => {
  const res = await apiClient.post<EnrichmentReportResponse>(
    `/enrichment/product/${productId}`
  );
  return res.data;
};

export const getProductEnrichment = async (
  productId: string
): Promise<EnrichmentReportResponse> => {
  const res = await apiClient.get<EnrichmentReportResponse>(
    `/enrichment/product/${productId}`
  );
  return res.data;
};
