import { apiClient } from './client';
import type {
  AIHealthResponse,
  AnalyzeJobResponse,
  ProductDetailResponse,
} from '../types/api';

export const getAIHealth = async (): Promise<AIHealthResponse> => {
  const res = await apiClient.get<AIHealthResponse>('/intelligence/health');
  return res.data;
};

export const analyzeJob = async (
  jobId: string,
  limit?: number,
  productId?: string
): Promise<AnalyzeJobResponse> => {
  const params: any = {};
  if (limit !== undefined) params.limit = limit;
  if (productId) params.product_id = productId;
  const res = await apiClient.post<AnalyzeJobResponse>(`/intelligence/analyze/${jobId}`, null, {
    params,
  });
  return res.data;
};

export const analyzeSingleProduct = async (
  productId: string
): Promise<ProductDetailResponse> => {
  const res = await apiClient.post<ProductDetailResponse>(
    `/intelligence/analyze/product/${productId}`
  );
  return res.data;
};

export const getProductIntelligence = async (
  productId: string
): Promise<ProductDetailResponse> => {
  const res = await apiClient.get<ProductDetailResponse>(
    `/intelligence/product/${productId}`
  );
  return res.data;
};
